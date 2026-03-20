# Handoff — Warframe Damage Calculator

## Current Status
All core backend complete and tested (120 tests passing).
Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs + DPS.
Web UI functional. **Design overhaul in progress on `claude/design-overhaul-bmwUa`.**

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
  Plus: `calculate_procs()` — Slash Bleed, Heat Burn, Gas Cloud, Toxin, Electricity, Corrosive strip
  - Slash: 35% of total Step-2 damage / tick, 6 ticks, faction double-dips
  - Heat: 50% of total Step-2 damage / tick, 6 ticks, applies Heat type-effectiveness, faction double-dips
  - Gas: 0.5 × base × (1+damage_bonus) × (1+faction)² × crit × body_part — ignores elemental mods (**formula under review**)
  - Toxin: bypasses shields, deals Toxin damage directly to health
  - Electricity: chain-damage proc
  - Corrosive: strips armor stacks
- `loader.py` — `load_weapon()`, `load_mod()`, `load_enemy()` from JSON; case-insensitive; headshot support

**Bug fix:** Mod-sourced secondary elements (Magnetic, Blast, Corrosive, Gas, Radiation, Viral)
were previously silently dropped. Now collected as `mod_secondary` and passed through directly,
same treatment as innate secondary elements.

### Data (`data/`)
- `weapons.json` — 588 weapons (primary/secondary/melee) with IPS split, innate elements, crit/status/fire_rate/magazine/reload stats, image filename
- `mods.json` — 1534 mods with damage%, elemental%, cc/cd/sc/multishot bonuses, faction bonus
- `enemies.json` — 983 enemies from 11 faction lua files; faction, health_type, armor_type (inferred), base_armor, head_multiplier

### Web (`web/`)
- `api.py` — FastAPI REST: `GET /api/weapons`, `/api/mods`, `/api/enemies`; `POST /api/modded-weapon`, `/api/calculate`, `/api/optimal-order`
  - `/api/calculate` accepts: `weapon`, `mods[]`, `enemy`, `crit_mode`, `headshot`, `viral_stacks`, `corrosive_stacks`
  - `/api/calculate` returns: `breakdown`, `total`, `procs` (Slash/Heat/Gas/Toxin/Electricity), `fire_rate`, `magazine`, `reload`, `modded_sc`, `modded_ms`
  - `/api/mods` now returns per-mod: `primary_element`, `rarity`, `base_drain`, `max_rank`
  - `/api/optimal-order` — brute-forces all permutations of primary-elemental mods in the selected slots, returns `optimal_mods` (reordered list that maximises total damage vs the given enemy)
- `static/index.html` — current dark-theme SPA (being replaced — see Pending):
  - Weapon panel: image, crit/status/fire rate/magazine/reload/multishot, live modded values
  - 8-slot mod grid filtered by weapon type, live damage table
  - Enemy panel, Hit Options (crit mode, headshot, Viral/Corrosive stacks)
  - Results: per-type bar chart, Status Procs table, DPS section

### CLI
- `__main__.py` — `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" [--crit average|guaranteed|max] [--headshot]`
- `run_web.py` — `python run_web.py` starts dev server on port 8000

### Tests (120 passing)
- `tests/test_quantization.py` — quantizer edge cases
- `tests/test_combiner.py` — elemental combination + innate rules
- `tests/test_loader.py` — JSON → model loading
- `tests/test_calculator.py` — M7–M13: modded damage, body part, faction, armor, crit, Viral stacks, secondary elemental mods, status procs

## Pending

### ① UI Design Overhaul (branch: `claude/design-overhaul-bmwUa`)
Rewrite `web/static/index.html`. Target features:
- **Glassmorphism dark theme** — backdrop-blur panels, subtle gradient borders, Warframe gold accent
- **2×4 mod grid** — portrait mod cards with polarity icon, rarity colour strip, drag-to-reorder (SortableJS)
- **Mod picker popup** — click an empty card → searchable list filtered to weapon type, closes on outside click
- **Element mixer** — SVG arc overlay connecting paired elemental mods → combined element badge (Viral, Corrosive, etc.)
- **"Optimal Order" button** — calls `/api/optimal-order`, animates cards into the best permutation
- **Tippy.js tooltips** on stat labels (replaces the custom `#tt` div)
- All existing calculation features preserved: live modded stats, results breakdown, DPS, procs

### ② Replace Mad5cout Research Reference
User has a PDF with authoritative damage calculation docs to replace the
[Mad5cout community research](https://wiki.warframe.com/w/User_blog:Mad5cout/Warframe_Damage_Calculation_Research).
Share PDF path or paste text when at a desktop → update `CLAUDE.md` "Confirmed Order of Operations".

### ③ Verify Gas Proc Formula
Current:
```
Gas proc = 0.5 × base × (1+damage_bonus) × (1+faction)² × crit × body_part
```
Ignores elemental mods. Cross-check against PDF above before confirming.

### ④ Riven Mod Support
- UI: riven builder panel (select stat type + value per bonus)
- Backend: none needed — `Mod` dataclass already supports arbitrary bonuses

### ⑤ Enemy Data Gaps
- `health_type` / `armor_type` are faction-inferred defaults, not per-enemy.
  Corpus Amalgams, Liches, etc. may differ. A manual override table in `enemies.json` would fix edge cases.

## Branch
Active design overhaul: `claude/design-overhaul-bmwUa`
```bash
git push -u origin claude/design-overhaul-bmwUa
```
