# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional. Live page (`/live`) fully rebuilt.

**Version:** `0.5.7`
**Branch:** `claude/review-handoff-docs-ZSlIJ` — last commit `d08e60e`

---

## What Was Done This Session

### 1. Armor Strip merged into Options panel
**Before:** Armor Strip was a standalone always-visible panel below the Build Compare placeholder in `.content-side`.

**After:** Armor Strip is a collapsible sub-section inside the Options panel (`#options-body`), below Warframe Buffs. It hides/shows with the Options collapse toggle.

- `web/static/index.html`: removed standalone `#armor-strip-panel` block; added `<div class="panel-sub-h">Armor Strip</div>` + `?` help block + all strip-row/strip-result-block divs inside `#options-body`
- No JS or CSS changes needed — `armorstrip.js` uses element IDs which travel with the HTML
- Options panel `?` help text updated to include an **Armor Strip** entry

### 2. Element wheel prototype (abandoned)
Explored replacing the Alchemy Mixer flat pill-row with a radial element wheel. Prototype built, could not be served to user (Windows dev server requires git pull + restart for new FastAPI routes). All files removed. **No persistent UI change.**

### 3. SVG panel background experiment (reverted)
Tried replacing `::after` radial-gradient center halo with an SVG (`panel-bg.svg`) providing edge-only glow (4 linear-gradient rects, transparent center). Reverted after tuning — original radial-gradient restored intact.

### 4. Live page — news ticker fixes
- Removed `"warframe.com" not in url` filter from `_parse_news` — new articles linking to Steam, patch-notes pages, or forums now pass through
- Added `"visit the official warframe forums!"` (with `!`) to `_NEWS_GENERIC_MESSAGES`
- Fixed `_debug_news` to match the same filter logic
- News thumbnails: `object-fit: contain`, fixed `height: 130px`, dark bg letterbox for off-ratio images
- Debug endpoint `/api/worldstate/debug-news` — shows `accepted` + `rejected` with reasons

### 5. `SORTIE_MODIFIER_EXPLOSION` mapped
Added to `SORTIE_MODIFIERS` dict in `scripts/parse_worldstate.py` → `"Environmental Hazard: Explosion"`.

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
| `web/static/index.html` | Calculator SPA — all CSS/JS links use `?v=3` cache-busting |
| `web/static/live.html` | Live Data SPA |
| `web/static/base.css` | CSS variables |
| `web/static/live.css` | Live page styles — news thumbnail CSS at line ~518 |
| `web/static/panels.css` | Shared panel styles — `.panel::after` radial halo, `.panel::before` 1px lines |
| `web/static/results.css` | `.weapon-stats-img-row` align-items: flex-start |
| `web/static/js/armorstrip.js` | updateArmorStripDisplay(), getArmorStripPayload(), initArmorStrip() — uses IDs only |
| `scripts/parse_worldstate.py` | Worldstate parser — `parse(raw)`; `_parse_news()`; `SORTIE_MODIFIERS` (~L169); `ALL_NODES`; `_NW_NAMES` |
| `__main__.py` | CLI interface |

### Data Files
| File | Records |
|------|---------|
| `data/weapons.json` | 588 weapons |
| `data/mods.json` | 1,405 mods |
| `data/enemies.json` | 983 enemies |

### Options Panel Structure
```html
#options-panel  ← collapsible, collapsed by default
  #options-body
    <!-- Hit Options (crit mode, headshot, distance, combo) -->
    <div class="panel-sub-h">Warframe Buffs</div>
    <div id="buff-rows">...</div>
    <div class="panel-sub-h">Armor Strip  <button class="btn-help">?</button></div>
    <div class="panel-help hidden">...</div>
    <!-- strip-row x2 (ability, CP) + strip-result-block -->
```

### Alchemy Mixer — Current State
Flat pill-row element picker (two rows: 4 primary + 6 combined). No redesign yet.
- Radial wheel concept discussed, on hold. Design notes:
  - Two rings: 4 primary inner (90° spacing) + 6 combined outer (60° spacing)
  - CSS pattern: `transform: rotate(Ndeg) translateY(-R) rotate(-Ndeg)`
  - Mobile: CSS vars `--inner-r` / `--outer-r`, media query ≤520px
  - Trapezoid petal shapes via `clip-path: polygon()`

### Live Page — Key JS Functions (`live.html`)
| Function | Purpose |
|----------|---------|
| `buildCyclesCard(cycles)` | Standalone full-width cycles block (no `.panel`) |
| `buildFissureCard(fissures)` | Fissures panel — tier tabs + two-col list |
| `buildInvasionsCard(invasions)` | 3-col attacker/VS/defender layout |
| `buildNightwaveCard(nw)` | Nightwave challenges — Daily/Weekly/Elite tags + rep |
| `buildAlertBanner(alerts)` | Populates `#alert-banner` ticker; hides when empty |
| `buildNewsSection(news)` | Horizontal scrollable news cards — `#live-news` |
| `renderAll(data)` | Panel order: cycles, fissures, invasions, sortie+archon stack, nightwave+baro stack, events |
| `loadData()` | Fetch + render; spinner on first load only |

### News Parsing (`_parse_news` in `scripts/parse_worldstate.py`)
Filters `Events[]` from worldstate. Keeps entries with:
- English message, length > 20, not `/Lotus/` path, not in `_NEWS_GENERIC_MESSAGES`
- Any URL (or no URL — shown as non-linked span in frontend)
Debug endpoint: `GET /api/worldstate/debug-news` → `{accepted, rejected}` with reasons.

### Sortie Modifier Map
`SORTIE_MODIFIERS` dict at `scripts/parse_worldstate.py` ~L169. Add missing keys as they appear in-game. Raw keys look like `SORTIE_MODIFIER_EXPLOSION`.

### Sandbox Git — Commit Workaround
Cowork's background git sync holds `index.lock`, blocking sandbox commits. Commit from Windows terminal instead:
```
cd C:\Users\jesse\Desktop\codex
git add -A && git commit -m "..."
```
`.git/config` has `[index] version = 2` — do not remove.

---

## Known Gaps / TODO

- **Alchemy Mixer wheel** — On hold. User wants to think about it.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.
- **Nightwave challenge names** — Some path keys still fall back to CamelCase split. Add to `_NW_NAMES` as identified.
- **Deployment** — Railway blocks `api.warframe.com`. Use VPS (DigitalOcean, Hetzner) or Fly.io.
- **Cache-busting** — Currently manual `?v=N` in index.html. Consider auto-versioning from `APP_VERSION`.
- **Sortie modifiers** — Add any new `SORTIE_MODIFIER_*` keys as they appear in-game.

---

## Scripts (run order after rescrape)
```bash
python scripts/parse_wiki_data.py      # rebuild weapons.json + mods.json from raw
python scripts/fix_secondary_stats.py  # backfill 109 secondary stat fields
python scripts/fix_galv_stats.py       # restore 10 galvanized mod fields
```

## Tests
```bash
pytest   # 304 passing — run before every commit
```
