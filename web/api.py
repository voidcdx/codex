"""
web/api.py — FastAPI backend for the Warframe Damage Calculator.

Endpoints:
  GET  /api/weapons          → list of weapon names + basic stats
  GET  /api/mods             → list of mod names + types
  GET  /api/enemies          → list of enemy names + factions
  POST /api/modded-weapon    → modded weapon stats
  POST /api/calculate        → full damage calculation
  GET  /api/worldstate       → parsed live worldstate (fissures, alerts, etc.)
  GET  /live                 → live data SPA
"""
from __future__ import annotations

import sys
import time
import json
from pathlib import Path

# Ensure project root on path when run from web/ directory
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import math
from pydantic import Field
from src.arcanes import ARCANE_PRESETS, ARCANE_DISPLAY_NAMES, ARCANE_RESTRICTIONS, ARCANE_MAX_STACKS, make_arcane
from src.buffs import BUFF_PRESETS, BUFF_DISPLAY_NAMES, make_buff
from src.calculator import DamageCalculator, calculate_crit_multiplier, status_chance_per_pellet
from src.combiner import combine_elements, PRIMARY_ELEMENTS
from src.loader import (
    _raw_enemies, _raw_mods, _raw_weapons,
    list_enemies, list_mods, list_weapons,
    load_enemy, load_mod, load_weapon, make_riven_mod,
)
from src.models import Buff, DamageComponent
from src.quantizer import quantize
from src.scaling import scale_enemy_stats
from src.version import APP_VERSION, GAME_DATA_VERSION

app = FastAPI(title="Warframe Damage Calculator", version=APP_VERSION)

# Serve static files (HTML/CSS/JS/images)
_static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static)), name="static")


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

@app.get("/api/version")
def get_version() -> dict:
    return {"app": APP_VERSION, "game_data": GAME_DATA_VERSION}


# ---------------------------------------------------------------------------
# List endpoints
# ---------------------------------------------------------------------------

@app.get("/api/weapons")
def get_weapons() -> list[dict]:
    raw = _raw_weapons()
    out = []
    for name, entry in raw.items():
        attacks = entry.get("attacks") or []
        # Show first attack's damage as the default base_damage
        first_atk = attacks[0] if attacks else {}
        first_damage: dict[str, float] = {
            **first_atk.get("base_damage", {}),
            **first_atk.get("innate_elements", {}),
        }
        out.append({
            "name":             name,
            "slot":             entry.get("slot", ""),
            "class":            entry.get("class", ""),
            "trigger":          entry.get("trigger", ""),
            "crit_chance":      entry.get("crit_chance", 0),
            "crit_multiplier":  entry.get("crit_multiplier", 1),
            "status_chance":    entry.get("status_chance", 0),
            "fire_rate":        entry.get("fire_rate", None),
            "magazine":         entry.get("magazine", None),
            "max_ammo":         entry.get("max_ammo", None),
            "reload":           entry.get("reload", None),
            "mastery_req":      entry.get("mastery_req", 0),
            "riven_disposition": entry.get("riven_disposition", None),
            "base_damage":      first_damage,
            "image":            name.replace(' ', '-').replace('&', 'and') + '.png',
            "attacks": [
                {
                    "name": a.get("name", ""),
                    "shot_type": a.get("shot_type", ""),
                    "base_damage": {**a.get("base_damage", {}), **a.get("innate_elements", {})},
                    "crit_chance": a.get("crit_chance", 0),
                    "crit_multiplier": a.get("crit_multiplier", 1),
                    "status_chance": a.get("status_chance", 0),
                    "fire_rate": a.get("fire_rate", 0),
                    "multishot": a.get("multishot", 1),
                }
                for a in attacks
            ],
        })
    return sorted(out, key=lambda x: x["name"])


_PRIMARY_ELEM_FIELDS = {
    "heat": "heat_pct",
    "cold": "cold_pct",
    "electricity": "electricity_pct",
    "toxin": "toxin_pct",
}

# pct fields consumed by the Alchemy Guide (sort, filter, display)
_PCT_FIELDS = [
    "heat_pct", "cold_pct", "electricity_pct", "toxin_pct",
    "blast_pct", "corrosive_pct", "gas_pct",
    "magnetic_pct", "radiation_pct", "viral_pct",
    "status_chance_pct", "damage_bonus_pct", "fire_rate_pct",
    "crit_damage_pct", "multishot_pct", "reload_speed_pct",
]


