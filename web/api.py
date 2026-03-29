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

import asyncio
import logging
import sys
import time
import json
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure project root on path when run from web/ directory
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import math
from src.arcanes import ARCANE_PRESETS, ARCANE_DISPLAY_NAMES, ARCANE_RESTRICTIONS, ARCANE_MAX_STACKS, make_arcane
from src.buffs import BUFF_PRESETS, BUFF_DISPLAY_NAMES, make_buff
from src.calculator import DamageCalculator, calculate_crit_multiplier, calculate_falloff_multiplier, status_chance_per_pellet
from src.combiner import combine_elements, PRIMARY_ELEMENTS
from src.loader import (
    _mod_family, _raw_enemies, _raw_mods, _raw_weapons,
    list_enemies, list_mods, list_weapons,
    load_enemy, load_mod, load_weapon, make_riven_mod,
)
from src.models import Buff, DamageComponent
from src.quantizer import quantize, quantize_cdm
from src.scaling import scale_enemy_stats
from src.version import APP_VERSION, GAME_DATA_VERSION

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate limiting — per-IP on worldstate endpoint
# ---------------------------------------------------------------------------

def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, respecting X-Forwarded-For from Railway's proxy."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        ip = xff.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    # Strip port from IPv4 (e.g. "1.2.3.4:12345" → "1.2.3.4")
    # IPv6 literals start with "[" when port is appended — leave those alone
    if ip and ":" in ip and not ip.startswith("["):
        ip = ip.rsplit(":", 1)[0]
    return ip


_limiter = Limiter(key_func=_get_client_ip)


# ---------------------------------------------------------------------------
# Background worldstate refresh
# ---------------------------------------------------------------------------

# Populated at module level (after worldstate section); referenced here by name
# since Python resolves globals at call time, not definition time.

async def _worldstate_bg_loop() -> None:
    """Refresh worldstate on a fixed interval."""
    global _ws_cache, _ws_error
    while True:
        try:
            parsed, raw = await asyncio.to_thread(_fetch_worldstate)
            _ws_cache = (parsed, raw, time.time())
            _ws_error = ""
        except Exception as exc:
            _ws_error = str(exc)
            _logger.warning("Worldstate refresh failed: %s", exc)
        sleep_time = 30 if _ws_cache is None else _WS_TTL
        await asyncio.sleep(sleep_time)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    task = asyncio.create_task(_worldstate_bg_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Warframe Damage Calculator", version=APP_VERSION, lifespan=_lifespan)

# Serve static files (HTML/CSS/JS/images)
_static = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_static)), name="static")

app.state.limiter = _limiter
app.add_middleware(SlowAPIMiddleware)


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    retry_after = getattr(exc, "retry_after", 60)
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(retry_after)},
        content={"detail": "Too Many Requests", "retry_after": retry_after},
    )


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
                    "falloff_start": a.get("falloff_start"),
                    "falloff_end": a.get("falloff_end"),
                    "falloff_reduction": a.get("falloff_reduction", 0),
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
            "family":          _mod_family(name),
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
    combo_counter: int = 0                # melee combo raw hit count
    riven: RivenSpec | None = None
    bonus_element: str | None = None      # "heat" | "cold" | "electricity" | "toxin"
    bonus_element_pct: float = 0.0        # 0.25–0.60
    arcanes: list[ArcaneSpec] = []        # weapon arcanes (max 2)
    cold_stacks: int = Field(default=0, ge=0, le=10)  # Cold proc stacks (flat +0.1 CDM each)


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

    combo_tiers = math.floor(req.combo_counter / 5)
    total_damage_bonus = sum(m.damage_bonus for m in mods) + arcane_damage_bonus
    combo_cc_bonus = sum(m.cc_per_combo_tier for m in mods) * combo_tiers
    total_cc_bonus = sum(m.cc_bonus for m in mods) + galv_cc_bonus + arcane_cc_bonus + combo_cc_bonus
    total_cd_bonus = sum(m.cd_bonus for m in mods) + galv_cd_bonus + arcane_cd_bonus
    combo_sc_bonus = sum(m.sc_per_combo_tier for m in mods) * combo_tiers
    total_sc_bonus = sum(m.sc_bonus for m in mods) + galv_sc_bonus + combo_sc_bonus
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
        "modded_cc": round(base_cc * (1.0 + total_cc_bonus), 6),
        "base_cm":  base_cm,
        "modded_cm": quantize_cdm(base_cm * (1.0 + total_cd_bonus) + min(req.cold_stacks, 10) * 0.1),
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
    cold_stacks:  int = Field(default=0, ge=0, le=10)  # Cold proc stacks (flat +0.1 CDM each)
    ability_strip_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    cp_strip_pct:      float = Field(default=0.0, ge=0.0, le=1.0)
    distance:          float = Field(default=0.0, ge=0.0)  # firing distance in meters


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

    calc_combo_tiers = math.floor(req.combo_counter / 5)
    combo_cc = sum(m.cc_per_combo_tier for m in mods) * calc_combo_tiers
    combo_sc = sum(m.sc_per_combo_tier for m in mods) * calc_combo_tiers
    base_cc = weapon.crit_chance * (1.0 + sum(m.cc_bonus for m in mods) + galv_cc + arcane_cc + combo_cc)
    base_cm = quantize_cdm(weapon.crit_multiplier * (1.0 + sum(m.cd_bonus for m in mods) + galv_cd + arcane_cd) + min(req.cold_stacks, 10) * 0.1)
    crit_mult = calculate_crit_multiplier(base_cc, base_cm, mode=req.crit_mode)

    raw_w = _raw_weapons().get(weapon.name, {})
    fire_rate   = float(raw_w.get("fire_rate")  or 1.0)
    magazine    = float(raw_w.get("magazine")   or 1.0)
    reload_time = float(raw_w.get("reload")     or 0.0)
    base_sc     = weapon.status_chance
    total_sc_bonus = sum(m.sc_bonus for m in mods) + galv_sc + combo_sc
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
        ability_strip_pct=req.ability_strip_pct,
        cp_strip_pct=req.cp_strip_pct,
        enemy_level=req.enemy_level,
        steel_path=req.steel_path,
        eximus=req.eximus,
        combo_counter=req.combo_counter,
        unique_statuses=req.unique_statuses,
        galvanized_stacks=galv_stacks,
        buffs=buff_objects,
        arcanes=arcane_objects,
        distance=req.distance,
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

    # CO curve: damage at each unique_statuses 0–10
    has_co = any(m.condition_overload_bonus > 0 for m in mods)
    co_curve = None
    if has_co:
        co_curve = []
        for us in range(11):
            if us == req.unique_statuses:
                co_curve.append(round(total, 2))
            else:
                r = calc.calculate(
                    weapon=weapon, mods=mods, enemy=enemy,
                    crit_multiplier=crit_mult,
                    is_crit_headshot=(effective_part != "Body"),
                    multishot=modded_ms,
                    viral_stacks=req.viral_stacks,
                    corrosive_stacks=req.corrosive_stacks,
                    ability_strip_pct=req.ability_strip_pct,
                    cp_strip_pct=req.cp_strip_pct,
                                enemy_level=req.enemy_level,
                    steel_path=req.steel_path,
                    eximus=req.eximus,
                    combo_counter=req.combo_counter,
                    unique_statuses=us,
                    galvanized_stacks=galv_stacks,
                    buffs=buff_objects,
                    arcanes=arcane_objects,
                    distance=req.distance,
                )
                co_curve.append(round(sum(r.values()), 2))

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
        "ability_strip_pct": req.ability_strip_pct,
        "cp_strip_pct": req.cp_strip_pct,
        "galvanized_stacks": galv_stacks,
        "buffs":         [{"name": b.name, "strength": bs.strength} for b, bs in zip(buff_objects, req.buffs)],
        "arcanes":       [{"name": a.name, "stacks": a.stacks} for a in arcane_objects],
        "breakdown":     breakdown,
        "total":         total,
        "co_curve":      co_curve,
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
        "distance":      req.distance,
        "falloff_multiplier": round(calculate_falloff_multiplier(
            req.distance, weapon.falloff_start, weapon.falloff_end, weapon.falloff_reduction
        ), 6),
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

