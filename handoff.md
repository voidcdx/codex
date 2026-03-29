# Handoff — Warframe Damage Calculator

## Current Status
**248 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional: dark theme, mod card grid, special slots (stance/exilus), weapon images, riven mod builder, enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks, inline SVG damage type icons. Live page (`/live`) with fissures (two-column, with cycles strip), sorties, archon hunt, void trader, nightwave, alert banner, invasions, events.

Branch: `codex` — last commit `f40b8c2`

---

## What Was Done This Session

### 1. Panel gradient lines — top + bottom
`.panel::before` in `panels.css` updated from a single top gradient to two-layer top + bottom gradient lines (opacity 0.55). Alert banner `::after` uses the same pattern.

### 2. Theme CSS variable changes (`base.css`)
- `--border: rgba(139, 0, 0, 0.2)` — reduced opacity (less visible borders)
- `--radius: 4px` and `--radius-sm: 3px` — slight rounding (was 0)

### 3. Mobile horizontal overflow fix (`live.css`)
- `.live-grid` column template: `minmax(min(360px, 100%), 1fr)` prevents columns forcing wider than viewport
- `overflow-x: hidden` on `.live-wrap`
- Single-column breakpoint raised 600px → 768px

### 4. Fissures panel — cycles strip + two-column layout
- Open World Cycles absorbed into Fissures panel as a strip above tier filter tabs (`.fissure-cycles-strip`)
- `.fissure-list` — two-column grid desktop, single column ≤768px
- `buildCyclesCard()` returns strip fragment only (no panel wrapper)
- `buildFissureCard(fissures, cycles)` embeds cycle strip; `renderAll` no longer renders standalone Cycles card

### 5. Alert banner (`live.html` + `live.css`)
Sticky auto-scrolling ticker between header and `.live-wrap`. Hidden when no alerts.
- `#alert-banner` div in HTML; `buildAlertBanner(alerts)` builds doubled ticker for seamless loop
- `ab-scroll` keyframe: `translateX(0) → translateX(-50%)` over 28s
- Top + bottom gradient lines via `::after`; side borders only
- Alerts panel in grid suppressed when banner is active (null → filtered by `.filter(Boolean)`)

### 6. Touch scroll fixes (`live.css`)
- `.news-row`, `.news-slider`, `.cycle-grid`: `touch-action: pan-x pan-y`
  (was `pan-x` only — blocked vertical page scroll after horizontal swipe)

### 7. News nav arrows — bare style (`live.css`)
`.news-nav-btn`: removed circle background and border. Now bare crimson arrows (`background: none; border: none; opacity: 0.8`).

### 8. No-flash auto-refresh (`live.html`)
`_hasLoaded` flag: loading spinner only shown on first load. Subsequent auto-refreshes update silently in place.

### 9. SolNode748, credits format, CamelCase fix (`parse_worldstate.py`)
- `SolNode748` added to `ALL_NODES` as "Garus (Kuva Fortress)" and `NODE_FACTION` as "Grineer"
- Credits format: `f"{credits:,} Credits"` changed to `f"{credits:,}c"` (two locations)
- `_item_name()` fallback now splits CamelCase via `re.sub(r'([A-Z])', r' \1', raw).strip()`

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
| `web/static/index.html` | Calculator SPA |
| `web/static/live.html` | Live Data SPA — worldstate, fissures, etc. |
| `web/static/base.css` | CSS variables: `--radius: 4px`, `--border: rgba(139,0,0,0.2)` |
| `web/static/live.css` | Live page styles — fissure layout, alert banner, news ticker |
| `web/static/panels.css` | Shared panel styles — top+bottom gradient lines via `::before` |
| `scripts/parse_worldstate.py` | Worldstate parser — `parse(raw)` entry point; `ALL_NODES` + `NODE_FACTION` |
| `__main__.py` | CLI interface |

### Data Files
| File | Records |
|------|---------|
| `data/weapons.json` | 588 weapons |
| `data/mods.json` | 1,405 mods |
| `data/enemies.json` | 983 enemies |

### Live Page — Key JS Functions (`live.html`)
| Function | Purpose |
|----------|---------|
| `buildFissureCard(fissures, cycles)` | Main fissures panel — embeds cycle strip + tier tabs + two-col list |
| `buildCyclesCard(cycles)` | Returns `.fissure-cycles-strip` fragment only (no panel wrapper) |
| `buildAlertBanner(alerts)` | Populates `#alert-banner` ticker; hides when empty |
| `renderAll(data)` | Sets `_hasLoaded = true`; omits Alerts card when banner is active |
| `loadData()` | Fetch + render; shows loading spinner on first load only |

### Live Page Fissure Categories
| Key | Condition |
|-----|-----------|
| `railjack` | `f.is_railjack === true` |
| `requiem` | `f.tier === 'Requiem'` |
| `steelpath` | `f.is_steel_path === true` |
| `origin` | everything else |

Tier column shows label + color from `TIER_COLORS`. Railjack uses `--void-teal: #3ddcb8`. SP tag shown inline in node name for steel path rows.

### Sandbox Git — Commit Workaround
Cowork's background git sync holds `index.lock`, blocking sandbox commits. Commit from Windows terminal instead:
```
cd C:\Users\jesse\Desktop\codex
git add -A && git commit -m "..."
```
`.git/config` has `[index] version = 2` to keep index format compatible between Windows git and sandbox git 2.34.1.

---

## Known Gaps / TODO

- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.

### Already Done (remove from TODO)
- ~~**Kill Time (TTK)**~~ — Implemented in `web/static/js/calculate.js`.
- ~~**Condition Overload**~~ — UI passes `unique_statuses` correctly.
- ~~**Jupiter/Eris node ID audit**~~ — `ALL_NODES` + `NODE_FACTION` fully audited in `parse_worldstate.py`.

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