@app.get("/api/mods")
def get_mods() -> list[dict]:
    raw = _raw_mods()
    out = []
    for name, entry in raw.items():
        if name.startswith("Flawed "):
            continue
        primary_element = None
        for elem, field in _PRIMARY_ELEM_FIELDS.items():
            if entry.get(field):
                primary_element = elem
                break
        out.append({
            "name":            name,
            "type":            entry.get("type", ""),
            "polarity":        entry.get("polarity", ""),
            "rarity":          entry.get("rarity", "Common"),
            "base_drain":      int(entry.get("base_drain") or 0),
            "max_rank":        int(entry.get("max_rank") or 5),
            "effect":          entry.get("effect_raw", ""),
            "primary_element": primary_element,
            **{f: float(entry.get(f) or 0) for f in _PCT_FIELDS},
        })
    return sorted(out, key=lambda x: x["name"])


@app.get("/api/enemies")
def get_enemies() -> list[dict]:
    raw = _raw_enemies()
    out = []
    for name, entry in raw.items():
        out.append({
            "name":           name,
            "faction":        entry.get("faction", ""),
            "health_type":    entry.get("health_type", ""),
            "armor_type":     entry.get("armor_type", ""),
            "base_armor":     entry.get("base_armor", 0),
            "base_health":    entry.get("base_health", 0),
            "base_shield":    entry.get("base_shield", 0),
            "base_level":     entry.get("base_level", 1),
            "body_parts":      entry.get("body_parts", {"Body": 1.0, "Head": 1.0}),
        })
    return sorted(out, key=lambda x: x["name"])


# ---------------------------------------------------------------------------
# Calculate endpoint
# ---------------------------------------------------------------------------

class BuffSpec(BaseModel):
    name: str            # preset key, e.g. "roar", "eclipse"
    strength: float = 1.0  # ability strength multiplier (1.0 = 100%)
    subsumed: bool = False  # True for Helminth (subsumed) reduced base values


@app.get("/api/buffs")
def get_buffs() -> list[dict]:
    """Return available buff presets for the UI."""
    return [
        {"key": k, "display_name": BUFF_DISPLAY_NAMES.get(k, k)}
        for k in BUFF_PRESETS
    ]


class ArcaneSpec(BaseModel):
    name: str          # preset key, e.g. "primary_merciless"
    stacks: int = 0    # current active stacks


@app.get("/api/arcanes")
def get_arcanes() -> list[dict]:
    """Return available weapon arcane presets for the UI."""
    return [
        {
            "key": k,
            "display_name": ARCANE_DISPLAY_NAMES.get(k, k),
            "max_stacks": ARCANE_MAX_STACKS.get(k, 1),
            "restriction": ARCANE_RESTRICTIONS.get(k, ""),
        }
        for k in ARCANE_PRESETS
    ]


class RivenStat(BaseModel):
    stat: str    # e.g. "damage", "crit_chance", "heat"
    value: float # decimal fraction (0.658 = +65.8%)


class RivenSpec(BaseModel):
    stats: list[RivenStat]


_BONUS_ELEM_MAP: dict[str, str] = {
    "heat": "HEAT", "cold": "COLD", "electricity": "ELECTRICITY", "toxin": "TOXIN",
}


class ModdedWeaponRequest(BaseModel):
    weapon: str
    mods: list[str] = []
    attack: str | None = None
    galvanized_stacks: int = Field(default=0, ge=0, le=5)
    riven: RivenSpec | None = None
    bonus_element: str | None = None      # "heat" | "cold" | "electricity" | "toxin"
    bonus_element_pct: float = 0.0        # 0.25–0.60
    arcanes: list[ArcaneSpec] = []        # weapon arcanes (max 2)