_WS_URL = "https://api.warframe.com/cdn/worldState.php"
_WS_TTL = 60  # 1 minute
_ws_cache: tuple[dict, dict, float] | None = None  # (parsed, raw, timestamp)
_ws_error: str = ""

# trust_env=False fully disables HTTPS_PROXY/HTTP_PROXY env vars (proxies={} does not)
_ws_session = _requests.Session()
_ws_session.trust_env = False
_ws_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.warframe.com",
    "Referer": "https://www.warframe.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
})


_parse_worldstate_mod = None  # loaded once on first call


def _load_parse_worldstate_mod():
    """Load scripts/parse_worldstate.py once and cache the module reference."""
    global _parse_worldstate_mod
    if _parse_worldstate_mod is not None:
        return _parse_worldstate_mod
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "parse_worldstate",
        Path(__file__).parent.parent / "scripts" / "parse_worldstate.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    _parse_worldstate_mod = mod
    return mod


def _fetch_worldstate() -> dict:
    """Fetch and parse live worldstate.

    Retries up to 3 times with 2-second backoff before giving up.
    Falls back to a local snapshot if one exists.
    """
    mod = _load_parse_worldstate_mod()
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            r = _ws_session.get(_WS_URL, timeout=15)
            r.raise_for_status()
            raw = r.json()
            return mod.parse(raw), raw
        except Exception as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(2)

    # All attempts failed — fall back to local snapshot if available
    raw_path = Path(__file__).parent.parent / "data" / "worldstate_raw.json"
    if raw_path.exists():
        _logger.warning("Worldstate fetch failed (%s); using local snapshot", last_exc)
        raw = json.loads(raw_path.read_text())
        return mod.parse(raw), raw
    raise RuntimeError(f"Worldstate fetch failed: {last_exc}") from last_exc


@app.get("/api/worldstate")
@_limiter.limit("30/minute")
def get_worldstate(request: Request) -> dict:
    if _ws_cache is None:
        raise HTTPException(503, f"Worldstate unavailable — {_ws_error or 'first fetch in progress'}")
    data, _raw, _ = _ws_cache
    return data


@app.get("/api/worldstate/debug-news")
@_limiter.limit("10/minute")
def debug_worldstate_news(request: Request) -> dict:
    if _ws_cache is None:
        raise HTTPException(503, f"Worldstate unavailable — {_ws_error or 'first fetch in progress'}")
    _parsed, raw, _ = _ws_cache
    mod = _load_parse_worldstate_mod()
    return mod._debug_news(raw)


# ---------------------------------------------------------------------------
# Root — serve the SPA
# ---------------------------------------------------------------------------


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(_static / "index.html"), headers={"Cache-Control": "no-store"})


@app.get("/live")
def live() -> FileResponse:
    return FileResponse(str(_static / "live.html"), headers={"Cache-Control": "no-store"})


@app.get("/factions")
def factions() -> FileResponse:
    return FileResponse(str(_static / "factions.html"))


@app.get("/enemy-preview")
def enemy_preview() -> FileResponse:
    return FileResponse(str(_static / "enemy-preview.html"))
