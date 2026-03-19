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

from src.calculator import DamageCalculator, calculate_crit_multiplier
from src.loader import (
    _raw_enemies, _raw_mods, _raw_weapons,
    list_enemies, list_mods, list_weapons,
    load_enemy, load_mod, load_weapon,
)

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
            "base_damage":      entry.get("base_damage", {}),
            "image":            entry.get("image", ""),
        })
    return sorted(out, key=lambda x: x["name"])


@app.get("/api/mods")
def get_mods() -> list[dict]:
    raw = _raw_mods()
    out = []
    for name, entry in raw.items():
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

class CalcRequest(BaseModel):
    weapon:    str
    mods:      list[str] = []
    enemy:     str
    crit_mode: str = "average"   # "average" | "guaranteed" | "max"
    headshot:  bool = False


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
    )

    breakdown = {dtype.name: val for dtype, val in result.items()}
    total = sum(result.values())

    return {
        "weapon":   weapon.name,
        "mods":     req.mods,
        "enemy":    enemy.name,
        "crit_mode": req.crit_mode,
        "crit_multiplier": crit_mult,
        "headshot": req.headshot,
        "breakdown": breakdown,
        "total":    total,
    }


# ---------------------------------------------------------------------------
# Root — serve the SPA
# ---------------------------------------------------------------------------

from fastapi.responses import FileResponse  # noqa: E402

@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(_static / "index.html"))
