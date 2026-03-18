#!/usr/bin/env python3
"""
parse_wiki_data.py
------------------
Reads data/weapons_raw.json and data/mods_raw.json (produced by fetch_wiki_data.py
or extract_data.lua) and outputs clean, calculator-ready files:

  data/weapons.json  — { "Soma Prime": { "impact": 1.2, "puncture": 4.8, ... }, ... }
  data/mods.json     — { "Serration": { "damage_bonus": 1.65 }, ... }

Run:
  python scripts/parse_wiki_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


# ---------------------------------------------------------------------------
# Weapon parsing
# ---------------------------------------------------------------------------
# Wiki weapon entries (from Module:Weapons/data) look like:
# {
#   "Name": "Soma Prime",
#   "Slot": "Primary",
#   "Trigger": "Auto-Spool",
#   "Damage": { "Impact": 1.2, "Puncture": 4.8, "Slash": 6.0 },   ← nested dict
#   OR
#   "Impact": 1.2, "Puncture": 4.8, "Slash": 6.0,                 ← flat fields
#   "FireRate": 15.0,
#   "Magazine": 200,
#   "Reload": 3.0,
#   "CritChance": 0.30,
#   "CritMult": 3.0,
#   "StatusChance": 0.10,
#   "MasteryReq": 7,
#   "Disposition": 1.05,
#   ...
# }

IPS_KEYS = {
    # possible key names in wiki data → canonical name
    "Impact":    "impact",
    "ImpactDmg": "impact",
    "Puncture":  "puncture",
    "PunctureDmg": "puncture",
    "Slash":     "slash",
    "SlashDmg":  "slash",
}

ELEMENTAL_KEYS = {
    "Heat":        "heat",
    "Cold":        "cold",
    "Electricity": "electricity",
    "Toxin":       "toxin",
    "Blast":       "blast",
    "Corrosive":   "corrosive",
    "Gas":         "gas",
    "Magnetic":    "magnetic",
    "Radiation":   "radiation",
    "Viral":       "viral",
    "Void":        "void",
    "Tau":         "tau",
}

STAT_KEYS = {
    "FireRate":     "fire_rate",
    "AttackSpeed":  "fire_rate",   # melee equivalent
    "Magazine":     "magazine",
    "MagSize":      "magazine",
    "Reload":       "reload",
    "ReloadTime":   "reload",
    "CritChance":   "crit_chance",
    "CritMult":     "crit_multiplier",
    "CritMultiplier": "crit_multiplier",
    "StatusChance": "status_chance",
    "MasteryReq":   "mastery_req",
    "Disposition":  "riven_disposition",
    "Slot":         "slot",
    "Trigger":      "trigger",
}


def _parse_weapon(name: str, raw: dict) -> dict | None:
    out: dict = {"name": name}

    # Damage — may be nested under "Damage" key or flat
    damage_src = raw.get("Damage") if isinstance(raw.get("Damage"), dict) else raw

    ips: dict[str, float] = {}
    for wiki_key, canon in IPS_KEYS.items():
        v = damage_src.get(wiki_key)
        if v is not None:
            try:
                ips[canon] = float(v)
            except (TypeError, ValueError):
                pass

    elems: dict[str, float] = {}
    for wiki_key, canon in ELEMENTAL_KEYS.items():
        v = damage_src.get(wiki_key)
        if v is not None:
            try:
                elems[canon] = float(v)
            except (TypeError, ValueError):
                pass

    if not ips and not elems:
        return None  # skip entries with no damage data

    if ips:
        out["base_damage"] = ips
    if elems:
        out["innate_elements"] = elems

    # Other stats
    for wiki_key, canon in STAT_KEYS.items():
        v = raw.get(wiki_key)
        if v is not None:
            try:
                out[canon] = float(v) if isinstance(v, (int, float)) else v
            except (TypeError, ValueError):
                out[canon] = v

    return out


def parse_weapons(raw: dict | list) -> dict:
    # raw may be a dict keyed by name, or a list of dicts
    entries: list[tuple[str, dict]] = []
    if isinstance(raw, dict):
        for k, v in raw.items():
            if isinstance(v, dict):
                name = v.get("Name") or str(k)
                entries.append((name, v))
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                name = item.get("Name", "")
                entries.append((name, item))

    weapons: dict = {}
    skipped = 0
    for name, raw_entry in entries:
        parsed = _parse_weapon(name, raw_entry)
        if parsed:
            weapons[name] = parsed
        else:
            skipped += 1

    print(f"  Weapons parsed: {len(weapons)} kept, {skipped} skipped (no damage data)")
    return weapons


# ---------------------------------------------------------------------------
# Mod parsing
# ---------------------------------------------------------------------------
# Wiki mod entries look like:
# {
#   "Name": "Serration",
#   "Type": "Rifle",
#   "Polarity": "Madurai",
#   "Rarity": "Rare",
#   "MaxRank": 10,
#   "BaseDrain": 4,
#   "Effect": "+165% Damage",      ← raw description string
#   "Stats": [{ "Damage": 0.165 }] ← structured (if present)
# }
#
# Some mods have structured numeric stats; others only have description strings.
# We parse both.

MOD_EFFECT_PATTERNS: list[tuple[str, str]] = [
    # (regex pattern, field name)
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Base\s+)?Damage",         "damage_bonus_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Heat(?:\s+Damage)?",          "heat_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Cold(?:\s+Damage)?",          "cold_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Electricity(?:\s+Damage)?",   "electricity_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Toxin(?:\s+Damage)?",         "toxin_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Blast(?:\s+Damage)?",         "blast_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Corrosive(?:\s+Damage)?",     "corrosive_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Gas(?:\s+Damage)?",           "gas_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Magnetic(?:\s+Damage)?",      "magnetic_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Radiation(?:\s+Damage)?",     "radiation_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Viral(?:\s+Damage)?",         "viral_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Damage\s+to\s+)?(?:Grineer|Corrupted|Corpus|Infested)",
                                                           "faction_bonus_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Critical\s+Chance",           "crit_chance_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Critical\s+Damage",           "crit_damage_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Fire\s+Rate|Attack\s+Speed)", "fire_rate_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Multishot",                   "multishot_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Magazine|Ammo\s+(?:Maximum|Capacity))",
                                                           "magazine_pct"),
]

import re  # noqa: E402 (after dataclasses imports)


def _parse_mod_effect(effect_str: str) -> dict:
    out: dict = {}
    for pattern, field in MOD_EFFECT_PATTERNS:
        m = re.search(pattern, effect_str, re.IGNORECASE)
        if m:
            out[field] = float(m.group(1)) / 100.0
    return out


def _parse_mod(raw: dict) -> dict | None:
    name = raw.get("Name", "")
    if not name:
        return None

    out: dict = {
        "name":       name,
        "type":       raw.get("Type", ""),
        "polarity":   raw.get("Polarity", ""),
        "rarity":     raw.get("Rarity", ""),
        "max_rank":   raw.get("MaxRank", 0),
        "base_drain": raw.get("BaseDrain", 0),
    }

    # Try structured Stats first
    stats = raw.get("Stats")
    if isinstance(stats, list) and stats:
        last = stats[-1]  # max rank stats
        if isinstance(last, dict):
            for k, v in last.items():
                try:
                    out[k.lower()] = float(v)
                except (TypeError, ValueError):
                    pass

    # Parse description string for bonuses
    effect = raw.get("Effect") or raw.get("Description") or ""
    if isinstance(effect, str) and effect:
        parsed = _parse_mod_effect(effect)
        out.update(parsed)
        out["effect_raw"] = effect

    return out


def parse_mods(raw: dict | list) -> dict:
    entries: list[dict] = []
    if isinstance(raw, dict):
        # May be { "ModName": { ... }, ... } or { 1: {...}, 2: {...} }
        for v in raw.values():
            if isinstance(v, dict):
                entries.append(v)
    elif isinstance(raw, list):
        entries = [m for m in raw if isinstance(m, dict)]

    mods: dict = {}
    for entry in entries:
        parsed = _parse_mod(entry)
        if parsed and parsed.get("name"):
            mods[parsed["name"]] = parsed

    print(f"  Mods parsed: {len(mods)}")
    return mods


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    w_raw = DATA_DIR / "weapons_raw.json"
    m_raw = DATA_DIR / "mods_raw.json"

    if not w_raw.exists():
        print(f"Missing {w_raw} — run fetch_wiki_data.py first")
        return
    if not m_raw.exists():
        print(f"Missing {m_raw} — run fetch_wiki_data.py first")
        return

    print("=== Parsing weapons ===")
    weapons = parse_weapons(json.loads(w_raw.read_text()))
    out_w = DATA_DIR / "weapons.json"
    out_w.write_text(json.dumps(weapons, indent=2, ensure_ascii=False))
    print(f"Saved → {out_w}\n")

    print("=== Parsing mods ===")
    mods = parse_mods(json.loads(m_raw.read_text()))
    out_m = DATA_DIR / "mods.json"
    out_m.write_text(json.dumps(mods, indent=2, ensure_ascii=False))
    print(f"Saved → {out_m}\n")


if __name__ == "__main__":
    main()