@app.post("/api/modded-weapon")
def modded_weapon(req: ModdedWeaponRequest) -> dict:
    try:
        weapon = load_weapon(req.weapon, attack_name=req.attack)
    except KeyError as e:
        raise HTTPException(400, str(e))
    if req.bonus_element and req.bonus_element_pct > 0.0:
        from src.enums import DamageType as _DT
        _bet_name = _BONUS_ELEM_MAP.get(req.bonus_element.lower())
        if _bet_name:
            weapon.bonus_element_type = _DT[_bet_name]
            weapon.bonus_element_pct = req.bonus_element_pct

    mods = []
    for mod_name in req.mods:
        try:
            mods.append(load_mod(mod_name))
        except KeyError:
            raise HTTPException(400, f"Unknown mod: {mod_name!r}")
    if req.riven:
        mods.append(make_riven_mod([s.model_dump() for s in req.riven.stats]))

    base_damage = weapon.total_base_damage
    base_cc = weapon.crit_chance
    base_cm = weapon.crit_multiplier
    base_sc = weapon.status_chance

    galv_stacks = req.galvanized_stacks
    galv_cc_bonus = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                        for m in mods if m.galv_kill_stat == "cc_bonus")
    galv_cd_bonus = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                        for m in mods if m.galv_kill_stat == "cd_bonus")
    galv_ms_bonus = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                        for m in mods if m.galv_kill_stat == "multishot_bonus")
    galv_sc_bonus = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                        for m in mods if m.galv_kill_stat == "sc_bonus")

    # --- Build Arcane objects ---
    arcane_objects = []
    for aspec in req.arcanes:
        try:
            arcane_objects.append(make_arcane(aspec.name, aspec.stacks))
        except KeyError as e:
            raise HTTPException(400, str(e))
    arcane_damage_bonus = sum(a.damage_bonus for a in arcane_objects)
    arcane_cc_bonus = sum(a.cc_bonus for a in arcane_objects)
    arcane_cd_bonus = sum(a.cd_bonus for a in arcane_objects)
    arcane_reload_bonus = sum(a.reload_bonus for a in arcane_objects)

    total_damage_bonus = sum(m.damage_bonus for m in mods) + arcane_damage_bonus
    total_cc_bonus = sum(m.cc_bonus for m in mods) + galv_cc_bonus + arcane_cc_bonus
    total_cd_bonus = sum(m.cd_bonus for m in mods) + galv_cd_bonus + arcane_cd_bonus
    total_sc_bonus = sum(m.sc_bonus for m in mods) + galv_sc_bonus
    total_ms_bonus = sum(m.multishot_bonus for m in mods) + galv_ms_bonus
    total_fr_bonus = sum(m.fire_rate_bonus for m in mods)
    total_mag_bonus = sum(m.magazine_bonus for m in mods)
    total_ammo_max_bonus = sum(m.ammo_max_bonus for m in mods)
    total_reload_bonus = sum(m.reload_bonus for m in mods) + arcane_reload_bonus

    # Build elemental components from mods + innate, then combine
    mod_elements: list[DamageComponent] = []
    for m in mods:
        mod_elements.extend(m.elemental_bonuses)

    scaled_mod_elements = [
        DamageComponent(c.type, c.amount * base_damage)
        for c in mod_elements
        if c.type in PRIMARY_ELEMENTS
    ]
    mod_secondary = [
        DamageComponent(c.type, quantize(c.amount * base_damage, base_damage))
        for c in mod_elements
        if c.type not in PRIMARY_ELEMENTS
    ]
    # Innate element amounts are flat damage values, not percentages of base_damage
    scaled_innate_primary = [
        DamageComponent(c.type, c.amount)
        for c in weapon.innate_elements
        if c.type in PRIMARY_ELEMENTS
    ]
    innate_secondary = [
        DamageComponent(c.type, quantize(c.amount, base_damage))
        for c in weapon.innate_elements
        if c.type not in PRIMARY_ELEMENTS
    ]
    combined_elements = combine_elements(
        scaled_mod_elements,
        scaled_innate_primary,
        base_damage=base_damage,
        is_kuva_tenet=weapon.is_kuva_tenet,
    )
    elemental_components = (
        combined_elements
        + [c for c in innate_secondary if c.amount != 0.0]
        + [c for c in mod_secondary if c.amount != 0.0]
    )

    # Modded IPS + innate secondary (base_damage dict only has IPS; innate secondaries are pre-built)
    base_dmg_dict: dict[str, float] = {dt.name.lower(): v for dt, v in weapon.base_damage.items()}
    for c in weapon.innate_elements:
        key = c.type.name.lower()
        base_dmg_dict[key] = base_dmg_dict.get(key, 0.0) + c.amount
    modded_dmg_dict: dict[str, float] = {}
    for dt, v in weapon.base_damage.items():
        q = quantize(float(math.floor(v * (1.0 + total_damage_bonus))), base_damage)
        if q != 0.0:
            modded_dmg_dict[dt.name.lower()] = q

    # Modded elementals (apply damage bonus scaling already done in combine_elements)
    for c in elemental_components:
        q = quantize(float(math.floor(c.amount * (1.0 + total_damage_bonus))), base_damage)
        if q != 0.0:
            modded_dmg_dict[c.type.name.lower()] = q

    base_total = weapon.total_base_damage
    modded_total = sum(modded_dmg_dict.values())

    # Quantized base: each IPS/innate type at 0% damage bonus — actual in-game unmodded values
    quantized_base_dict: dict[str, float] = {}
    for dt, v in weapon.base_damage.items():
        q = quantize(float(math.floor(v)), base_damage)
        if q != 0.0:
            quantized_base_dict[dt.name.lower()] = q
    for c in weapon.innate_elements:
        key = c.type.name.lower()
        q = quantize(quantized_base_dict.get(key, 0.0) + c.amount, base_damage)
        if q != 0.0:
            quantized_base_dict[key] = q

    # Base fire rate from selected attack
    if weapon.attacks:
        att_name = req.attack or ""
        sel_atk = next(
            (a for a in weapon.attacks if a.name.lower() == att_name.lower()),
            weapon.attacks[0],
        )
        base_fr = sel_atk.fire_rate
    else:
        base_fr = 0.0

    # Base magazine and max ammo from raw weapon data
    raw_w = _raw_weapons().get(weapon.name, {})
    base_mag = float(raw_w.get("magazine") or 0.0)
    modded_mag = math.ceil(base_mag * (1.0 + total_mag_bonus)) if base_mag > 0 else 0
    base_ammo_max = float(raw_w.get("max_ammo") or 0.0)
    modded_ammo_max = math.ceil(base_ammo_max * (1.0 + total_ammo_max_bonus)) if base_ammo_max > 0 else 0
    base_reload = float(raw_w.get("reload") or 0.0)
    modded_reload = round(base_reload / (1.0 + total_reload_bonus), 4) if total_reload_bonus and base_reload else base_reload

    return {
        "base_damage":  base_dmg_dict,
        "base_total":   round(base_total, 4),
        "quantized_base_damage": quantized_base_dict,
        "modded_damage": modded_dmg_dict,
        "modded_total":  round(modded_total, 4),
        "base_cc":  base_cc,
        "modded_cc": round(base_cc + total_cc_bonus, 6),
        "base_cm":  base_cm,
        "modded_cm": round(base_cm * (1.0 + total_cd_bonus), 6),
        "base_sc":  base_sc,
        "modded_sc": round(base_sc * (1.0 + total_sc_bonus), 6),
        "sc_per_pellet": round(status_chance_per_pellet(base_sc * (1.0 + total_sc_bonus), weapon.multishot), 6),
        "inherent_multishot": weapon.multishot,
        "base_multishot":   1.0,
        "modded_multishot": round(1.0 + total_ms_bonus, 6),
        "base_fr":    round(base_fr, 4),
        "modded_fr":  round(base_fr * (1.0 + total_fr_bonus), 6),
        "base_magazine":   base_mag,
        "modded_magazine": modded_mag,
        "base_ammo_max":   base_ammo_max,
        "modded_ammo_max": modded_ammo_max,
        "base_reload":     base_reload,
        "modded_reload":   modded_reload,
    }


