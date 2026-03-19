"""
web/api.py — FastAPI backend for the Warframe Damage Calculator.

Endpoints:
  GET  /api/weapons          → list of weapon names + basic stats
  GET  /api/mods             → list of mod names + types
  GET  /api/enemies          → list of enemy names + factions
  POST /api/calculate        → full damage calculation
"""
from __future__ import annotations

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
            "base_damage":      {
                **entry.get("base_damage", {}),
                **entry.get("innate_elements", {}),
            },
            "image":            entry.get("image", ""),
        })
    return sorted(out, key=lambda x: x["name"])


@app.get("/api/mods")
def get_mods() -> list[dict]:
    raw = _raw_mods()
    out = []
    for name, entry in raw.items():
        if name.startswith("Flawed "):
            continue
        out.append({
            "name":     name,
            "type":     entry.get("type", ""),
            "polarity": entry.get("polarity", ""),
            "effect":   entry.get("effect_raw", ""),
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


@app.post("/api/modded-weapon")
def modded_weapon(req: ModdedWeaponRequest) -> dict:
    try:
        weapon = load_weapon(req.weapon)
    except KeyError:
        raise HTTPException(400, f"Unknown weapon: {req.weapon!r}")

    mods = []
    for mod_name in req.mods:
        try:
            mods.append(load_mod(mod_name))
        except KeyError:
            raise HTTPException(400, f"Unknown mod: {mod_name!r}")

    base_damage = weapon.total_base_damage
    raw_w = _raw_weapons().get(weapon.name, {})
    base_cc = float(raw_w.get("crit_chance") or 0.0)
    base_cm = float(raw_w.get("crit_multiplier") or 1.0)
    base_sc = float(raw_w.get("status_chance") or 0.0)

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
    elemental_components = combined_elements + [c for c in innate_secondary if c.amount != 0.0]

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
    crit_mode:    str = "average"   # "average" | "guaranteed" | "max"
    headshot:     bool = False
    viral_stacks: int = 0           # 0–10


@app.post("/api/calculate")
def calculate(req: CalcRequest) -> dict:
    try:
        weapon = load_weapon(req.weapon)
    except KeyError:
        raise HTTPException(400, f"Unknown weapon: {req.weapon!r}")

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

    raw_w = _raw_weapons().get(weapon.name, {})
    base_cc = float(raw_w.get("crit_chance") or 0.0)
    base_cm = float(raw_w.get("crit_multiplier") or 1.0)
    crit_mult = calculate_crit_multiplier(base_cc, base_cm, mode=req.crit_mode)

    calc = DamageCalculator()
    result = calc.calculate(
        weapon=weapon,
        mods=mods,
        enemy=enemy,
        crit_multiplier=crit_mult,
        is_crit_headshot=req.headshot,
        viral_stacks=req.viral_stacks,
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
        "viral_stacks":  req.viral_stacks,
        "breakdown":     breakdown,
        "total":         total,
    }


# ---------------------------------------------------------------------------
# Root — serve the SPA
# ---------------------------------------------------------------------------

from fastapi.responses import FileResponse  # noqa: E402

@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(_static / "index.html"))
