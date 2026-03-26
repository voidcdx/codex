# Calculator Accuracy Assessment

**Honest answer: probably 75–80% accurate for mainstream cases, but with real gaps worth knowing about.**

---

## High confidence

- Pipeline structure (6 steps, order of operations) — sourced from community research and wiki, matches the test cases we wrote
- Quantization (1/32 scale, ROUND_HALF_UP) — verified against wiki examples
- Armor formula post-Update 36 (flat DR, 2700 cap) — confirmed
- Viral/Corrosive stack multipliers — exact values from wiki
- Elemental combination slot order — tested

---

## Meaningful uncertainty

- **Data quality** — 27 known placeholder weapons (100.0 values), and we haven't cross-checked weapon stats against live game recently. A wrong base damage number cascades through every step
- **Faction effectiveness table** — coded from the wiki but haven't verified every matchup in-game. This changes with updates
- **Status proc formulas** — especially Gas (scales off base damage × bonus, not step-2 total like the others). Implemented per the wiki but one of the harder ones to verify
- **Proc double-dipping** — the faction mod applying twice on DoT procs is a documented mechanic but the exact multiplier hasn't been validated against real numbers
- **No systematic in-game verification** — tests were written to match the math, not to match recorded in-game screenshots

---

## Least confident

- Unusual weapons with special mechanics (Catchmoon falloff, beam weapons, AoE)
- Damage Falloff (not implemented at all)
- Any mechanic changed in an update between when the wiki was scraped and now

---

## Key distinction

The 290 tests passing means the code is internally consistent — not that it matches the game. Those are different things.
