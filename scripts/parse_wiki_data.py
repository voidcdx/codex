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


def _parse_damage_dict(d: dict) -> tuple[dict, dict]:
    """Extract IPS and elemental amounts from a Damage sub-dict."""
    ips: dict[str, float] = {}
    elems: dict[str, float] = {}
    for wiki_key, canon in IPS_KEYS.items():
        v = d.get(wiki_key)
        if v is not None:
            try: ips[canon] = float(v)
            except (TypeError, ValueError): pass
    for wiki_key, canon in ELEMENTAL_KEYS.items():
        v = d.get(wiki_key)
        if v is not None:
            try: elems[canon] = float(v)
            except (TypeError, ValueError): pass
    return ips, elems


def _parse_weapon(name: str, raw: dict) -> dict | None:
    out: dict = {"name": name}

    # Damage lives inside Attacks[N].Damage (wiki format)
    # Use the first attack named "Normal Attack", or index 0.
    attacks = raw.get("Attacks") or []
    normal = next(
        (a for a in attacks if isinstance(a, dict)
         and a.get("AttackName", "").lower() == "normal attack"),
        attacks[0] if attacks else None,
    )

    if normal is None:
        return None

    damage_dict = normal.get("Damage") if isinstance(normal.get("Damage"), dict) else {}
    ips, elems = _parse_damage_dict(damage_dict)

    if not ips and not elems:
        return None

    if ips:
        out["base_damage"] = ips
    if elems:
        out["innate_elements"] = elems

    # Per-attack stats (crit, status, fire rate)
    ATTACK_STAT_KEYS = {
        "CritChance":     "crit_chance",
        "CritMultiplier": "crit_multiplier",
        "StatusChance":   "status_chance",
        "FireRate":       "fire_rate",
    }
    for wiki_key, canon in ATTACK_STAT_KEYS.items():
        v = normal.get(wiki_key)
        if v is not None:
            try: out[canon] = float(v)
            except (TypeError, ValueError): pass

    # Top-level stats
    TOP_STAT_KEYS = {
        "Magazine":    "magazine",
        "MagSize":     "magazine",
        "Reload":      "reload",
        "Mastery":     "mastery_req",
        "MasteryReq":  "mastery_req",
        "Disposition": "riven_disposition",
        "Slot":        "slot",
        "Class":       "class",
        "Trigger":     "trigger",
        "Family":      "family",
        "MaxRank":     "max_rank",
    }
    for wiki_key, canon in TOP_STAT_KEYS.items():
        v = raw.get(wiki_key)
        if v is not None:
            try: out[canon] = float(v) if isinstance(v, (int, float)) else v
            except (TypeError, ValueError): out[canon] = v

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
# Wiki mod entries (from Module:Mods/data) look like:
# {
#   "Name": "Serration",
#   "Type": "Rifle",
#   "Polarity": "Madurai",
#   "Rarity": "Rare",
#   "MaxRank": 10,      ← also "fusionLimit" in some exports
#   "BaseDrain": 4,
#   "Effect": "+165% Damage",           ← plain string
#   OR (from WFCD-style exports):
#   "levelStats": [                     ← per-rank stats array
#       {"stats": ["+16.5% Damage"]},   ← rank 0
#       ...
#       {"stats": ["+165% Damage"]}     ← rank 10 (max)
#   ]
# }
#
# Elemental stat strings embed DT_ color tags, e.g.:
#   "+90% <DT_FIRE_COLOR>Heat"
#   "+90% <DT_FREEZE_COLOR>Cold"
# We strip the tag and match the element name.
#
# Faction mods use a multiplier format:
#   "x1.55 Damage to Corpus"
# Faction bonus = multiplier - 1.0  (e.g. x1.55 → 0.55)

# Map DT_ color tags → elemental type name
DT_TAG_MAP: dict[str, str] = {
    "DT_FIRE_COLOR":        "heat",
    "DT_FREEZE_COLOR":      "cold",
    "DT_ELECTRICITY_COLOR": "electricity",
    "DT_POISON_COLOR":      "toxin",
    "DT_EXPLOSION_COLOR":   "blast",
    "DT_RADIATION_COLOR":   "radiation",
    "DT_GAS_COLOR":         "gas",
    "DT_MAGNETIC_COLOR":    "magnetic",
    "DT_VIRAL_COLOR":       "viral",
    "DT_CORROSIVE_COLOR":   "corrosive",
    "DT_IMPACT_COLOR":      "impact",
    "DT_PUNCTURE_COLOR":    "puncture",
    "DT_SLASH_COLOR":       "slash",
    "DT_RADIANT_COLOR":     "void",
    "DT_SENTIENT":          "sentient",
}

