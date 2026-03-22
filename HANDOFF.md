# Handoff — Warframe Damage Calculator

## Current Status
**164 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS.
Web UI fully functional with dark theme, mod card grid, special slots, weapon images, riven mod builder, enemy level scaler.

---

## What's Done

### Core (`src/`)
- `enums.py` — DamageType, FactionType, HealthType, ArmorType
- `models.py` — Weapon, WeaponAttack, Mod, Enemy, DamageComponent dataclasses
- `quantizer.py` — `quantize()` with Decimal + ROUND_HALF_UP (never uses Python `round()`)
- `combiner.py` — elemental combination by mod slot order; innate primary/secondary split; Kuva/Tenet HCET priority
- `calculator.py` — full 6-step damage pipeline + `calculate_procs()` for all 10 proc types (5 DoT + 5 CC/debuff)
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
  - `POST /api/calculate` — full damage calculation (accepts enemy_level, steel_path, eximus, viral_stacks, corrosive_stacks)
  - `POST /api/scaled-enemy` — scaled HP/shield/armor/overguard for given level
- `static/index.html` — dark SPA:
  - Weapon combobox with thumbnail images in dropdown; attack tab buttons for multi-attack weapons
  - 2×4 mod card grid with searchable mod picker popup; duplicate mod prevention
  - Element arcs — SVG lines connecting paired elemental mods → combined element badge
  - **Stance slot** (melee-only, gold shimmer) + **Exilus slot** (teal, all weapon types)
  - **Weapon-specific exilus mods** — Adhesive Blast, Cautious Shot, etc. appear only for eligible weapons
  - **Riven mod slot** — purple card, opens two-column stat builder modal; up to 4 stats; `×` clears a row; % input enforces 4-char max via `oninput`
  - Enemy combobox with faction/type display
  - **Enemy level scaler** — Level input (1–9999), Steel Path toggle (×2.5 HP/shield), Eximus toggle (shows Overguard)
  - Live stats panel: modded base damage, DPS (burst + sustained), crit stats, element badges
  - Damage breakdown table with per-hit and per-trigger columns + faction effectiveness badges
  - **Status Procs** table — DoT procs (per-tick / total). Separate **CC / Debuff Procs** table (effect text, no damage columns). DPS loop skips CC entries.

### CLI (`__main__.py`)
- `python -m dc "Soma Prime" "Serration" vs "Heavy Gunner"`
- Flags: `--crit avg|guaranteed|max`, `--headshot`, `--attack "Name"`, `--viral N`, `--corrosive`, `--procs`
- `--procs` now shows two tables: DoT procs (per-tick / total) + CC/debuff procs (effect text)

---

## Recent Changes (this session)

### Multishot Fix
- `DamageCalculator.calculate()` now accepts `multishot: float` param
- Per-hit damage is multiplied by multishot count inside the pipeline
- `api.py` computes `modded_ms` from mods and passes it through
- `index.html` shows "Per-trigger damage (includes ×N multishot)" note when MS > 1
- `breakdown_per_trigger` and `total_per_trigger` added to API response

### CC / Debuff Status Procs
Added 5 non-DoT procs to `calculate_procs()` in `src/calculator.py`:

| Proc | Effect |
|---|---|
| `viral` | Health ×1.75–×4.25 (already modeled via viral_stacks in main pipeline) |
| `magnetic` | +100% shield/OG dmg; forced Elec proc on shield break |
| `radiation` | Confuses enemy to attack allies for 12s |
| `blast` | −30% accuracy (up to −75%); detonates at 10 stacks |
| `cold` | −50% speed (up to −90%); +0.1 flat crit damage |

These return `{active, effect, damage_per_tick:0, ticks:0, total_damage:0}`. A `_cc_proc()` helper was added alongside the existing `_proc()`.

**Web UI:** A second "CC / Debuff Procs" table renders below the DoT table when any CC procs are active. The DPS proc loop skips them (`k in PROC_LABELS` guard added). `CC_PROC_LABELS` and `CC_PROC_COLORS` constants added (colors sourced from existing `ELEM_COLORS`).

**CLI:** `--procs` flag now renders two separate sections.

**Tests:** `TestCCProcs` class added (7 tests) — active/inactive per type + zero-damage assertion.

---

## Known Issue / Not Yet Verified

The CC procs table in the web UI renders correctly in code (HTML inserted at line 1751 inside `displayResults()`), but **was not visually confirmed in browser** before session ended. If it's not showing:
1. Open browser console — check for JS errors in `displayResults()`
2. Inspect the raw `/api/calculate` response — confirm `procs.viral`, `procs.cold`, etc. are present with `active: true`
3. The guard is `p.active && k in CC_PROC_LABELS` — if `data.procs` keys don't match, the filter silently skips them

---

## Pending

### Shield HP Layer (Corpus)
Model Corpus enemy shields as a separate HP layer in `DamageCalculator.calculate()`:
- Shield gate: damage hits shields first; excess carries over to health
- Magnetic amplifier: ×2.0 damage to shields when shields are up
- API: `/api/calculate` request needs `target_layer: "shield"|"health"` or the calculator returns both layers

### Melee Combo Counter
- `Weapon.combo_counter: int` field (default 0)
- Combo multiplier: `1.0 + 0.5 × floor(counter / 5)` (unmodded)
- CLI: `--combo N` flag

### Condition Overload
- Melee mod: `+60%` damage per unique active status on enemy, max 6 stacks (+360%)
- Requires tracking which status types are currently active on the enemy
- Applied in Step 1 alongside other damage mods

### Arcane Framework
- Weapon arcanes (Arcane Acceleration, Arcane Velocity, etc.) and Warframe arcanes affecting damage
- Add `arcanes: list[Arcane]` to request body; apply bonuses in Step 1 / as flat multipliers

### TAU Damage Effectiveness Table
- Void, Tau damage types have their own effectiveness vs Sentient/Murmur (Zariman-era)
- Add to `FACTION_EFFECTIVENESS` in `src/calculator.py` and mirror in `index.html`

---

## Key Architecture Notes
- **Crit stats are per-attack:** `Weapon.crit_chance`/`crit_multiplier` come from the selected attack.
- **`attacks[]` is source of truth:** Flat `base_damage`/`innate_elements` on `Weapon` are populated from the selected attack. `Weapon.attacks` holds all `WeaponAttack` objects.
- **IPS vs innate_elements:** In `weapons.json`, Impact/Puncture/Slash go in `base_damage`; elemental types go in `innate_elements`.
- **Exilus filtering:** `getExilusSet()` in `index.html` returns a weapon-type-appropriate Set, unioned with any `WEAPON_SPECIFIC_EXILUS` entries. Switching weapon auto-clears invalid exilus mods via `onWeaponChange()`.
- **Riven modal:** `rivenDraft[]` is a 4-element array. `buildRivenFromDraft()` converts it to a `Mod`-compatible riven object. `%` input is `type="number"` — `maxlength` doesn't apply to number inputs, so 4-char cap enforced with `oninput` slice.
- **Duplicate mod prevention:** `onModSelect()` checks if chosen mod key is already in any slot and aborts if so.
- **Scaling precision:** `scaling.py` uses full Python float64 literals for exponent coefficients — do not round them. 6-decimal truncation causes ~9 HP / ~2 OG drift vs wiki values.
- **Decimal display:** `refreshEnemyScaling()` uses `Number(v.toFixed(2)).toLocaleString(...)` so integers show without `.00`.
- **CC proc DPS guard:** In `index.html` DPS loop, `k in PROC_LABELS` guard must stay — CC procs have `damage_per_tick: 0` and must not pollute the proc DPS total.