class CalcRequest(BaseModel):
    weapon:       str
    mods:         list[str] = []
    enemy:        str
    attack:       str | None = None
    crit_mode:    str = "average"   # "average" | "guaranteed" | "max"
    body_part:    str = "Body"
    headshot:     bool = False      # deprecated alias for body_part="Head"
    viral_stacks: int = 0           # 0–10
    corrosive_stacks: int = 0      # 0–10
    enemy_level:  int = Field(default=1, ge=1, le=9999)
    steel_path:   bool = False
    eximus:       bool = False
    combo_counter: int = 0         # melee combo hit count
    unique_statuses: int = 0       # unique active status types (Condition Overload)
    galvanized_stacks: int = Field(default=0, ge=0, le=5)   # 0–5 galvanized kill-stacks
    riven:        RivenSpec | None = None
    bonus_element: str | None = None    # "heat" | "cold" | "electricity" | "toxin"
    bonus_element_pct: float = 0.0      # 0.25–0.60
    buffs:        list[BuffSpec] = []    # Warframe ability buffs
    arcanes:      list[ArcaneSpec] = []  # Weapon arcanes (max 2)


@app.post("/api/calculate")
def calculate(req: CalcRequest) -> dict:
    try:
        weapon = load_weapon(req.weapon, attack_name=req.attack)
    except KeyError as e:
        raise HTTPException(400, str(e))
    if req.bonus_element and req.bonus_element_pct > 0.0:
        from src.enums import DamageType as _DT
        _bet_name = _BONUS_ELEM_MAP.get(req.bonus_element.lower())
        if _bet_name:
            weapon.bonus_element_type = _DT[_bet_name]
            weapon.bonus_element_pct = req.bonus_element_pct

    mods = []
    for mod_name in req.mods:
        try:
            mods.append(load_mod(mod_name))
        except KeyError:
            raise HTTPException(400, f"Unknown mod: {mod_name!r}")
    if req.riven:
        mods.append(make_riven_mod([s.model_dump() for s in req.riven.stats]))

    effective_part = "Head" if req.headshot else req.body_part
    try:
        enemy = load_enemy(req.enemy, body_part=effective_part)
    except KeyError:
        raise HTTPException(400, f"Unknown enemy: {req.enemy!r}")

    if req.crit_mode not in ("average", "guaranteed", "max"):
        raise HTTPException(400, f"crit_mode must be average/guaranteed/max")

    # --- Build Buff objects ---
    buff_objects: list[Buff] = []
    for bs in req.buffs:
        try:
            buff_objects.append(make_buff(bs.name, bs.strength, subsumed=bs.subsumed))
        except KeyError as e:
            raise HTTPException(400, str(e))

    # --- Build Arcane objects ---
    arcane_objects = []
    for aspec in req.arcanes:
        try:
            arcane_objects.append(make_arcane(aspec.name, aspec.stacks))
        except KeyError as e:
            raise HTTPException(400, str(e))
    arcane_cc = sum(a.cc_bonus for a in arcane_objects)
    arcane_cd = sum(a.cd_bonus for a in arcane_objects)
    arcane_reload = sum(a.reload_bonus for a in arcane_objects)

    galv_stacks = req.galvanized_stacks
    galv_cc = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                  for m in mods if m.galv_kill_stat == "cc_bonus")
    galv_cd = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                  for m in mods if m.galv_kill_stat == "cd_bonus")
    galv_ms = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                  for m in mods if m.galv_kill_stat == "multishot_bonus")
    galv_sc = sum(m.galv_kill_pct * min(galv_stacks, m.galv_max_stacks)
                  for m in mods if m.galv_kill_stat == "sc_bonus")

    base_cc = weapon.crit_chance + sum(m.cc_bonus for m in mods) + galv_cc + arcane_cc
    base_cm = weapon.crit_multiplier * (1.0 + sum(m.cd_bonus for m in mods) + galv_cd + arcane_cd)
    crit_mult = calculate_crit_multiplier(base_cc, base_cm, mode=req.crit_mode)

    raw_w = _raw_weapons().get(weapon.name, {})
    fire_rate   = float(raw_w.get("fire_rate")  or 1.0)
    magazine    = float(raw_w.get("magazine")   or 1.0)
    reload_time = float(raw_w.get("reload")     or 0.0)
    base_sc     = weapon.status_chance
    total_sc_bonus = sum(m.sc_bonus for m in mods) + galv_sc
    total_ms_bonus = sum(m.multishot_bonus for m in mods) + galv_ms
    total_fr_bonus = sum(m.fire_rate_bonus for m in mods)
    total_reload_bonus = sum(m.reload_bonus for m in mods) + arcane_reload
    modded_sc   = base_sc * (1.0 + total_sc_bonus)
    modded_ms   = 1.0 + total_ms_bonus

    calc = DamageCalculator()
    result = calc.calculate(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=(effective_part != "Body"),
        multishot=modded_ms,
        viral_stacks=req.viral_stacks,
        corrosive_stacks=req.corrosive_stacks,
        enemy_level=req.enemy_level,
        steel_path=req.steel_path,
        eximus=req.eximus,
        combo_counter=req.combo_counter,
        unique_statuses=req.unique_statuses,
        galvanized_stacks=galv_stacks,
        buffs=buff_objects,
        arcanes=arcane_objects,
    )
    procs = calc.calculate_procs(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=(effective_part != "Body"),
        unique_statuses=req.unique_statuses,
        galvanized_stacks=galv_stacks,
        buffs=buff_objects,
        arcanes=arcane_objects,
    )

    breakdown = {dtype.name: val for dtype, val in result.items()}
    total = sum(result.values())

    # Modded fire rate includes buff fire rate bonus
    modded_fr = fire_rate * (1.0 + total_fr_bonus)

    return {
        "weapon":        weapon.name,
        "mods":          req.mods,
        "enemy":         enemy.name,
        "crit_mode":     req.crit_mode,
        "crit_multiplier": crit_mult,
        "body_part":     effective_part,
        "viral_stacks":    req.viral_stacks,
        "corrosive_stacks": req.corrosive_stacks,
        "galvanized_stacks": galv_stacks,
        "buffs":         [{"name": b.name, "strength": bs.strength} for b, bs in zip(buff_objects, req.buffs)],
        "arcanes":       [{"name": a.name, "stacks": a.stacks} for a in arcane_objects],
        "breakdown":     breakdown,
        "total":         total,
        "procs":         procs,
        "fire_rate":     fire_rate,
        "modded_fr":     round(modded_fr, 6),
        "magazine":      magazine,
        "reload":        reload_time,
        "modded_reload": round(reload_time / (1.0 + total_reload_bonus), 4) if total_reload_bonus and reload_time else reload_time,
        "modded_sc":     round(modded_sc, 6),
        "sc_per_pellet": round(status_chance_per_pellet(modded_sc, weapon.multishot), 6),
        "inherent_multishot": weapon.multishot,
        "modded_ms":     round(modded_ms, 6),
    }



