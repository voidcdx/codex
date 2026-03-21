# Handoff — Warframe Damage Calculator

## Current Status
**128 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs + DPS.
Web UI fully functional with dark theme, mod card grid, special slots, weapon images, riven mod builder, and enemy level scaler.

---

## What's Done

### Core (`src/`)
- `enums.py` — DamageType, FactionType, HealthType, ArmorType
- `models.py` — Weapon, WeaponAttack, Mod, Enemy, DamageComponent dataclasses
- `quantizer.py` — `quantize()` with Decimal + ROUND_HALF_UP (never uses Python `round()`)
- `combiner.py` — elemental combination by mod slot order; innate primary/secondary split; Kuva/Tenet HCET priority
- `calculator.py` — full 6-step damage pipeline + `calculate_procs()` (Slash, Heat, Gas, Toxin, Electricity, Corrosive)
- `loader.py` — `load_weapon(name, attack_name=None)`, `load_mod()`, `load_enemy()`
- `scaling.py` — enemy level scaling (health/shield power law, armor cap, Overguard); full float64 precision coefficients reproduce wiki values exactly

### Data (`data/`)
- `weapons.json` — 588 weapons with `attacks[]` per weapon, per-attack damage/crit/status/shot_type, weapon images
- `mods.json` — 1534 mods — all stats audited; damage%, elemental%, cc/cd/sc/multishot, faction bonus
- `enemies.json` — 983 enemies — faction, health/armor type, base_armor, base_level, base_health, base_shield, head_multiplier

### Web (`web/`)
- `api.py` — FastAPI:
  - `GET /api/weapons` — all weapons with per-attack stats
  - `GET /api/mods` — all mods
  - `GET /api/enemies` — all enemies with base_level
  - `POST /api/modded-weapon` — modded weapon stats (no enemy)
  - `POST /api/calculate` — full damage calculation (accepts enemy_level, steel_path, eximus)
  - `POST /api/scaled-enemy` — scaled HP/shield/armor/overguard for given level
- `static/index.html` — dark SPA:
  - Weapon combobox with thumbnail images in dropdown; attack tab buttons for multi-attack weapons
  - 2×4 mod card grid with searchable mod picker popup; duplicate mod prevention
  - Element arcs — SVG lines connecting paired elemental mods → combined element badge
  - **Stance slot** (melee-only, gold shimmer) + **Exilus slot** (teal, all weapon types)
  - **Weapon-specific exilus mods** — Adhesive Blast, Cautious Shot, etc. appear only for eligible weapons
  - **Riven mod slot** — purple card, opens two-column stat builder modal; up to 4 stats (stat + % per row); `×` clears a row; % input enforces 4-char max via `oninput`
  - Enemy combobox with faction/type/armor display
  - **Enemy level scaler** — Level input (1–9999), Steel Path toggle (+100 level, ×2.5 HP/shield), Eximus toggle (shows Overguard)
  - Scaled enemy stats displayed with decimals (e.g. `4,502,520.4` HP, `825,903.86` OG)
  - Live stats panel: modded base damage, DPS (burst + sustained), crit stats, element badges
  - Damage breakdown table + status proc DPS

### CLI (`__main__.py`)
- `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner"`
- Flags: `--crit avg|guaranteed|max`, `--headshot`, `--attack "Name"`, `--viral N`, `--corrosive`, `--procs`
- Riven warning printed if a riven is loaded (data accuracy caveat)
- Headshot confirmation line printed when `--headshot` is passed

---

## Pending

### ① Authoritative Damage Docs
User has authoritative damage calculation docs (PDF). Share path → update `CLAUDE.md` "Confirmed Order of Operations".

### ② Enemy Data Gaps
`health_type` / `armor_type` are faction-inferred defaults, not per-enemy. Corpus Amalgams, Liches, etc. may differ. A manual override table in `enemies.json` would fix edge cases.

### ③ Helstrum / Tombfinger Missing
Both are absent from `weapons.json`. `WEAPON_SPECIFIC_EXILUS` in `index.html` already lists them — they'll work once the weapon entries are added.

### ④ Overguard Formula Needs Implementing
The correct formula (from wiki.warframe.com/w/Enemy_Level_Scaling) is a two-regime smoothstep: `f1 = 1 + 0.0015×δ^4` (δ<45), `f2 = 1 + 260×δ^0.9` (δ>50), smoothstep blend at δ=45–50. `src/scaling.py` still uses the old single power-law fit with wrong coefficients. See CLAUDE.md Overguard section for full formula and reference values.

---

## Key Architecture Notes
- **Crit stats are per-attack:** `Weapon.crit_chance`/`crit_multiplier` come from the selected attack.
- **`attacks[]` is source of truth:** Flat `base_damage`/`innate_elements` on `Weapon` are populated from the selected attack. `Weapon.attacks` holds all `WeaponAttack` objects.
- **IPS vs innate_elements:** In `weapons.json`, Impact/Puncture/Slash go in `base_damage`; elemental types go in `innate_elements`.
- **Exilus filtering:** `getExilusSet()` in `index.html` returns a weapon-type-appropriate Set, unioned with any `WEAPON_SPECIFIC_EXILUS` entries. Switching weapon auto-clears invalid exilus mods via `onWeaponChange()`.
- **Riven modal:** `rivenDraft[]` is a 4-element array (stat + pct per row). `buildRivenFromDraft()` converts it to a `Mod`-compatible riven object. Mod card shows active stat count. `%` input is `type="number"` — `maxlength` doesn't apply to number inputs, so 4-char cap is enforced with `oninput` slice.
- **Duplicate mod prevention:** `onModSelect()` checks if the chosen mod key is already present in any slot and aborts if so.
- **Scaling precision:** `scaling.py` uses full Python float64 literals for exponent coefficients — do not round them. Changing to 6-decimal truncations causes ~9 HP / ~2 OG drift vs wiki values.
- **Decimal display:** `refreshEnemyScaling()` in the UI uses `Number(v.toFixed(2)).toLocaleString(undefined, {maximumFractionDigits:2})` so integer values show without `.00` and fractional values show up to 2 decimal places.
