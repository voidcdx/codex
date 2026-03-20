"""
web/api.py — FastAPI backend for the Warframe Damage Calculator.

Endpoints:
  GET  /api/weapons          → list of weapon names + basic stats
  GET  /api/mods             → list of mod names + types
  GET  /api/enemies          → list of enemy names + factions
  POST /api/calculate        → full damage calculation
  POST /api/optimal-order    → find mod order maximising damage vs enemy
"""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

# Ensure project root on path when run from web/ directory
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import math
from src.calculator import DamageCalculator, calculate_crit_multiplier
from src.combiner import combine_elements, PRIMARY_ELEMENTS
from src.loader import (
    _raw_enemies, _raw_mods, _raw_weapons,
    list_enemies, list_mods, list_weapons,
    load_enemy, load_mod, load_weapon,
)
from src.models import DamageComponent
from src.quantizer import quantize

app = FastAPI(title="Warframe Damage Calculator", version="1.0.0")

# Serve static files (HTML/CSS/JS/images)
_static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static)), name="static")


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
            "reload":           entry.get("reload", None),
            "mastery_req":      entry.get("mastery_req", 0),
            "riven_disposition": entry.get("riven_disposition", None),
            "base_damage":      first_damage,
            "image":            entry.get("image", ""),
            "attacks": [
                {
                    "name": a.get("name", ""),
                    "shot_type": a.get("shot_type", ""),
                    "base_damage": {**a.get("base_damage", {}), **a.get("innate_elements", {})},
                    "crit_chance": a.get("crit_chance", 0),
                    "crit_multiplier": a.get("crit_multiplier", 1),
                    "status_chance": a.get("status_chance", 0),
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
            "head_multiplier": entry.get("head_multiplier", 1),
        })
    return sorted(out, key=lambda x: x["name"])


# ---------------------------------------------------------------------------
# Calculate endpoint
# ---------------------------------------------------------------------------

class ModdedWeaponRequest(BaseModel):
    weapon: str
    mods: list[str] = []
    attack: str | None = None


@app.post("/api/modded-weapon")
def modded_weapon(req: ModdedWeaponRequest) -> dict:
    try:
        weapon = load_weapon(req.weapon, attack_name=req.attack)
    except KeyError as e:
        raise HTTPException(400, str(e))

    mods = []
    for mod_name in req.mods:
        try:
            mods.append(load_mod(mod_name))
        except KeyError:
            raise HTTPException(400, f"Unknown mod: {mod_name!r}")

    base_damage = weapon.total_base_damage
    base_cc = weapon.crit_chance
    base_cm = weapon.crit_multiplier
    base_sc = weapon.status_chance

    total_damage_bonus = sum(m.damage_bonus for m in mods)
    total_cc_bonus = sum(m.cc_bonus for m in mods)
    total_cd_bonus = sum(m.cd_bonus for m in mods)
    total_sc_bonus = sum(m.sc_bonus for m in mods)
    total_ms_bonus = sum(m.multishot_bonus for m in mods)

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

    return {
        "base_damage":  base_dmg_dict,
        "base_total":   round(base_total, 4),
        "modded_damage": modded_dmg_dict,
        "modded_total":  round(modded_total, 4),
        "base_cc":  base_cc,
        "modded_cc": round(base_cc * (1.0 + total_cc_bonus), 6),
        "base_cm":  base_cm,
        "modded_cm": round(base_cm * (1.0 + total_cd_bonus), 6),
        "base_sc":  base_sc,
        "modded_sc": round(base_sc * (1.0 + total_sc_bonus), 6),
        "base_multishot":   1.0,
        "modded_multishot": round(1.0 + total_ms_bonus, 6),
    }


class CalcRequest(BaseModel):
    weapon:       str
    mods:         list[str] = []
    enemy:        str
    attack:       str | None = None
    crit_mode:    str = "average"   # "average" | "guaranteed" | "max"
    headshot:     bool = False
    viral_stacks: int = 0           # 0–10
    corrosive_stacks: int = 0      # 0–10


