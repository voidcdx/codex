# Handoff — Warframe Damage Calculator

## Current Status
All core backend is complete and tested (99 tests passing).
Full pipeline: weapon + mods + enemy → per-type damage breakdown.
Web UI is functional with live modded stats, tooltips, enemy panel, and Viral stack simulation.

## What's Done

### Core (`src/`)
- `enums.py` — DamageType, FactionType, HealthType, ArmorType
- `models.py` — Weapon, Mod, Enemy dataclasses
- `quantizer.py` — `quantize()` with Decimal + ROUND_HALF_UP (never uses Python `round()`)
- `combiner.py` — elemental combination by mod slot order; innate primary/secondary split; Kuva/Tenet HCET priority
- `calculator.py` — full 6-step damage pipeline:
  1. Base × (1 + ΣDamageMods) → floor
  2. × Body part × Crit → warframe_round
  3. × DamageType effectiveness → floor
  4. × Armor mitigation → floor
  5. × (1 + FactionMod) → floor
  6. × Viral stack multiplier → floor  ← new
  Plus: `VIRAL_STACK_MULTIPLIERS` table (0–10 stacks, max ×4.25), crit tier/average/max modes, armor type modifiers (Ferrite/Alloy), Bane mod table
- `loader.py` — `load_weapon()`, `load_mod()`, `load_enemy()` from JSON; case-insensitive lookup; `headshot=True` applies head multiplier

### Data (`data/`)
- `weapons.json` — 588 weapons (primary/secondary/melee) with IPS split, innate elements, crit/status stats, image filename
- `mods.json` — 1534 mods with damage%, elemental%, cc/cd/sc/multishot bonuses, faction bonus
- `enemies.json` — 983 enemies from 11 faction lua files; faction, health_type, armor_type (inferred), base_armor, head_multiplier

### Web (`web/`)
- `api.py` — FastAPI REST: `GET /api/weapons`, `/api/mods`, `/api/enemies`; `POST /api/modded-weapon`, `/api/calculate`
  - `/api/calculate` accepts: `weapon`, `mods[]`, `enemy`, `crit_mode`, `headshot`, `viral_stacks`
  - `/api/weapons` response merges `innate_elements` into `base_damage` so UI shows them on weapon select
- `static/index.html` — dark-theme SPA:
  - Weapon panel: image, crit/status/fire rate/magazine/reload/multishot stats, live modded values
  - 8-slot mod grid filtered by weapon type, live damage table updating on every mod change
  - Enemy panel: faction, health/armor type, armor, health, head multiplier
  - Hit Options: crit mode (average/guaranteed/max), headshot toggle, Viral stacks input (0–10)
  - Results: per-type bar chart with damage breakdown and totals

### CLI
- `__main__.py` — `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" [--crit average|guaranteed|max] [--headshot]`
- `run_web.py` — `python run_web.py` starts dev server on port 8000

### Tests (99 passing)
- `tests/test_quantization.py` — quantizer edge cases
- `tests/test_combiner.py` — elemental combination + innate rules
- `tests/test_loader.py` — JSON → model loading
- `tests/test_calculator.py` — full pipeline: modded damage, body part, faction, armor, crit, Viral stacks

## What's Still Needed

### Status Proc Simulation (next big feature)
The calculator only applies the Viral *hit multiplier* (stacks input). Full proc simulation would add:
- **Slash bleed** — `35% of hit damage / tick, 6 ticks` — ignores armor, bypasses shields
- **Heat burn** — `50% of hit damage / tick, 6 ticks` — applies Heat DR, strips armor stacks
- **Gas cloud** — `50% of hit Toxin damage / tick` — AoE, bypasses shields
- **Corrosive strip** — permanent `-80% armor` per stack (up to 10 strips 100%)
- **Faction double-dip** — Slash/Gas/Heat DOT procs inherit faction mod then apply it again on tick: `proc × (1 + faction)²`

### Data Gaps
- Enemy health_type and armor_type are faction-inferred defaults, not per-enemy.
  Some units use different types (e.g. Corpus Amalgams use Alloy armor).
  A manual override table in `enemies.json` would fix edge cases.

### Frontend Polish
- DPS mode (fire rate × multishot × damage per hit)
- Status proc tick display
- Riven mod support (disposition-aware custom mod builder)

## Branch
Current work is on `claude/continue-work-kuwE9`.
Session-start hook auto-detects the latest `claude/*` branch.
