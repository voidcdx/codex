# Handoff — Warframe Damage Calculator

## Current Status
All core backend complete and tested (110 tests passing).
Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs + DPS.
Web UI functional with live modded stats, tooltips, enemy panel, Viral stacks, proc display, and DPS section.

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
  6. × Viral stack multiplier → floor
  Plus: `calculate_procs()` — Slash Bleed, Heat Burn, Gas Cloud proc DPT/total
  - Slash: 35% of total Step-2 damage / tick, 6 ticks, faction double-dips
  - Heat: 50% of total Step-2 damage / tick, 6 ticks, applies Heat type-effectiveness, faction double-dips
  - Gas: 0.5 × base × (1+damage_bonus) × (1+faction)² × crit × body_part — ignores elemental mods, wiki-verified
- `loader.py` — `load_weapon()`, `load_mod()`, `load_enemy()` from JSON; case-insensitive; headshot support

**Bug fix:** Mod-sourced secondary elements (Magnetic, Blast, Corrosive, Gas, Radiation, Viral)
were previously silently dropped. Now collected as `mod_secondary` and passed through directly,
same treatment as innate secondary elements.

### Data (`data/`)
- `weapons.json` — 588 weapons (primary/secondary/melee) with IPS split, innate elements, crit/status/fire_rate/magazine/reload stats, image filename
- `mods.json` — 1534 mods with damage%, elemental%, cc/cd/sc/multishot bonuses, faction bonus
- `enemies.json` — 983 enemies from 11 faction lua files; faction, health_type, armor_type (inferred), base_armor, head_multiplier

### Web (`web/`)
- `api.py` — FastAPI REST: `GET /api/weapons`, `/api/mods`, `/api/enemies`; `POST /api/modded-weapon`, `/api/calculate`
  - `/api/calculate` accepts: `weapon`, `mods[]`, `enemy`, `crit_mode`, `headshot`, `viral_stacks`
  - `/api/calculate` returns: `breakdown`, `total`, `procs` (Slash/Heat/Gas), `fire_rate`, `magazine`, `reload`, `modded_sc`, `modded_ms`
- `static/index.html` — dark-theme SPA:
  - Weapon panel: image, crit/status/fire rate/magazine/reload/multishot stats, live modded values
  - 8-slot mod grid filtered by weapon type, live damage table updating on every mod change
  - Enemy panel: faction, health/armor type, armor, health, head multiplier
  - Hit Options: crit mode (average/guaranteed/max), headshot toggle, Viral stacks input (0–10)
  - Results: per-type bar chart with damage breakdown, totals
  - Status Procs table: Slash (Bleed), Heat (Burn), Gas (Cloud) — damage/tick × ticks = total
  - DPS section: Burst DPS, Sustained DPS (reload-adjusted), proc DPS per type, Total w/ procs

### CLI
- `__main__.py` — `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" [--crit average|guaranteed|max] [--headshot]`
- `run_web.py` — `python run_web.py` starts dev server on port 8000

### Tests (110 passing)
- `tests/test_quantization.py` — quantizer edge cases
- `tests/test_combiner.py` — elemental combination + innate rules
- `tests/test_loader.py` — JSON → model loading
- `tests/test_calculator.py` — M7–M13: modded damage, body part, faction, armor, crit, Viral stacks, secondary elemental mods, status procs (Slash/Heat/Gas with wiki examples)

## What's Still Needed

### Riven Mod Support
Custom mod builder with disposition-aware stats. Player enters riven curse/boon values → generates a `Mod` object and slots it in. Needs:
- UI: riven builder panel (select stat type + value)
- No data changes needed — Mod dataclass already supports arbitrary bonuses

### Corrosive Strip
- Permanent `-26% armor per stack` (up to 10 stacks = 100% strip)
- Would need enemy armor to be mutable during calculation or shown as a separate "after strip" result

### Enemy Data Gaps
- Health_type and armor_type are faction-inferred defaults, not per-enemy.
  Some units differ (e.g. Corpus Amalgams use Alloy armor).
  A manual override table in `enemies.json` would fix edge cases.

### Toxin Proc
- Bypasses shields, deals Toxin damage directly to health
- Formula similar to Slash but targets health layer only

## Branch
Push target: `claude/continue-work-hVQ4u` on `https://github.com/voidcdx/dc`.
Session-start hook creates a local branch; always push with:
```bash
git push origin HEAD:claude/continue-work-hVQ4u
```
