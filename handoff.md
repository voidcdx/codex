# Handoff — Warframe Damage Calculator

## Current Status
**248 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional: dark theme, mod card grid, special slots (stance/exilus), weapon images, riven mod builder, enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks, inline SVG damage type icons.

Branch: `codex`

---

## What Was Done Recently

### Live Page (`/live`) — Major Work

**Worldstate parsing (`scripts/parse_worldstate.py`)**
- Fixed Railjack fissure detection: `is_railjack` now checks `raw_node.startswith("CrewBattleNode")` instead of mission type matching (which never worked)
- Added/corrected node name mappings: SolNode45, 184, 203, 204, 215, 709–721, 229, 741–747

**Live page design (`web/static/live.html` + `web/static/live.css`)**
- News section: landscape cards (220×130px), `position: relative` on `.news-slider`, nav buttons (`‹ ›`) are `position: absolute` overlaid on left/right edges — semi-transparent dark background so images show through, crimson-wash hover, circular (border-radius: 50%)
- News card text: `position: absolute` overlay at card bottom with multi-stop gradient (`transparent → rgba(0,0,0,0.55) → rgba(0,0,0,0.82)`)
- Placeholder card for missing images: `<div class="news-thumb news-thumb-ph">` (a plain div, NOT SVG — SVG ignores parent `overflow: hidden`)
- No scrollbar on news row (`scrollbar-width: none`)
- `gap: 16px` on `.live-wrap` to space all panels apart

**Global panel styling (`web/static/panels.css`)**
- `.panel { border-radius: 8px }` — all panels across the app now have rounded corners
- `.panel h2 { font-size: 0.85rem }` — panel headers reduced from 1rem to 0.85rem Orbitron

---

## Architecture Quick Reference

### Damage Pipeline (6 Steps)
```
1. Base Damage × (1 + ΣDamageMods)          → Modded Base   [floor]
2. Modded Base × Body Part × Crit            → Part Damage   [round nearest]
3. Part Damage × Faction Type Effectiveness  → Typed Damage  [floor]
4. Typed Damage × Armor Mitigation           → Mitigated     [floor]
5. Mitigated × (1 + FactionMod + Roar)       → Final         [floor]
5.5. Final × Eclipse multiplier              → Buffed Final  [floor]
6. Buffed Final × Viral stacks               → Viral Damage  [floor]
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
| `web/static/index.html` | Calculator SPA — all JS inline |
| `web/static/live.html` | Live Data SPA — worldstate, fissures, news, etc. |
| `web/static/live.css` | Live page styles |
| `web/static/panels.css` | Shared panel/component styles (border-radius: 8px) |
| `scripts/parse_worldstate.py` | Worldstate parser — `parse(raw)` entry point |
| `__main__.py` | CLI interface |

### Data Files
| File | Records |
|------|---------|
| `data/weapons.json` | 588 weapons |
| `data/mods.json` | 1,405 mods |
| `data/enemies.json` | 983 enemies |

### Combobox Architecture
`setupCombobox(inputId, dropdownId, items, onSelect, getImageUrl)` in `index.html`:
- Dropdown is `position: absolute` inside `.combobox-wrap` — no portal
- `_confirmed` tracks last committed name; restored to input on abandon
- `.panel.combobox-open` lifts parent panel z-index when open
- Selection: `mousedown` (desktop) + `touchend` (mobile), both with `e.preventDefault()`
- Close: `mousedown` outside only (no touchstart)

---

## Known Gaps / TODO

### Not yet implemented
- **Kill Time (TTK)** — Shots and seconds to kill at given enemy level.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.
- **Unresolved node names** — `Node220 (Sol)`, `Node10 (Sol)` still appear in fissure list; not yet mapped.

### Partially wired
- **Condition Overload** — parsed and stored on Mod. Calculator uses `unique_statuses` parameter but UI doesn't pass actual unique status counts.

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