@app.post("/api/calculate")
def calculate(req: CalcRequest) -> dict:
    try:
        weapon = load_weapon(req.weapon, attack_name=req.attack)
    except KeyError as e:
        raise HTTPException(400, str(e))

    mods = []
    for mod_name in req.mods:
        try:
            mods.append(load_mod(mod_name))
        except KeyError:
            raise HTTPException(400, f"Unknown mod: {mod_name!r}")

    try:
        enemy = load_enemy(req.enemy, headshot=req.headshot)
    except KeyError:
        raise HTTPException(400, f"Unknown enemy: {req.enemy!r}")

    if req.crit_mode not in ("average", "guaranteed", "max"):
        raise HTTPException(400, f"crit_mode must be average/guaranteed/max")

    base_cc = weapon.crit_chance + sum(m.cc_bonus for m in mods)
    base_cm = weapon.crit_multiplier + sum(m.cd_bonus for m in mods)
    crit_mult = calculate_crit_multiplier(base_cc, base_cm, mode=req.crit_mode)

    raw_w = _raw_weapons().get(weapon.name, {})
    fire_rate   = float(raw_w.get("fire_rate")  or 1.0)
    magazine    = float(raw_w.get("magazine")   or 1.0)
    reload_time = float(raw_w.get("reload")     or 0.0)
    base_sc     = weapon.status_chance
    total_sc_bonus = sum(m.sc_bonus for m in mods)
    total_ms_bonus = sum(m.multishot_bonus for m in mods)
    modded_sc   = base_sc * (1.0 + total_sc_bonus)
    modded_ms   = 1.0 + total_ms_bonus

    calc = DamageCalculator()
    result = calc.calculate(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=req.headshot,
        viral_stacks=req.viral_stacks,
        corrosive_stacks=req.corrosive_stacks,
    )
    procs = calc.calculate_procs(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=req.headshot,
    )

    breakdown = {dtype.name: val for dtype, val in result.items()}
    total = sum(result.values())

    return {
        "weapon":        weapon.name,
        "mods":          req.mods,
        "enemy":         enemy.name,
        "crit_mode":     req.crit_mode,
        "crit_multiplier": crit_mult,
        "headshot":      req.headshot,
        "viral_stacks":    req.viral_stacks,
        "corrosive_stacks": req.corrosive_stacks,
        "breakdown":     breakdown,
        "total":         total,
        "procs":         procs,
        "fire_rate":     fire_rate,
        "magazine":      magazine,
        "reload":        reload_time,
        "modded_sc":     round(modded_sc, 6),
        "modded_ms":     round(modded_ms, 6),
    }


# ---------------------------------------------------------------------------
# Optimal mod order endpoint
# ---------------------------------------------------------------------------

class OptimalOrderRequest(BaseModel):
    weapon:           str
    mods:             list[str] = []
    enemy:            str
    attack:           str | None = None
    crit_mode:        str  = "average"
    headshot:         bool = False
    viral_stacks:     int  = 0
    corrosive_stacks: int  = 0


@app.post("/api/optimal-order")
def optimal_order(req: OptimalOrderRequest) -> dict:
    try:
        weapon = load_weapon(req.weapon, attack_name=req.attack)
    except KeyError as e:
        raise HTTPException(400, str(e))

    try:
        enemy = load_enemy(req.enemy, headshot=req.headshot)
    except KeyError:
        raise HTTPException(400, f"Unknown enemy: {req.enemy!r}")

    # Load only non-empty slots
    slots: list[tuple[int, str]] = [(i, n) for i, n in enumerate(req.mods) if n]
    loaded: list[tuple[int, str, object]] = []
    for i, name in slots:
        try:
            loaded.append((i, name, load_mod(name)))
        except KeyError:
            raise HTTPException(400, f"Unknown mod: {name!r}")

    # Identify primary-elemental mods
    elem_entries = [
        (i, name, mod)
        for i, name, mod in loaded
        if any(c.type in PRIMARY_ELEMENTS for c in mod.elemental_bonuses)
    ]

    if len(elem_entries) <= 1:
        return {"optimal_mods": list(req.mods)}

    crit_mult = calculate_crit_multiplier(
        weapon.crit_chance,
        weapon.crit_multiplier,
        mode=req.crit_mode,
    )

    # Build a base slot dict: position → (name, mod)
    base_slots: dict[int, tuple[str, object]] = {i: (n, m) for i, n, m in loaded}
    elem_positions = [i for i, _, _ in elem_entries]
    elem_pairs     = [(n, m) for _, n, m in elem_entries]

    best_total = -1.0
    best_mods  = list(req.mods)

    for perm in itertools.permutations(elem_pairs):
        # Substitute permuted elemental mods back into their original positions
        trial = dict(base_slots)
        for pos, (name, mod) in zip(elem_positions, perm):
            trial[pos] = (name, mod)

        ordered_mods = [trial[i][1] for i in sorted(trial)]

        calc   = DamageCalculator()
        result = calc.calculate(
            weapon=weapon,
            mods=ordered_mods,
            enemy=enemy,
            crit_multiplier=crit_mult,
            is_crit_headshot=req.headshot,
            viral_stacks=req.viral_stacks,
            corrosive_stacks=req.corrosive_stacks,
        )
        total = sum(result.values())

        if total > best_total:
            best_total = total
            # Reconstruct full 8-slot list preserving empty slots
            best_mods = list(req.mods)
            for pos, (name, _) in zip(elem_positions, perm):
                best_mods[pos] = name

    return {"optimal_mods": best_mods}


# ---------------------------------------------------------------------------
# Root — serve the SPA
# ---------------------------------------------------------------------------

from fastapi.responses import FileResponse  # noqa: E402

@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(_static / "index.html"))
