# Handoff — Warframe Damage Calculator

## Current Status
**248 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional: dark theme, mod card grid, special slots (stance/exilus), weapon images, riven mod builder, enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks, inline SVG damage type icons.

Branch: `claude/continue-handoff-aMsDx`

---

## What Was Done This Session

### 1. Mod grid — fix scroll on mobile (SortableJS)
SortableJS was immediately capturing touch events on mod cards, blocking page scroll. Fixed by adding `delay: 150` + `delayOnTouchOnly: true` to the Sortable config. Desktop drag is instant; mobile requires a 150ms long-press before drag begins.

### 2. Tighter text field sizing (desktop + mobile)
Reduced padding and font sizes across all form inputs for a more compact UI:
- Global inputs/selects: `padding 8px 10px → 5px 8px`, `font 13px → 12px`, margins reduced
- Riven modal inputs: `height 36px → 30px`, `font 14px → 12px`
- Mobile (≤768px): preserves `font-size: 16px !important` (iOS zoom prevention), adds tight padding override
- Combobox dropdown items: padding reduced

### 3. Weapon/enemy search — bare-bones rewrite
Stripped the combobox of all overcomplicated machinery that caused bugs on mobile and desktop:

**Removed:**
- Body portal (`document.body.appendChild`) + `position: fixed` + JS repositioning on every scroll/resize
- `ignoreBlur` mousedown/mouseup hack
- `tabindex` on every dropdown item (fought touch scrolling)
- Arrow key navigation inside dropdown
- `blur` timeout close

**Added/fixed:**
- `position: absolute` inside `.combobox-wrap` — natural DOM positioning
- `overscroll-behavior: contain` — dropdown scroll no longer bleeds to page
- `-webkit-overflow-scrolling: touch` — iOS momentum scrolling
- `mousedown` + `e.preventDefault()` for desktop selection (no blur)
- Clean `touchend` handler for mobile item selection
- Click-outside-to-close via single `mousedown` document listener

### 4. Dropdown z-index fix (behind tables)
`.panel` uses `backdrop-filter` which creates a CSS stacking context, trapping the dropdown's z-index. Fix: when a dropdown opens, its parent `.panel` gets `.combobox-open` class (`z-index: 50; position: relative`) to lift it above sibling panels. Removed on close.

### 5. Dropdown collapses on touch scroll — fixed
`document.addEventListener('touchstart', ...)` was firing when scrolling inside the dropdown, closing it. Removed the touchstart close listener entirely. Mobile close now relies on tapping outside (mousedown fires on mobile too after touch).

### 6. Search UX — clear on click, persist stats
Two UX improvements to the search flow:
- **Click-to-clear:** Focusing the search input now clears the text and opens the full dropdown immediately. No need to manually delete the name or click X first.
- **Persist stats:** Clicking X or abandoning a search no longer wipes the stats panel. Stats remain visible showing the last confirmed selection until a new one is committed. Achieved via `_confirmed` variable inside `setupCombobox` — restored to input on close-without-commit (Escape or click-outside).

---

## Architecture Quick Reference

### Damage Pipeline (6 Steps)
```
1. Base Damage × (1 + ΣDamageMods)         → Modded Base   [floor]
2. Modded Base × Body Part × Crit           → Part Damage   [round nearest]
3. Part Damage × Faction Type Effectiveness  → Typed Damage   [floor]
4. Typed Damage × Armor Mitigation          → Mitigated     [floor]
5. Mitigated × (1 + FactionMod + Roar)      → Final         [floor]
5.5. Final × Eclipse multiplier             → Buffed Final   [floor]
6. Buffed Final × Viral stacks              → Viral Damage   [floor]
```

### Key Files
| File | Purpose |
|------|---------|
| `src/calculator.py` | 6-step pipeline + crit + armor + faction + Viral + procs |
| `src/loader.py` | JSON → Weapon/Mod/Enemy; case-insensitive; attack selection |
| `src/buffs.py` | 4 buff presets (Roar, Eclipse, Xata's Whisper, Nourish) |
| `src/models.py` | Weapon, WeaponAttack, Mod, Enemy, Buff, DamageComponent |
| `src/scaling.py` | Enemy level scaling per faction |
| `src/combiner.py` | Elemental combination by mod slot order |
| `src/quantizer.py` | quantize() — Decimal + ROUND_HALF_UP |
| `web/api.py` | FastAPI endpoints |
| `web/static/index.html` | SPA — all JS inline |
| `web/static/style.css` | Dark theme styles |
| `__main__.py` | CLI interface |

### Data Files
| File | Records |
|------|---------|
| `data/weapons.json` | 588 weapons |
| `data/mods.json` | 1,405 mods |
| `data/enemies.json` | 983 enemies |

### Combobox Architecture (post-rewrite)
`setupCombobox(inputId, dropdownId, items, onSelect, getImageUrl)` in `index.html`:
- Dropdown is `position: absolute` inside `.combobox-wrap` — **no portal**
- `_confirmed` tracks last committed name; restored to input on abandon
- `.panel.combobox-open` lifts parent panel z-index when open
- `overscroll-behavior: contain` on `.combobox-dropdown` prevents scroll bleed
- Selection: `mousedown` (desktop) + `touchend` (mobile), both with `e.preventDefault()`
- Close: `mousedown` outside only (no touchstart — it caused scroll collapse)
- X button dispatches `combobox-clear` custom event to reset `_confirmed` without calling `onSelect`

---

## Known Gaps / TODO

### Not yet implemented
- **Weapon Arcanes** — Deadhead, Merciless, Cascadia Flare. Stack-based bonuses not modelled.
- **Kill Time (TTK)** — Shots and seconds to kill at given enemy level.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.

### Partially wired
- **Condition Overload** — `condition_overload_bonus` parsed and stored on Mod. Calculator uses `unique_statuses` parameter. API/CLI don't pass actual unique status counts from UI — caller-side wiring missing.

### Design unsettled
- **Header / Branding** — Current plain header works but user wants something better. Previous attempts (SVG wings, hero banner) all removed. Needs mobile-first design (≤375px).
- **Combobox styling** — Intentionally stripped bare this session. Ready to be restyled (border, hover states, shadow, etc.) now that the core mechanics are stable.

---

## Scripts (run order after rescrape)
```bash
python scripts/parse_wiki_data.py      # rebuild weapons.json + mods.json from raw
python scripts/fix_secondary_stats.py  # backfill 109 secondary stat fields
python scripts/fix_galv_stats.py       # restore 10 galvanized mod fields
```

## Tests
```bash
pytest   # 248 passing — run before every commit
```