# ---------------------------------------------------------------------------
# Scaled enemy stats endpoint
# ---------------------------------------------------------------------------

class ScaleRequest(BaseModel):
    enemy:      str
    level:      int  = Field(default=1, ge=1, le=9999)
    steel_path: bool = False
    eximus:     bool = False


@app.post("/api/scaled-enemy")
def scaled_enemy(req: ScaleRequest) -> dict:
    try:
        e = load_enemy(req.enemy)
    except KeyError:
        raise HTTPException(400, f"Unknown enemy: {req.enemy!r}")
    return scale_enemy_stats(
        e.base_health, e.base_shield, e.base_armor,
        e.base_level, req.level, req.steel_path, req.eximus,
        faction=e.faction,
    )


# ---------------------------------------------------------------------------
# Worldstate — live game data
# ---------------------------------------------------------------------------

import requests as _requests  # noqa: E402

# In-memory cache: platform → (parsed_data, timestamp)
_ws_cache: dict[str, tuple[dict, float]] = {}
_WS_TTL = 300  # 5 minutes

_PLATFORM_URLS: dict[str, str] = {
    "pc":  "https://content.warframe.com/dynamic/worldState.php",
    "ps4": "https://ps4.warframe.com/dynamic/worldState.php",
    "xb1": "https://xb1.warframe.com/dynamic/worldState.php",
    "swi": "https://swi.warframe.com/dynamic/worldState.php",
}

