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


def _parse_attack(raw_attack: dict) -> dict:
    """Parse a single attack entry into a normalized dict."""
    attack_out: dict = {"name": raw_attack.get("AttackName", "")}

    damage_dict = raw_attack.get("Damage") if isinstance(raw_attack.get("Damage"), dict) else {}
    ips, elems = _parse_damage_dict(damage_dict)
    if ips:
        attack_out["base_damage"] = ips
    if elems:
        attack_out["innate_elements"] = elems

    for wiki_key, canon in (
        ("CritChance", "crit_chance"),
        ("CritMultiplier", "crit_multiplier"),
        ("StatusChance", "status_chance"),
        ("FireRate", "fire_rate"),
    ):
        v = raw_attack.get(wiki_key)
        if v is not None:
            try: attack_out[canon] = float(v)
            except (TypeError, ValueError): pass

    shot_type = raw_attack.get("ShotType", "")
    if shot_type:
        attack_out["shot_type"] = shot_type

    ms = raw_attack.get("Multishot")
    if ms is not None:
        try:
            ms_val = int(float(ms))
            if ms_val > 1:
                attack_out["multishot"] = ms_val
        except (TypeError, ValueError):
            pass

    falloff = raw_attack.get("Falloff")
    if isinstance(falloff, dict):
        for fk, ck in (("StartRange", "falloff_start"), ("EndRange", "falloff_end"), ("Reduction", "falloff_reduction")):
            v = falloff.get(fk)
            if v is not None:
                try: attack_out[ck] = float(v)
                except (TypeError, ValueError): pass

    return attack_out


