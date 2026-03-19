# Handoff — Warframe Damage Calculator

## Current Status
All core backend is complete and tested (95 tests passing).
Full pipeline: weapon + mods + enemy → per-type damage breakdown.

## What's Done
- `src/enums.py` — DamageType, FactionType, HealthType, ArmorType
- `src/models.py` — Weapon, Mod, Enemy dataclasses
- `src/quantizer.py` — `quantize()` with Decimal + ROUND_HALF_UP
- `src/combiner.py` — elemental combination by mod slot order
- `src/calculator.py` — full 5-step damage pipeline + crit + armor + faction
- `src/loader.py` — `load_weapon()`, `load_mod()`, `load_enemy()` from JSON; case-insensitive lookup; `headshot=True` applies head multiplier
- `data/weapons.json` — 588 weapons with IPS split, crit stats, image filename
- `data/mods.json` — 1534 mods with damage%, elemental%, faction bonus
- `data/enemies.json` — 983 enemies parsed from 11 faction lua files; faction, health_type, armor_type (inferred), base_armor, head_multiplier
- `__main__.py` — CLI: `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" [--crit average|guaranteed|max] [--headshot]`
- `web/api.py` — FastAPI REST API: GET /api/weapons, /api/mods, /api/enemies; POST /api/calculate
- `web/static/index.html` — dark-theme SPA with weapon/mod/enemy selects (live search), crit mode, headshot toggle, bar chart breakdown
- `run_web.py` — `python run_web.py` starts the dev server on port 8000
- 95 passing tests

## What's Still Needed
### Frontend polish
- Weapon images: user has 619 PNGs — copy into `web/static/images/weapons/`
  Filenames: `Soma-Prime.png` convention (spaces→`-`, `&`→`and`, parens stripped)
  `weapons.json` already has `"image"` field on every weapon
- Multishot display (Split Chamber doubles projectiles, not per-hit damage)
- Status chance / proc display
- DPS mode (fire rate × damage)

### Data gaps
- Enemy health_type and armor_type are faction-inferred defaults, not per-enemy.
  Some units within a faction use different types (e.g. Corpus Amalgams use Alloy armor).
  Could be refined with a manual override table.

## Branch
All work is on `claude/review-docs-4JbbC`.
Session-start hook auto-detects the latest `claude/*` branch.
