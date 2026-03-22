# Handoff — Warframe Damage Calculator

## Current Status
**164 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS.
Web UI fully functional: dark theme, mod card grid, special slots, weapon images, riven mod builder, enemy level scaler, alchemy mixer.

## Branch
`claude/continue-handoff-rKTj3` — push all work here.

## Architecture
```
src/
  enums.py        — DamageType, FactionType, HealthType, ArmorType
  models.py       — Weapon, WeaponAttack, Mod, Enemy, DamageComponent dataclasses
  quantizer.py    — quantize() pure function
  combiner.py     — elemental combination by mod slot order
  calculator.py   — 6-step pipeline + crit + armor + faction + Viral + calculate_procs()
  scaling.py      — enemy level scaling (health/shield/armor/overguard)
  loader.py       — load_weapon/mod/enemy from JSON
web/
  api.py          — FastAPI endpoints
  static/index.html  — SPA (all UI + JS)
  static/style.css   — dark theme
data/
  weapons.json    — 588 weapons (multi-attack)
  mods.json       — 1534 mods
  enemies.json    — 983 enemies
```

## What Was Done Last Session (2026-03-22)

### 1. Viral CC Proc Label / Effect Text
Renamed the Viral proc label from `"Viral (Health)"` → `"Viral Health Vulnr."` across all three surfaces:
- `src/calculator.py` (~line 478): effect string `"Health Vulnr. ×1.75–×4.25"` (removed dev-note `(use viral_stacks param)`)
- `__main__.py` (~line 140): `_CC_LABELS["viral"]`
- `web/static/index.html` (~line 1859): `CC_PROC_LABELS.viral`

### 2. Combo Counter Hidden for Non-Melee Weapons
Combo counter is a melee-only mechanic. The input was always visible and its value was sent to the backend for any weapon type. Fixed in `onWeaponChange()` (`index.html` ~line 772):
- Added `id="combo-div"` to the container div (line 143)
- `isMeleeWeapon()` (already existed, ~line 1428) now controls `comboDiv.style.display`
- Resets to tier 1 when switching to a non-melee weapon (ensures `combo_counter: 0` in POST body)

### 3. Combo Counter Max Clamped via oninput
The `max` attribute only controls spinner arrows — manual keyboard entry could exceed 12/13. Added `oninput` handler to the input (line 145):
```
oninput="if(+this.value>+this.max)this.value=this.max;if(+this.value<1)this.value=1"
```
Uses `+this.max` so it automatically respects the dynamic 12 (default) / 13 (Venka Prime) cap set by `onWeaponChange()`.

## Critical Naming Trap
`PRIMARY_ELEMENTS` is **already declared** as a `const Set` at line ~566 (used by the element combiner UI). The alchemy mixer uses `ALCH_PRIMARY` (array). **Never rename it to `PRIMARY_ELEMENTS`** — the duplicate `const` causes a `SyntaxError` that silently kills all JavaScript on the page.

## Other Critical Rules
- `getCompatibleModTypes(weapon)` takes a weapon object, returns a `Set` — use `.has()` not `.includes()`
- `getCurrentWeapon()` returns the currently selected weapon object
- NEVER use `round()` — always use `warframe_round` (Decimal + ROUND_HALF_UP)
- `armor_type` field is inert post-Update 36; don't add armor-type logic
- All damage type effectiveness is faction-based (see `FACTION_EFFECTIVENESS` in calculator.py and index.html)

## Running the App
```bash
pip install fastapi uvicorn
python run_web.py        # http://localhost:8000
pytest                   # 164 tests, all pass
```

## Possible Next Tasks
- UI improvements: weapon/mod comparison mode, filter by slot/class
- Additional damage mechanics: kuva/tenet weapon bonuses, galvanized mods
- More body part data for enemies (currently only head multiplier stored)
- CLI: `--list-attacks WEAPON` flag to enumerate attack modes