# Plain element name → field suffix (for strings without DT_ tags)
ELEM_NAME_MAP: dict[str, str] = {
    "heat": "heat_pct", "cold": "cold_pct",
    "electricity": "electricity_pct", "toxin": "toxin_pct",
    "blast": "blast_pct", "radiation": "radiation_pct",
    "gas": "gas_pct", "magnetic": "magnetic_pct",
    "viral": "viral_pct", "corrosive": "corrosive_pct",
}

MOD_EFFECT_PATTERNS: list[tuple[str, str]] = [
    # plain "+N% Damage" (no element)
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Base\s+)?Damage(?!\s+to)",  "damage_bonus_pct"),
    # faction: "x1.55 Damage to Corpus"
    (r"x([\d.]+)\s+Damage\s+to\s+(?:Grineer|Corpus|Infested|Corrupted)",
                                                              "_faction_mult"),
    # crit
    (r"\+(\d+(?:\.\d+)?)%\s*Critical\s+Chance",              "crit_chance_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Critical\s+Damage",              "crit_damage_pct"),
    # other stats
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Fire\s+Rate|Attack\s+Speed)", "fire_rate_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Multishot",                      "multishot_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Magazine|Ammo\s+(?:Maximum|Capacity))",
                                                              "magazine_pct"),
]

import re  # noqa: E402 (after dataclasses imports)


def _parse_mod_effect(effect_str: str) -> dict:
    """Parse a single stat string from a mod entry."""
    out: dict = {}

    # Strip DT_ color tags: "<DT_FIRE_COLOR>Heat" → "Heat"
    # Also capture the tag so we know which element it is.
    dt_match = re.search(r"<(DT_\w+)>(\w+)", effect_str)
    if dt_match:
        tag, elem_name = dt_match.group(1), dt_match.group(2).lower()
        elem_type = DT_TAG_MAP.get(tag, elem_name)
        # Find the associated percentage
        pct_m = re.search(r"\+(\d+(?:\.\d+)?)%", effect_str)
        if pct_m:
            field = ELEM_NAME_MAP.get(elem_type, f"{elem_type}_pct")
            out[field] = float(pct_m.group(1)) / 100.0
        return out

    # Plain element name without tag (fallback)
    for elem, field in ELEM_NAME_MAP.items():
        if re.search(rf"\+\d[\d.]*%\s*{elem}(?:\s+Damage)?", effect_str, re.IGNORECASE):
            pct_m = re.search(r"\+(\d+(?:\.\d+)?)%", effect_str)
            if pct_m:
                out[field] = float(pct_m.group(1)) / 100.0
            return out

    # Faction multiplier: "x1.55 Damage to Corpus" → faction_bonus = 0.55
    fact_m = re.search(r"x([\d.]+)\s+Damage\s+to\s+(\w+)", effect_str, re.IGNORECASE)
    if fact_m:
        out["faction_bonus"] = round(float(fact_m.group(1)) - 1.0, 6)
        out["faction_target"] = fact_m.group(2).lower()
        return out

    # Generic patterns (damage bonus, crit, fire rate, etc.)
    for pattern, field in MOD_EFFECT_PATTERNS:
        m = re.search(pattern, effect_str, re.IGNORECASE)
        if m:
            out[field] = float(m.group(1)) / 100.0
            break

    return out


def _parse_mod(raw: dict) -> dict | None:
    name = raw.get("Name", "")
    if not name:
        return None

    max_rank = raw.get("MaxRank") or raw.get("fusionLimit") or 0

    out: dict = {
        "name":       name,
        "type":       raw.get("Type") or raw.get("compatName", ""),
        "polarity":   raw.get("Polarity", ""),
        "rarity":     raw.get("Rarity", ""),
        "max_rank":   int(max_rank),
        "base_drain": raw.get("BaseDrain") or raw.get("baseDrain") or 0,
    }

    # levelStats: per-rank array — use last entry (max rank)
    level_stats = raw.get("levelStats") or raw.get("Stats")
    if isinstance(level_stats, list) and level_stats:
        last = level_stats[-1]
        stat_strings: list[str] = []
        if isinstance(last, dict):
            stat_strings = last.get("stats", [])
        elif isinstance(last, list):
            stat_strings = last
        for s in stat_strings:
            if isinstance(s, str):
                parsed = _parse_mod_effect(s)
                out.update(parsed)
        if stat_strings:
            out["effect_raw"] = " | ".join(stat_strings)

    # Fallback: plain Effect/Description string
    if "effect_raw" not in out:
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
        if not parsed or not parsed.get("name"):
            continue
        n = parsed["name"]
        # Keep the entry with the highest max_rank (deduplicate legacy versions)
        if n not in mods or parsed["max_rank"] > mods[n]["max_rank"]:
            mods[n] = parsed

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