_WS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, */*",
    "Referer": "https://www.warframe.com/",
}


def _fetch_worldstate(platform: str) -> dict:
    """Fetch and parse live worldstate for the given platform."""
    # Import here to avoid circular issues; scripts/ is not a package
    import importlib.util, os
    spec = importlib.util.spec_from_file_location(
        "parse_worldstate",
        Path(__file__).parent.parent / "scripts" / "parse_worldstate.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]

    url = _PLATFORM_URLS.get(platform, _PLATFORM_URLS["pc"])
    try:
        r = _requests.get(url, headers=_WS_HEADERS, timeout=15)
        r.raise_for_status()
        raw = r.json()
    except Exception:
        # Fall back to cached file if available
        raw_path = Path(__file__).parent.parent / "data" / "worldstate_raw.json"
        if raw_path.exists():
            raw = json.loads(raw_path.read_text())
        else:
            raise HTTPException(503, "Worldstate unavailable and no local cache found. "
                                     "Run: python scripts/fetch_worldstate.py")

    return mod.parse(raw)


@app.get("/api/worldstate")
def get_worldstate(platform: str = "pc") -> dict:
    if platform not in _PLATFORM_URLS:
        raise HTTPException(400, f"Unknown platform: {platform!r}")
    now = time.time()
    if platform in _ws_cache:
        data, ts = _ws_cache[platform]
        if now - ts < _WS_TTL:
            return data
    parsed = _fetch_worldstate(platform)
    _ws_cache[platform] = (parsed, now)
    return parsed


# ---------------------------------------------------------------------------
# Root — serve the SPA
# ---------------------------------------------------------------------------

from fastapi.responses import FileResponse  # noqa: E402

@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(_static / "index.html"))


@app.get("/live")
def live() -> FileResponse:
    return FileResponse(str(_static / "live.html"))
