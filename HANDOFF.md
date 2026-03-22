# Handoff — Warframe Damage Calculator

## Current Status
**164 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS.
Web UI fully functional: dark theme, mod card grid, special slots, weapon images, riven mod builder, enemy level scaler, alchemy mixer.

## Branch
`claude/continue-handoff-HHzvE` — push all work here.

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

### 1. Update 36 Tooltip Fixes
All elemental damage tooltips in `const TOOLTIPS` (~line 200) updated. Ferrite Armor / Alloy Armor references removed — now show faction names matching `FACTION_EFFECTIVENESS`. Affected: `puncture`, `slash`, `heat`, `cold`, `electricity`, `toxin`, `blast`, `corrosive`, `gas`, `magnetic`, `radiation`.

### 2. Orokin SVG Icon (riven button)
Replaced simple vial path with an Orokin transmutation seal: boxy octagonal frame, dark fill `#1a1208`, gold `#D4A843` stroke, alchemical triangle+crossbar center glyph, 4 cardinal bubble circles, inner ring. `viewBox="0 0 24 24"`, 20px rendered.

### 3. Alchemy Mixer Modal
New feature: click the gold seal in the mod panel heading → modal opens. Pick two primary elements → orbs swirl (CSS animation) → merge/flash → shows combined element + mod suggestions for current weapon.

**Button layout:** `span.mod-panel-actions` (flex, gap 10px) wraps:
- `btn-alchemy-mixer` (gold, left) → `openAlchemyMixer()`
- `btn-add-riven` (purple `+`, right) → `openRivenBuilder()`

**JS functions added** (near line ~1490):
- `openAlchemyMixer()` / `closeAlchemyMixer()`
- `renderAlchPicker()` — 4 element buttons using `ALCH_PRIMARY` array
- `selectAlchElem(elem)` — toggle, max 2; clears timer on change
- `updateAlchStage()` — sets orb colors, starts swirl, schedules merge
- `triggerAlchMerge(a, b)` — removes swirl, adds merging, fires flash + result after 480ms
- `showAlchModSuggestions(a, b)` — filters `allMods` by `getCompatibleModTypes(getCurrentWeapon()).has(m.type)`

**CSS added** (end of style.css):
- `.alchemy-modal`, `.alchemy-element-picker`, `.alchemy-elem-btn`
- `.alchemy-stage`, `.alchemy-orb`, `.alchemy-orb-left/right`
- Keyframes: `alch-swirl-left/right`, `alch-merge-left/right`, `alch-flash-pop`
- `.alchemy-result`, `.alchemy-mods`, `.alchemy-mod-chip`

## Critical Naming Trap
`PRIMARY_ELEMENTS` is **already declared** as a `const Set` at line ~566 (used by the element combiner UI). The alchemy mixer uses `ALCH_PRIMARY` (array). **Never rename it to `PRIMARY_ELEMENTS`** — the duplicate `const` causes a `SyntaxError` that silently kills all JavaScript on the page (breaks weapon/enemy search, stats, everything).

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
- Alchemy mixer polish: larger stage, "equip these mods" button, show innate weapon elements pre-selected
- UI improvements: more weapon/mod filters, comparison mode
- Additional damage mechanics: Condition Overload multi-proc stacking improvements
