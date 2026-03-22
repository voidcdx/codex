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
  models.py         # Weapon, WeaponAttack, Mod, Enemy, DamageComponent dataclasses
  quantizer.py      # quantize() — pure function, no side effects
  combiner.py       # elemental combination by mod slot order; innate primary/secondary split
  calculator.py     # DamageCalculator — 6-step pipeline + crit + armor + faction + Viral stacks + calculate_procs()
  loader.py         # load_weapon/mod/enemy from JSON; case-insensitive; headshot + attack selection
tests/
  test_quantization.py
  test_combiner.py
  test_loader.py
  test_calculator.py  # M7–M13: modded damage, body part, faction, armor, crit, Viral stacks, secondary elemental mods, status procs
data/
  weapons.json      # 588 weapons — multi-attack (attacks[]), per-attack IPS/innate/crit/status/shot_type, image
  mods.json         # 1534 mods — damage%, elemental%, cc/cd/sc/multishot, faction bonus
  enemies.json      # 983 enemies — faction, health_type, armor_type, base_armor, head_multiplier
scripts/
  parse_lua.py      # parses raw .lua module files downloaded from wiki
  parse_wiki_data.py # normalizes raw JSON → calculator-ready weapons.json/mods.json (multi-attack aware)
  fetch_wiki_data.py # (attempted) automated fetch — wiki blocks it, use browser instead
  extract_data.lua  # Lua extraction script / wiki ApiSandbox one-liners
web/
  api.py            # FastAPI: GET /api/weapons|mods|enemies; POST /api/modded-weapon, /api/calculate
  static/index.html # SPA: weapon/mod/enemy selects, mod card grid, stance/exilus slots, live stats, Viral stacks input
  static/style.css  # dark theme; .eff-badge/.eff-vuln/.eff-res for faction effectiveness badges in results table
