# CLAUDE.md

# Warframe 100% Accurate Damage Calculator

## Project Goal
Create a Python-based damage calculator that accurately emulates in-game damage calculations, including full quantization (rounding to 1/32nd of base damage).

## Technical Stack
- **Language:** Python 3.11+
- **Testing:** `pytest`
- **Data Source:** Warframe Wiki (Damage/Calculation)

## Project Structure
- `/src`: Core logic (classes: Weapon, Mod, Enemy, Calculator)
- `/tests`: Unit tests reproducing Wiki examples
- `/memory-bank`: Detailed architectural documentation

## Coding Standards & Conventions
- **Accuracy First:** Always prioritize mathematical accuracy over speed.
- **Quantization:** Physical and Elemental damage must be rounded to the nearest multiple of 1/32nd of the base damage.
- **Rounding:** Use `round()` to the nearest whole number for intermediate steps.
- **Type Safety:** Use type hinting.

## How to Work on This Project
1.  **Read the Wiki:** When in doubt, search the Warframe Wiki for the latest damage calculation formulas.
2.  **Verify First:** Create a `pytest` case using a specific scenario (Weapon X + Mod Y) from the wiki *before* writing the logic.
3.  **Refactor:** Break down large calculations into smaller, testable functions (e.g., `calculate_crit`, `apply_armor`).

## Order of Operations (High Importance)
1. Modded Base Damage
2. Faction/Damage Type Multipliers
3. Armor Mitigation
4. Critical Hit Multiplier (Avg)

## Rules of Coding
1. Short answers only. Dont rewrite entire code just the parts that need rewriting. Ask questions. 
