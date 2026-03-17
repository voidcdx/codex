# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Warframe 100% Accurate Damage Calculator

## Project Goal
Create a Python-based damage calculator that accurately emulates in-game damage calculations per the official [Warframe Wiki — Damage/Calculation](https://wiki.warframe.com/w/Damage/Calculation), including full quantization to 1/32nd of base damage.

**Reference wiki:** https://wiki.warframe.com/w/Damage/Calculation (always prefer this over the Fandom mirror)

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
  combiner.py       # ElementalCombiner — mod-order-based element combination
  calculator.py     # DamageCalculator — full pipeline
tests/
  test_quantization.py
  test_combiner.py
  test_pipeline.py  # integration tests using wiki examples
memory-bank/        # detailed architectural notes
```

## Confirmed Order of Operations (from wiki research)
Per [Mad5cout's community research](https://wiki.warframe.com/w/User_blog:Mad5cout/Warframe_Damage_Calculation_Research):

```
1. Base Damage × (1 + ΣDamageMods)           → Modded Base Damage  [round DOWN]
2. Modded Base Damage × Body Part Multiplier  → Part Damage         [round to nearest]
3. Part Damage × (1 + FactionMod)             → Faction Damage      [round DOWN]
4. Faction Damage × DamageType Multiplier     → Typed Damage        [round DOWN]
5. Typed Damage × Armor Mitigation            → Final Damage        [round DOWN]
```

**Armor Mitigation** = `300 / (300 + effective_armor)`
**Faction/Damage mods** do NOT affect quantization scale — they are simple multipliers on already-quantized values.

## Quantization Rules (Damage 3.0)
Scale = `base_damage / 32`

For each damage type:
```python
quantized = round(raw_amount / scale) * scale
```
- Applied independently per damage type (Impact, Puncture, Slash, each elemental)
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
