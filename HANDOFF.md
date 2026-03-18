# Handoff — Warframe Damage Calculator

## Current Status
All core calculator logic is implemented and tested (65 tests passing).
Weapon and mod data has been scraped from wiki.warframe.com and parsed into JSON.

## What's Done
- `src/enums.py` — DamageType, FactionType, HealthType, ArmorType
- `src/models.py` — Weapon, Mod, Enemy dataclasses
- `src/quantizer.py` — `quantize()` with Decimal + ROUND_HALF_UP (no banker's rounding)
- `src/combiner.py` — elemental combination by mod slot order
- `src/calculator.py` — full 5-step damage pipeline + crit + armor + faction
- `data/weapons.json` — 588 weapons (primary/secondary/melee) with IPS split, crit stats, etc.
- `data/mods.json` — 1534 mods with parsed bonus fields
- `scripts/parse_lua.py` — Lua module parser (handles wiki's statement-sequence format)
- `scripts/parse_wiki_data.py` — normalizes raw JSON into calculator-ready format

## Data Pipeline (for re-scraping)
The wiki blocks automated HTTP. Data must be downloaded manually:

1. Open in browser → Ctrl+S into `data/`:
   - `https://wiki.warframe.com/w/Module:Weapons/data/primary?action=raw` → `weapons_primary.lua`
   - `https://wiki.warframe.com/w/Module:Weapons/data/secondary?action=raw` → `weapons_secondary.lua`
   - `https://wiki.warframe.com/w/Module:Weapons/data/melee?action=raw` → `weapons_melee.lua`
   - `https://wiki.warframe.com/w/Module:Mods/data?action=raw` → `mods_data.lua`
2. `python scripts/parse_lua.py` → produces `weapons_raw.json`, `mods_raw.json`
3. `python scripts/parse_wiki_data.py` → produces `weapons.json`, `mods.json`

## !! Three Things Still Needed !!

### 1. Enemy Database (`data/enemies.json`)
We have the `Enemy` dataclass and enums but no actual enemy data.
Need to scrape `Module:Enemies/data` from the wiki the same way as weapons:
- `https://wiki.warframe.com/w/Module:Enemies/data?action=raw` → `data/enemies_data.lua`
- Then parse with `parse_lua.py` and add an enemy-specific normalizer to `parse_wiki_data.py`

Each enemy needs:
- `faction` → `FactionType` enum
- `health_type` → `HealthType` enum  (maps to FLESH, ROBOTIC, SHIELDS, etc.)
- `armor_type` → `ArmorType` enum   (NONE, FERRITE, ALLOY)
- `base_armor` → float
- `body_part_multiplier` → float (default 1.0, head = 2.0)

### 2. Data Loader (`src/loader.py`)
Converts `weapons.json` and `mods.json` into the `Weapon` and `Mod` objects
the `DamageCalculator` expects.

Key mapping work:
- `"impact": 1.2` → `{DamageType.IMPACT: 1.2}` in `Weapon.base_damage`
- `"heat_pct": 0.9` → `DamageComponent(DamageType.HEAT, 0.9)` in `Mod.elemental_bonuses`
- `"damage_bonus_pct": 1.65` → `Mod.damage_bonus = 1.65`
- `"faction_bonus": 0.55, "faction_target": "corpus"` → `Mod.faction_bonus`, `Mod.faction_type`

### 3. CLI / Entrypoint
A simple way to run a full calculation from the command line, e.g.:
```
python -m dc "Soma Prime" "Serration" "Split Chamber" "Primed Bane of Grineer" vs "Heavy Gunner"
```
Or an interactive mode. Exact UX TBD with the user.

## Key Data Format Examples

### weapons.json entry
```json
"Soma Prime": {
  "name": "Soma Prime",
  "base_damage": {"impact": 1.2, "puncture": 4.8, "slash": 6.0},
  "crit_chance": 0.3,
  "crit_multiplier": 3.0,
  "status_chance": 0.1,
  "fire_rate": 15.0,
  "magazine": 200.0,
  "reload": 3.0,
  "mastery_req": 7.0,
  "slot": "Primary",
  "class": "Rifle"
}
```

### mods.json entry
```json
"Serration": {
  "name": "Serration",
  "type": "Rifle",
  "max_rank": 10,
  "damage_bonus_pct": 1.65,
  "effect_raw": "+165% Damage"
}
```
```json
"Hellfire": {
  "name": "Hellfire",
  "type": "Rifle",
  "max_rank": 5,
  "heat_pct": 0.9,
  "effect_raw": "+90% <DT_FIRE_COLOR>Heat"
}
```
```json
"Primed Bane of Corpus": {
  "name": "Primed Bane of Corpus",
  "type": "Rifle",
  "max_rank": 10,
  "faction_bonus": 0.55,
  "faction_target": "corpus"
}
```

## Branch
All work is on `claude/continue-work-WfJ0X`.