run_web.py          # python run_web.py → dev server on port 8000
__main__.py         # python -m dc "Weapon" "Mod" vs "Enemy" [--crit avg|guaranteed|max] [--headshot] [--attack "Name"]
```

## 154 Tests Passing
`pytest` — all pass. Run before committing.

## Web UI Notes

### Faction Effectiveness Badges
Results breakdown table shows `+50%` (green) or `−50%` (red) badges next to damage types based on the selected enemy's faction. Driven by `FACTION_EFFECTIVENESS` JS constant in `index.html` (mirrors `src/calculator.py`). CSS: `.eff-badge`, `.eff-vuln`, `.eff-res` in `style.css`.

### Weapon Picker Filtering
Exalted weapons (`class === 'Exalted Weapon'`) and Garuda Talons are hidden from the weapon search combobox via `visibleWeapons` filter in `loadData()`. `allWeapons` retains full data.

### Mod Slot Compatibility
`onWeaponChange()` clears any mod slots whose `mod.type` is not in `getCompatibleModTypes()` for the new weapon. Mod picker always enforces type compatibility — no fallback to showing all mods.

## Riven Mod Builder (Web UI)
- **Slot:** Purple card in the mod grid. Clicking opens a two-column modal.
- **Modal state:** `rivenDraft[]` — 4 rows, each `{stat, pct}`. Rendered by `renderRivenModal()`.
- **Stat select:** Populated from `RIVEN_STATS` constant. Empty option = "no stat" (row inactive).
- **% input:** `type="number"`, range `min="-999" max="9999"`. `maxlength` doesn't work on number inputs — 4-char cap enforced via `oninput` slice: `if(this.value.length>4)this.value=this.value.slice(0,4)`.
- **Clear row:** `×` button calls `clearRivenRow(i)` → sets row to `{stat:'', pct:''}`.
- **Apply:** `buildRivenFromDraft()` converts draft to a Mod-compatible object → `equippedMods['riven']`. Card shows stat count badge.

## Multi-Attack System
Weapons can have multiple attack modes (e.g. Acceltra Prime: Rocket Impact + Rocket Explosion; Torid: Grenade Impact + Poison Cloud + Incarnon Form). Each attack has its own damage, crit, status, fire rate, and shot type.

**Data schema:** `weapons.json` stores `attacks[]` per weapon. Each attack has `name`, `base_damage`, `innate_elements`, `crit_chance`, `crit_multiplier`, `status_chance`, `fire_rate`, `shot_type`.

**Selection:** `load_weapon(name, attack_name=None)` — defaults to first attack. The selected attack's stats populate `Weapon.base_damage`, `innate_elements`, `crit_chance`, `crit_multiplier`, `status_chance`. All attacks are also available via `Weapon.attacks` for enumeration.

**CLI:** `--attack "Rocket Explosion"` flag (must come before or after all positional args due to argparse).

**API:** POST endpoints (`/api/calculate`, `/api/modded-weapon`) accept optional `"attack"` field. `GET /api/weapons` returns per-weapon `attacks[]` with per-attack stats.

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

**Armor Mitigation** = `300 / (300 + min(armor, 2700))` — flat DR, no per-type modifiers (Update 36+).
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

## Enemy Armor (Post-Update 36: Jade Shadows, June 18 2024)
- **Hard Cap:** Enemy armor is hard-capped at 2,700 (90% DR).
- **Armor Scaling:** `DR = Armor / (Armor + 300)` — flat, no per-type modifiers.
- **No armor-type modifiers:** Update 36 removed Ferrite/Alloy armor types. Armor provides flat DR only. All damage type bonuses/penalties are faction-based (see Faction Effectiveness table).
- `armor_type` field in `enemies.json` and `ArmorType` enum are retained as inert metadata.

## Enemy Level Scaling

Formula source: [wiki.warframe.com/w/Enemy_Level_Scaling](https://wiki.warframe.com/w/Enemy_Level_Scaling) (community-derived).

**ΔLevel** = `max(0, level - base_level)`. Steel Path applies a ×2.5 multiplier to health and shields only — it does **not** add +100 to the level used in the formula.

### Health Multiplier (per-faction)
Smoothstep blend 70–80. `f1(δ) = 1 + A1×δ^e1`, `f2(δ) = 1 + A2×δ^e2`.

| Faction | A1 | e1 | A2 | e2 |
|---|---|---|---|---|
| Grineer / Scaldra | 0.015 | 2.12 | 10.7332 | 0.72   |
| Corpus | 0.015 | 2.12 | 13.4165 | 0.55 |
| Infested | 0.0225 | 2.12 | 16.1 | 0.72 |
| Corrupted | 0.015 | 2.10 | 10.7332 | 0.685 |
| Murmur / Sentient / Unaffiliated | 0.015 | 2.0 | 10.7332 | 0.5 |
| Techrot | 0.02 | 2.12 | 15.1 | 0.7 |

### Shield Multiplier (per-faction)
Same smoothstep structure. Factions not listed use Grineer coefficients.

| Faction | A1 | e1 | A2 | e2 |
|---|---|---|---|---|
| Corpus | 0.02 | 1.76 | 2.0 | 0.76 |
| Corrupted | 0.02 | 1.75 | 2.0 | 0.75 |
| Grineer / Sentient | 0.02 | 1.75 | 1.6 | 0.75 |
| Techrot | 0.02 | 1.76 | 3.5 | 0.76 |

- **Steel Path:** ×2.5 multiplier applied to health and shields

### Overguard (Eximus Only)
Two-regime smoothstep formula (source: wiki.warframe.com/w/Enemy_Level_Scaling):
```
δ_OG  = target_level − enemy_base_level  (same delta as health; SP +100 NOT added for OG)
f1(δ) = 1 + 0.0015 × δ^4            (δ < 45)
f2(δ) = 1 + 260 × δ^0.9             (δ > 50)
T     = (δ - 45) / 5
S2    = 3T² − 2T³                   (45 ≤ δ ≤ 50), else 0 or 1
Overguard = 12 × [f1(δ)·(1 − S2) + f2(δ)·S2]
```
Reference values: δ=0 → 12.0 | δ=10 → 192.0 | δ=45 → 73,823.25 | δ=50 → ~105,592.8 | δ=199 → ~365,676 | δ=599 → ~985,000

### Armor Scaling
Two-regime smoothstep (70–80 transition), hard-capped at 2700 (90% DR):
```
f1(δ) = 1 + 0.005 × δ^1.75
f2(δ) = 1 + 0.4   × δ^0.75
```

### Implementation
- `src/scaling.py` — all formulas; `scale_enemy_stats()` is the main entry point
- `web/api.py` — `POST /api/scaled-enemy` → `{level, health, shield, armor, overguard}`
- UI: enemy panel shows faction, health type (armor type hidden — inert post-Update 36), Level input (1–9999), Steel Path toggle, Eximus toggle
- Display uses `toFixed(2)` → `toLocaleString` to show decimals (e.g. `4,502,520.4`)
- **Do not truncate coefficients** — 6-decimal rounding causes ~9 HP / ~2 OG drift vs wiki

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
