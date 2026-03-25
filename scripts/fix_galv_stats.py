#!/usr/bin/env python3
"""Patch galvanized mod fields into data/mods.json after regeneration.

Run this after parse_wiki_data.py to restore the three galvanized fields
(galv_kill_stat, galv_kill_pct, galv_max_stacks) that the wiki's raw mod
data does not include.
"""
import json
import pathlib

GALV_STATS: dict[str, dict] = {
    "Galvanized Chamber":      {"galv_kill_stat": "multishot_bonus",       "galv_kill_pct": 0.30, "galv_max_stacks": 5},
    "Galvanized Diffusion":    {"galv_kill_stat": "multishot_bonus",       "galv_kill_pct": 0.30, "galv_max_stacks": 4},
    "Galvanized Hell":         {"galv_kill_stat": "multishot_bonus",       "galv_kill_pct": 0.30, "galv_max_stacks": 4},
    "Galvanized Crosshairs":   {"galv_kill_stat": "cc_bonus",              "galv_kill_pct": 0.40, "galv_max_stacks": 5},
    "Galvanized Scope":        {"galv_kill_stat": "cc_bonus",              "galv_kill_pct": 0.40, "galv_max_stacks": 5},
    "Galvanized Steel":        {"galv_kill_stat": "cd_bonus",              "galv_kill_pct": 0.30, "galv_max_stacks": 4},
    "Galvanized Aptitude":     {"galv_kill_stat": "aptitude_damage_bonus", "galv_kill_pct": 0.40, "galv_max_stacks": 2},
    "Galvanized Savvy":        {"galv_kill_stat": "aptitude_damage_bonus", "galv_kill_pct": 0.40, "galv_max_stacks": 2},
    "Galvanized Shot":         {"galv_kill_stat": "aptitude_damage_bonus", "galv_kill_pct": 0.40, "galv_max_stacks": 3},
    "Galvanized Elementalist": {"galv_kill_stat": "sc_bonus",              "galv_kill_pct": 0.30, "galv_max_stacks": 4},
}

path = pathlib.Path("data/mods.json")
mods: dict = json.loads(path.read_text(encoding="utf-8"))

patched = 0
for name, fields in GALV_STATS.items():
    if name in mods:
        mods[name].update(fields)
        patched += 1
    else:
        print(f"  WARNING: {name!r} not found in mods.json — skipped")

path.write_text(json.dumps(mods, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Patched {patched}/{len(GALV_STATS)} galvanized mods → data/mods.json")
