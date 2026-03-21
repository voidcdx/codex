# Handoff — Warframe Damage Calculator

## Current Status
**128 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs + DPS.
Web UI fully functional with dark theme, mod card grid, special slots, and weapon images.

---

## What's Done

### Core (`src/`)
- `enums.py` — DamageType, FactionType, HealthType, ArmorType
- `models.py` — Weapon, WeaponAttack, Mod, Enemy, DamageComponent dataclasses
- `quantizer.py` — `quantize()` with Decimal + ROUND_HALF_UP (never uses Python `round()`)
- `combiner.py` — elemental combination by mod slot order; innate primary/secondary split; Kuva/Tenet HCET priority
- `calculator.py` — full 6-step damage pipeline + `calculate_procs()` (Slash, Heat, Gas, Toxin, Electricity, Corrosive)
- `loader.py` — `load_weapon(name, attack_name=None)`, `load_mod()`, `load_enemy()`

### Data (`data/`)
- `weapons.json` — 588 weapons with `attacks[]` per weapon, per-attack damage/crit/status/shot_type, weapon images
- `mods.json` — 1534 mods — all stats audited; damage%, elemental%, cc/cd/sc/multishot, faction bonus
- `enemies.json` — 983 enemies — faction, health/armor type, base_armor, head_multiplier

### Web (`web/`)
- `api.py` — FastAPI: GET /api/weapons|mods|enemies; POST /api/modded-weapon, /api/calculate, /api/optimal-order
- `static/index.html` — dark SPA:
  - Weapon picker with image + attack tab buttons (multi-attack weapons show per-attack stats)
  - 2×4 mod card grid with searchable mod picker popup
  - Element arcs — SVG lines connecting paired elemental mods → combined element badge
  - **Stance slot** (melee-only, gold shimmer) + **Exilus slot** (teal, all weapon types)
  - **Weapon-specific exilus mods** — Adhesive Blast, Cautious Shot, Directed Convergence, Fomorian Accelerant, Kinetic Ricochet, Tether Grenades appear only when their eligible weapon is selected
  - Riven mod slot (purple card, custom stat builder modal)
  - Enemy picker with faction/type display
  - Live stats panel: modded base damage, DPS (burst + sustained), crit stats, element badges
  - Damage breakdown table + status proc DPS
  - Optimal Mod Order button

### CLI
- `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner" [--crit avg|guaranteed|max] [--headshot] [--attack "Name"]`

---

## Pending

### ① Chat Interface (next session)
Add an AI chat panel to the web UI. See CLAUDE.md § Chat Interface for full spec.

### ② Replace Mad5cout Research Reference
User has authoritative damage calculation docs (PDF). Share path → update `CLAUDE.md` "Confirmed Order of Operations".

### ③ Enemy Data Gaps
`health_type` / `armor_type` are faction-inferred defaults, not per-enemy. Corpus Amalgams, Liches, etc. may differ. A manual override table in `enemies.json` would fix edge cases.

### ④ Helstrum / Tombfinger Missing from weapons.json
Both are not present in the current data. `WEAPON_SPECIFIC_EXILUS` in `index.html` already lists them for Adhesive Blast / Cautious Shot — they'll activate automatically once the weapons are added to weapons.json.

---

## Key Architecture Notes
- **Crit stats are per-attack:** `Weapon.crit_chance`/`crit_multiplier` come from the selected attack, not weapon-level.
- **`attacks[]` is the source of truth:** Flat `base_damage`/`innate_elements` on `Weapon` are populated from the selected attack. `Weapon.attacks` holds all `WeaponAttack` objects.
- **IPS vs innate_elements:** In `weapons.json`, Impact/Puncture/Slash go in `base_damage`; elemental types go in `innate_elements`. Combiner treats them differently.
- **Exilus filtering:** `getExilusSet()` in `index.html` returns a weapon-type-appropriate Set, then unions in any `WEAPON_SPECIFIC_EXILUS` entries matching the current weapon name. Switching weapon auto-clears invalid exilus mods via `onWeaponChange()`.