def _parse_weapon(name: str, raw: dict) -> dict | None:
    out: dict = {"name": name}

    attacks_raw = raw.get("Attacks") or []
    parsed_attacks = []
    for raw_attack in attacks_raw:
        if not isinstance(raw_attack, dict):
            continue
        parsed = _parse_attack(raw_attack)
        if parsed.get("base_damage") or parsed.get("innate_elements"):
            parsed_attacks.append(parsed)

    if not parsed_attacks:
        return None

    out["attacks"] = parsed_attacks

    # Promote first-attack stats to weapon level for convenience (crit, status, fire_rate)
    first = parsed_attacks[0]
    for stat in ("crit_chance", "crit_multiplier", "status_chance", "fire_rate"):
        if stat in first:
            out[stat] = first[stat]

    # Top-level stats
    TOP_STAT_KEYS = {
        "Magazine":    "magazine",
        "MagSize":     "magazine",
        "AmmoMax":     "max_ammo",
        "Reload":      "reload",
        "Mastery":     "mastery_req",
        "MasteryReq":  "mastery_req",
        "Disposition": "riven_disposition",
        "Slot":        "slot",
        "Class":       "class",
        "Trigger":     "trigger",
        "Family":      "family",
        "MaxRank":     "max_rank",
        "Image":       "image",
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
    (r"\+(\d+(?:\.\d+)?)%\s*(?:Magazine(?:\s+Capacity)?)",   "magazine_pct"),
    (r"\+(\d+(?:\.\d+)?)%\s*Ammo\s+Maximum",                "ammo_max_pct"),
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

    # Skip Conclave-exclusive (wings icon) mods — identified by /PvPMods/ in InternalName
    if "/PvPMods/" in (raw.get("InternalName") or ""):
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
# Enemy parsing
# ---------------------------------------------------------------------------
# Enemy lua files (enemies_grineer.lua, enemies_corpus.lua, etc.) contain:
#   { "EnemyName": { General = { Faction = "Grineer", ... },
#                    Stats   = { Health = 300, Armor = 500,
#                                Multis = { "Head: 3.0x" }, ... } } }
#
# Health type and armor type are inferred from faction + stats:
#   Grineer        → FLESH     + FERRITE (if armor > 0)
#   Corpus         → FLESH     + ALLOY (if armor > 0)   [shields separate]
#   Infested       → INFESTED_FLESH + NONE (unless fossilized/ancients)
#   Orokin         → FLESH     + ALLOY (if armor > 0)
#   Sentient       → FLESH     + NONE
#   Narmer         → FLESH     + FERRITE (if armor > 0)
#   Techrot/Scaldra → INFESTED_FLESH + NONE
#   Stalker        → FLESH     + ALLOY (if armor > 0)
#   Unaffiliated   → FLESH     + NONE

_FACTION_HEALTH_TYPE: dict[str, str] = {
    "grineer":     "flesh",
    "corpus":      "flesh",
    "infestation": "infested_flesh",
    "orokin":      "flesh",
    "sentient":    "flesh",
    "narmer":      "flesh",
    "themurmur":   "flesh",
    "techrot":     "infested_flesh",
    "scaldra":     "flesh",
    "stalker":     "flesh",
    "anarchs":     "flesh",
    "unaffiliated": "flesh",
}

_FACTION_ARMOR_TYPE: dict[str, str] = {
    "grineer":     "ferrite",
    "corpus":      "alloy",
    "infestation": "none",
    "orokin":      "alloy",
    "sentient":    "none",
    "narmer":      "ferrite",
    "themurmur":   "none",
    "techrot":     "none",
    "scaldra":     "none",
    "stalker":     "alloy",
    "anarchs":     "none",
    "unaffiliated": "none",
}

# File name → canonical faction key
_FILENAME_FACTION: dict[str, str] = {
    "enemies_grineer":     "grineer",
    "enemies_corpus":      "corpus",
    "enemies_infestation": "infestation",
    "enemies_orokin":      "orokin",
    "enemies_sentient":    "sentient",
    "enemies_narmer":      "narmer",
    "enemies_themurmur":   "themurmur",
    "enemies_techrot":     "techrot",
    "enemies_scaldra":     "scaldra",
    "enemies_stalker":     "stalker",
    "enemies_unaffiliated": "unaffiliated",
}


def _parse_head_multiplier(multis: list) -> float:
    """Extract head multiplier from Multis list, e.g. ["Head: 3.0x"] → 3.0."""
    for entry in multis:
        if isinstance(entry, str):
            m = re.search(r"Head\s*:\s*([\d.]+)x", entry, re.IGNORECASE)
            if m:
                return float(m.group(1))
    return 1.0


def _parse_enemy(name: str, raw: dict, faction_key: str) -> dict | None:
    general = raw.get("General") or {}
    stats   = raw.get("Stats") or {}

    faction_raw = general.get("Faction", "").lower()
    # Resolve faction via the file's faction key (more reliable than the string)
    faction = faction_key

    health_type = _FACTION_HEALTH_TYPE.get(faction, "flesh")
    base_armor  = float(stats.get("Armor") or 0)
    armor_type  = _FACTION_ARMOR_TYPE.get(faction, "none") if base_armor > 0 else "none"

    multis = stats.get("Multis") or []
    head_mult = _parse_head_multiplier(multis) if isinstance(multis, list) else 1.0

    return {
        "name":                 name,
        "faction":              faction,
        "health_type":          health_type,
        "armor_type":           armor_type,
        "base_armor":           base_armor,
        "base_health":          float(stats.get("Health") or 0),
        "base_shield":          float(stats.get("Shield") or 0),
        "head_multiplier":      head_mult,
    }


def parse_enemies(lua_files: list) -> dict:
    """Parse all enemies_*.lua files and return merged dict keyed by name."""
    from scripts.parse_lua import lua_to_py  # local import to avoid circular

    enemies: dict = {}
    for lua_path in sorted(lua_files):
        stem = lua_path.stem            # e.g. "enemies_grineer"
        faction_key = _FILENAME_FACTION.get(stem, stem.replace("enemies_", ""))
        print(f"  Parsing {lua_path.name} (faction={faction_key}) …", end=" ", flush=True)
        src = lua_path.read_text(encoding="utf-8")
        raw = lua_to_py(src)
        if not isinstance(raw, dict):
            print("skipped (unexpected format)")
            continue
        count = 0
        for entry_name, entry_data in raw.items():
            if not isinstance(entry_data, dict):
                continue
            parsed = _parse_enemy(str(entry_name), entry_data, faction_key)
            if parsed:
                enemies[str(entry_name)] = parsed
                count += 1
        print(f"{count} entries")
    print(f"  Total enemies: {len(enemies)}")
    return enemies


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
    out_w.write_text(json.dumps(weapons, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved → {out_w}\n")

    print("=== Parsing mods ===")
    mods = parse_mods(json.loads(m_raw.read_text(encoding="utf-8", errors="replace")))
    out_m = DATA_DIR / "mods.json"
    out_m.write_text(json.dumps(mods, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved → {out_m}\n")

    print("=== Parsing enemies ===")
    enemy_files = sorted(DATA_DIR.glob("enemies_*.lua"))
    if not enemy_files:
        print("  No enemies_*.lua files found. Skipping.")
    else:
        import sys
        sys.path.insert(0, str(DATA_DIR.parent))
        enemies = parse_enemies(enemy_files)
        out_e = DATA_DIR / "enemies.json"
        out_e.write_text(json.dumps(enemies, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Saved → {out_e}\n")


if __name__ == "__main__":
    main()
