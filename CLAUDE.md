# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Warframe 100% Accurate Damage Calculator

## Project Goal
Create a Python-based damage calculator that accurately emulates in-game damage calculations per the official [Warframe Wiki — Damage/Calculation](https://wiki.warframe.com/w/Damage/Calculation), including full quantization to 1/32nd of base damage.

**Reference wiki:** https://wiki.warframe.com/w/Damage/Calculation

**NEVER use the Fandom wiki (warframe.fandom.com) — it is no longer updated. Always use the official wiki at wiki.warframe.com.**

## Technical Stack
- **Language:** Python 3.11+
- **Testing:** `pytest`
- **Data Source:** Warframe Wiki (official: wiki.warframe.com)

## Commands
```bash
pip install pytest
pytest                              # run all tests
pytest tests/test_quantization.py  # run single file
pytest -k "test_viral_combo"        # run single test by name
```

## Project Structure
```
src/
  enums.py          # DamageType, FactionType, HealthType, ArmorType
  models.py         # Weapon, Mod, Enemy dataclasses
  quantizer.py      # quantize() — pure function, no side effects
  combiner.py       # elemental combination by mod slot order; innate primary/secondary split
  calculator.py     # DamageCalculator — 6-step pipeline + crit + armor + faction + Viral stacks + calculate_procs()
  loader.py         # load_weapon/mod/enemy from JSON; case-insensitive; headshot support
tests/
  test_quantization.py
  test_combiner.py
  test_loader.py
  test_calculator.py  # M7–M13: modded damage, body part, faction, armor, crit, Viral stacks, secondary elemental mods, status procs
data/
  weapons.json      # 588 weapons (primary/secondary/melee) — IPS, innate elements, stats, image
  mods.json         # 1534 mods — damage%, elemental%, cc/cd/sc/multishot, faction bonus
  enemies.json      # 983 enemies — faction, health_type, armor_type, base_armor, head_multiplier
scripts/
  parse_lua.py      # parses raw .lua module files downloaded from wiki
  parse_wiki_data.py # normalizes raw JSON → calculator-ready weapons.json/mods.json
  fetch_wiki_data.py # (attempted) automated fetch — wiki blocks it, use browser instead
  extract_data.lua  # Lua extraction script / wiki ApiSandbox one-liners
web/
  api.py            # FastAPI: GET /api/weapons|mods|enemies; POST /api/modded-weapon, /api/calculate, /api/optimal-order
  static/index.html # SPA: weapon/mod/enemy selects, live stats, Viral stacks input (design overhaul in progress)
run_web.py          # python run_web.py → dev server on port 8000
__main__.py         # python -m dc "Weapon" "Mod" vs "Enemy" [--crit avg|guaranteed|max] [--headshot]
```

## 120 Tests Passing
`pytest` — all pass. Run before committing.

## Confirmed Order of Operations (from wiki research)
Per [Mad5cout's community research](https://wiki.warframe.com/w/User_blog:Mad5cout/Warframe_Damage_Calculation_Research):

```
1. Base Damage × (1 + ΣDamageMods)           → Modded Base Damage  [round DOWN]
2. Modded Base Damage × Body Part Multiplier  → Part Damage         [round to nearest]
3. Part Damage × DamageType Multiplier        → Typed Damage        [round DOWN]
4. Typed Damage × Armor Mitigation            → Mitigated Damage    [round DOWN]
5. Mitigated Damage × (1 + FactionMod)        → Final Damage        [round DOWN]
6. Final Damage × Viral stack multiplier      → Viral Damage        [round DOWN]
```

**Viral stack multipliers** (0 stacks = ×1.0, max 10 stacks = ×4.25):
`{1:1.75, 2:2.0, 3:2.25, 4:2.5, 5:2.75, 6:3.0, 7:3.25, 8:3.5, 9:3.75, 10:4.25}`

**Armor Mitigation** = `300 / (300 + effective_armor)`
**Faction mods apply LAST** — multiplicative `(1 + bonus)` after armor mitigation.
**Faction/Damage mods** do NOT affect quantization scale — they are simple multipliers on already-quantized values.

## Critical Hit Rules
- **Tier Scaling:** `M_crit = 1 + T × (CD − 1)` where T = `floor(total_crit_chance)`
- **Average Multiplier:** Use `1 + CC × (CD − 1)` for DPS calculations (exact for all tiers).
- **Headshot:** Normal headshot = ×2 body part multiplier (Step 2).
- **Crit on Headshot:** If the hit is also a critical, the crit multiplier is **doubled**: `M_crit_headshot = 1 + T × (CD − 1) × 2`. Apply after Step 2, before Step 3.

## Faction Mod Rules
- **Placement:** Faction mods (Bane of X) apply **at the very end** — Step 5, after armor mitigation.
- **Formula:** `Final Damage × (1 + faction_bonus)`
- **Double-Dipping (Status Procs):** For damage-over-time procs triggered by the hit (Slash bleed, Gas cloud, Heat burn), the faction bonus applies **twice**: `proc_damage × (1 + faction_bonus)²`. This is because the proc inherits the faction bonus from the hit that triggered it, then applies it again when the proc ticks.

## Quantization Rules (Damage 3.0)
Scale = `base_damage / 32`

For each damage type:
```python
from decimal import Decimal, ROUND_HALF_UP

def warframe_round(x: Decimal) -> Decimal:
    """NEVER use Python's built-in round() — it uses Banker's Rounding (round-half-to-even),
    which produces wrong results on exact .5 boundaries. Always use this instead."""
    return x.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

quantized = warframe_round(Decimal(str(raw_amount)) / Decimal(str(scale))) * Decimal(str(scale))
```
- **NEVER use Python's `round()` built-in** — use `warframe_round` (Decimal + ROUND_HALF_UP) everywhere
- **Use `Decimal` for all intermediate steps** to prevent floating-point drift
- Applied **independently per damage type** (Impact, Puncture, Slash, each elemental)
- Applied **before** faction/damage multipliers
- Combined elements (e.g. Viral from Cold+Toxin) quantize their **combined total** at 1/32 of base

## Elemental Combination
**Primary elements:** Heat, Cold, Electricity, Toxin
**Combination priority:** mod placement order, top-left first. Innate weapon elements come last.
Exception: Kuva/Tenet innate elements follow HCET priority (Heat > Cold > Electricity > Toxin).

| Combined Element | Recipe              |
|-----------------|---------------------|
| Blast           | Heat + Cold         |
| Corrosive       | Electricity + Toxin |
| Gas             | Heat + Toxin        |
| Magnetic        | Cold + Electricity  |
| Radiation       | Heat + Electricity  |
| Viral           | Cold + Toxin        |

### Innate Element Placement Rules
- **Primary innate elements** (e.g. Heat on Ignis) occupy **"Slot 9"** — after all mod slots — unless a mod of the same element is equipped. If a mod of the same element is present, the innate amount merges into that mod's slot position (first occurrence wins queue order).
- **Secondary (combined) innate elements** (e.g. Magnetic on Kuva Nukor) are a fixed bucket — they cannot be uncombined or combined further with anything else. They are passed through directly to the damage output.
- **Quantization order:** Combine raw bonus percentages first → calculate raw damage → then apply `quantize_damage()` to the final combined total. Never quantize individual primaries before combining.

## Enemy Armor (Post-June 2024)
- **Hard Cap:** Enemy armor is hard-capped at 2,700 (90% DR).
- **Armor Scaling:** `DR = Armor / (Armor + 300)`
- **Type Modifiers:** A damage type bonus against armor (e.g. Corrosive vs. Ferrite) does two things:
  1. Increases base damage by that percentage.
  2. Ignores that percentage of the armor value: `effective_armor = Armor × (1 − Modifier)`.

## Damage Type Effectiveness (Update 36.0+)
- **Vulnerable (+):** ×1.5
- **Resistant (−):** ×0.5

## Coding Standards
- **Accuracy first:** Mathematical correctness over speed or brevity.
- **Test before implement:** Write the `pytest` case from a wiki example, then write logic until it passes.
- **Pure functions:** `quantize()`, `combine()` must have no side effects.
- **Type hints** on all function signatures.

## Rules
- Short answers only. Don't rewrite entire files — only the parts that need changing. Ask questions when uncertain.

## Critical Implementation Rules
- **Rounding:** NEVER use the built-in `round()` function. All rounding must use the `warframe_round` utility (Decimal + ROUND_HALF_UP) to prevent Banker's Rounding errors.
- **Quantization:** Apply quantization (scale of 1/32) to each damage type (Impact, Puncture, Slash, Elementals) individually before summing.
- **Precision:** Use `Decimal` or high-precision floats for intermediate steps to avoid floating-point drift.
