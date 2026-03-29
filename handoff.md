# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional. Live page (`/live`) fully rebuilt.

**Version:** `0.5.6`
**Branch:** `claude/review-handoff-notes-2Cmip` — last commit `0ba17fa`

---

## What Was Done This Session

### 1. Code cleanup (dead code removal + import consolidation)
- `web/api.py`: merged duplicate `pydantic` imports; moved late `FileResponse` import to top
- `tests/test_arcanes.py`: removed unused `import math`
- `tests/test_calculator.py`: moved mid-file `Buff`/`make_buff` imports to top
- `__main__.py`: moved inline `import math as _math` to module level
- `utils.js`: removed dead `setSelectValue()` and `setSelectByText()`
- `combobox.js`: removed dead `setupSearch()`
- `app.js`: merged two `DOMContentLoaded` listeners into one

### 2. Enemy picker — name/subtitle alignment
**Before:** Enemy name and faction/health were inside `.threat-card` (which has `padding: 12px`), causing the name to sit 12px lower than the weapon name.

**After:** Name and subtitle are now **outside** the `.threat-card`, sitting directly in `#enemy-stats-content` with no padding above them — same structure as the weapon name in `#weapon-stats-content`.

- `enemy.js`: name uses `.weapon-stats-name`, subtitle uses `.weapon-stats-sub` (plain dim text)
- `panels.css`: `.threat-card` gains `margin-top: 10px` to space it below the name
- `results.css`: `.weapon-stats-img-row` changed from `align-items: center` → `align-items: flex-start` so weapon name aligns to top of image, not mid-image

### 3. Cache-busting
Added `?v=3` version params to all CSS and JS `<link>`/`<script>` tags in `index.html` to force fresh loads after changes.

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
| `web/static/live.css` | Live page styles |
| `web/static/panels.css` | Shared panel styles — `.threat-card` margin-top:10px |
| `web/static/results.css` | `.weapon-stats-img-row` align-items: flex-start |
| `web/static/js/enemy.js` | Enemy panel — name/sub now outside `.threat-card` |
| `scripts/parse_worldstate.py` | Worldstate parser — `parse(raw)`; `_parse_nightwave(raw)`; `ALL_NODES`; `_NW_NAMES` |
| `__main__.py` | CLI interface |

### Data Files
| File | Records |
|------|---------|
| `data/weapons.json` | 588 weapons |
| `data/mods.json` | 1,405 mods |
| `data/enemies.json` | 983 enemies |

### Enemy Panel Structure (post this session)
```html
#enemy-stats-content
  <div class="weapon-stats-name">Enemy Name</div>       ← same class as weapon
  <div class="weapon-stats-sub">Faction · Health Type</div>  ← plain dim text
  <div class="threat-card">                             ← margin-top:10px
    <div class="threat-stats-row">Base Lvl / Head / Armor</div>
    <div class="threat-bars" id="threat-bars"></div>
  </div>
```

### Live Page — Key JS Functions (`live.html`)
| Function | Purpose |
|----------|---------|
| `buildCyclesCard(cycles)` | Standalone full-width cycles block (no `.panel`) |
| `buildFissureCard(fissures)` | Fissures panel — tier tabs + two-col list (no cycles) |
| `buildInvasionsCard(invasions)` | 3-col attacker/VS/defender layout |
| `buildNightwaveCard(nw)` | Nightwave challenges — Daily/Weekly/Elite tags + rep |
| `buildAlertBanner(alerts)` | Populates `#alert-banner` ticker; hides when empty |
| `renderAll(data)` | Panel order: cycles, fissures, invasions, sortie+archon stack, nightwave+baro stack, events |
| `loadData()` | Fetch + render; spinner on first load only |

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
- **Nightwave challenge names** — Some path keys still fall back to CamelCase split. Add to `_NW_NAMES` as they're identified in-game.
- **Deployment** — Railway blocks `api.warframe.com`. Use VPS (DigitalOcean, Hetzner) or Fly.io for hosting.
- **Cache-busting** — Currently manual `?v=N` in index.html. Consider auto-versioning from `APP_VERSION`.

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
