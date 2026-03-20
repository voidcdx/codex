# Handoff — Warframe Damage Calculator

## Current Status
All core backend complete and tested (**122 tests passing**).
Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs + DPS.
Multi-attack support: weapons with multiple attack modes (Acceltra Prime, Torid, etc.) are fully supported.
Web UI functional. **Design overhaul in progress on `claude/design-overhaul-bmwUa`.**

## What's Done

### Core (`src/`)
- `enums.py` — DamageType, FactionType, HealthType, ArmorType
- `models.py` — Weapon, WeaponAttack, Mod, Enemy, DamageComponent dataclasses
  - `WeaponAttack`: name, base_damage, innate_elements, crit_chance, crit_multiplier, status_chance, shot_type, fire_rate
  - `Weapon`: base_damage + innate_elements (from selected attack), attacks[] (all), crit_chance/crit_multiplier/status_chance
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
  - Gas: 0.5 × base × (1+damage_bonus) × (1+faction)² × crit × body_part — ignores elemental mods
  - Toxin: bypasses shields, deals Toxin damage directly to health
  - Electricity: chain-damage proc
  - Corrosive: strips armor stacks
- `loader.py` — `load_weapon(name, attack_name=None)`, `load_mod()`, `load_enemy()` from JSON; case-insensitive; headshot + attack selection

### Multi-Attack System (new)
`weapons.json` stores an `attacks[]` array per weapon instead of flat `base_damage`/`innate_elements`. Each attack has:
- `name` (e.g. "Rocket Impact", "Rocket Explosion", "Incarnon Form")
- `base_damage` dict (IPS keys)
- `innate_elements` dict (elemental keys)
- `crit_chance`, `crit_multiplier`, `status_chance`, `fire_rate`, `shot_type`

`load_weapon()` accepts optional `attack_name` parameter. Defaults to first attack. Selected attack's stats populate `Weapon.base_damage`/`innate_elements`/`crit_chance`/`crit_multiplier`/`status_chance`. All attacks available via `Weapon.attacks` for UI enumeration.

`parse_wiki_data.py` extracts all attacks via `_parse_attack()` helper. Weapon-level crit/status/fire_rate are promoted from first attack for convenience.

### Data (`data/`)
- `weapons.json` — 588 weapons with `attacks[]` array, per-attack damage/crit/status/shot_type, weapon-level magazine/reload/disposition/image
- `mods.json` — 1534 mods with damage%, elemental%, cc/cd/sc/multishot bonuses, faction bonus
- `enemies.json` — 983 enemies from 11 faction lua files; faction, health_type, armor_type (inferred), base_armor, head_multiplier

### Web (`web/`)
- `api.py` — FastAPI REST endpoints:
  - `GET /api/weapons` — returns per-weapon `attacks[]` with per-attack base_damage/crit/status/shot_type. Top-level `base_damage` shows first attack only.
  - `GET /api/mods` — per-mod: primary_element, rarity, base_drain, max_rank
  - `GET /api/enemies` — faction, health/armor type, base_armor, head_multiplier
  - `POST /api/modded-weapon` — accepts optional `attack` field
  - `POST /api/calculate` — accepts optional `attack` field; returns breakdown, total, procs, fire_rate, magazine, reload, modded_sc, modded_ms
  - `POST /api/optimal-order` — accepts optional `attack` field; brute-forces elemental mod permutations
- `static/index.html` — dark-theme SPA (design overhaul in progress)

### CLI
- `__main__.py` — `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" [--crit average|guaranteed|max] [--headshot] [--attack "Name"]`
  - `--attack` must come before or after all positional args (argparse `nargs="*"` limitation)
  - Crit stats now read from `Weapon.crit_chance`/`crit_multiplier` directly (no more raw JSON lookups)
- `run_web.py` — `python run_web.py` starts dev server on port 8000

### Tests (122 passing)
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
- **Attack selector dropdown** — when weapon has >1 attack, show a dropdown to pick attack mode. Update all stats/damage on change.
- **Element mixer** — SVG arc overlay connecting paired elemental mods → combined element badge
- **"Optimal Order" button** — calls `/api/optimal-order`, animates cards into the best permutation
- **Tippy.js tooltips** on stat labels
- All existing calculation features preserved

### ② Replace Mad5cout Research Reference
User has a PDF with authoritative damage calculation docs to replace the
[Mad5cout community research](https://wiki.warframe.com/w/User_blog:Mad5cout/Warframe_Damage_Calculation_Research).
Share PDF path or paste text when at a desktop → update `CLAUDE.md` "Confirmed Order of Operations".

### ③ Riven Mod Support
- UI: riven builder panel (select stat type + value per bonus)
- Backend: none needed — `Mod` dataclass already supports arbitrary bonuses

### ④ Enemy Data Gaps
- `health_type` / `armor_type` are faction-inferred defaults, not per-enemy.
  Corpus Amalgams, Liches, etc. may differ. A manual override table in `enemies.json` would fix edge cases.

### ⑤ Multi-Attack UI Integration
- Web frontend needs an attack selector when weapon has multiple attacks
- Per-attack stats (crit/status/fire_rate) should update live when attack changes
- Consider showing all attacks side-by-side for comparison

## Key Architecture Notes
- **Crit stats are per-attack:** `Weapon.crit_chance` and `crit_multiplier` come from the selected attack, not a weapon-level default. All code (CLI, API, calculator) now reads these from the Weapon object directly instead of raw JSON lookups.
- **`attacks[]` is the source of truth:** The flat `base_damage`/`innate_elements` on `Weapon` are populated from the selected attack. `Weapon.attacks` holds all parsed `WeaponAttack` objects for enumeration.
- **Legacy fallback:** `load_weapon()` still handles weapons without `attacks[]` (reads flat `base_damage`/`innate_elements`), but `weapons.json` has been fully regenerated with the new schema.
- **IPS vs innate_elements distinction:** In `weapons.json`, IPS damage types (impact/puncture/slash) go in `base_damage`, elemental types go in `innate_elements`. The combiner treats them differently (innate elements participate in elemental combination).
