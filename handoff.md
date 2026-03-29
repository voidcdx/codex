# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional. Live page (`/live`) fully rebuilt with **live countdown timers**.

**Version:** `0.5.7`
**Branch:** `claude/review-handoff-notes-46SWF` — last commit `9a13c2b`

---

## What Was Done This Session

### 1. Font size fixes (live page + calculator)
- `.reward-chip` bumped `0.73rem` → `0.85rem` (matches `.invasion-faction`)
- `.modifier-badge` (sortie modifiers) bumped `0.73rem` → `0.85rem`; border removed; color → `var(--crimson-bright)`
- `.strip-bar-label-left` / `.strip-bar-label-right` ("Original" / "0% stripped") bumped `0.67rem` → `0.85rem`

### 2. Warframe Buffs help text fix
- "Enter ability strength as a **decimal** (e.g. 1.5 for 150%)" → "Enter ability strength as a **percentage** (e.g. 150 for 150%)"
- Input actually sends `parseFloat(val) / 100` — text was always wrong

### 3. Helminth checkbox — crimson custom styling
- Removed inline `style=` from label and checkbox in `web/static/js/modals.js`
- Added `.buff-helminth-label` (crimson, `0.73rem`, flex) and `.buff-subsumed` (fully custom: `appearance:none`, crimson border, crimson fill + white checkmark on `:checked`) to `panels.css`
- Cache-busted `panels.css?v=7` and `modals.js?v=4` in `index.html`

### 4. Live countdown timers
Full real-time countdown on all expiring live page sections:

**Parser (`scripts/parse_worldstate.py`)** — added `expiry_ts` (Unix float) to:
- Fissures: already had it
- Alerts: already had it
- Sortie, Archon Hunt, Nightwave (season + per-challenge), Void Trader, Events, all Cycles (Cetus/Vallis/Cambion/Earth/Zariman/Duviri)

**Frontend (`web/static/live.html`)** — added `data-expiry="${expiry_ts}"` to all eta display elements. Added:
- `fmtCountdown(secs)` — formats `Xd Yh` / `Xh Ym Zs` / `Xm Ys` / `Xs`
- `startEtaTimer()` — single shared `setInterval(1000)`, scans all `[data-expiry]` elements, computes `Date.now()/1000 - exp`, updates textContent. Recalculates from wall clock each tick (no drift on tab background).
- Called from `renderAll()` after DOM is built.

**Bug fixed:** Duviri cycle was missing `expiry_ts` — added `"expiry_ts": ts + secs_left`.

### 5. HTML caching fix
- Added `headers={"Cache-Control": "no-store"}` to `/`, `/live`, `/factions`, `/enemy-preview` `FileResponse` routes in `web/api.py`
- Prevents browser from serving stale HTML after deploys

### 6. Favicon
- Added `/favicon.ico` route in `web/api.py` → serves `web/static/favicon.png`
- `web/static/favicon.png` — 32×32 void/purple spiral icon (user-provided)
- `<link rel="icon" type="image/png" href="/favicon.ico">` added to `index.html` and `live.html`
- Stops 404 log spam for favicon requests

### 7. News thumbnail brown background fix
- `.news-thumb` and `.news-thumb-ph` backgrounds changed from `var(--surface-solid)` (`#201818` brownish) to `var(--bg)` (`#050505`) — letterbox bars and placeholder now blend into the page

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
| `web/api.py` | FastAPI endpoints; `no-store` cache on all HTML routes |
| `web/static/index.html` | Calculator SPA — CSS/JS links use `?v=N` cache-busting |
| `web/static/live.html` | Live Data SPA — inline JS, countdown engine |
| `web/static/base.css` | CSS variables |
| `web/static/live.css` | Live page styles |
| `web/static/panels.css` | Shared panel styles; `.buff-helminth-label`, `.buff-subsumed`, `.strip-bar-label-*` |
| `web/static/results.css` | Results table |
| `web/static/js/modals.js` | Helminth label/checkbox — no inline styles, uses CSS classes |
| `web/static/js/armorstrip.js` | Armor strip logic — uses IDs only |
| `scripts/parse_worldstate.py` | Worldstate parser — `expiry_ts` on all sections |
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

### Live Page Countdown Engine
`fmtCountdown(secs)` in `live.html`:
- `>= 1 day`: `Xd Yh` (updates hourly — noisy to show seconds for weekly resets)
- `< 1 day`: `Xh Ym Zs` (ticks every second)
- `< 1 hour`: `Xm Ys`
- `< 1 min`: `Xs`

`startEtaTimer()` — single `setInterval(1000)`, queries all `[data-expiry]` each tick. Called from `renderAll()`. `_etaTimer` module-level var, cleared on re-render.

All sections with `expiry_ts` in parser response: fissures, alerts, sortie, archon hunt, nightwave (season + challenges), void trader, events, cycles (Cetus/Vallis/Cambion/Earth/Zariman/Duviri).

### CSS Cache Busting
Manual `?v=N` on `<link>` and `<script>` tags in `index.html`. Current versions:
- `panels.css?v=7`
- `modals.js?v=4`
- Other files at `?v=3`

Bump when changing a static file and needing users to get the update immediately.

### Sandbox Git — Commit Workaround
Cowork's background git sync holds `index.lock`, blocking sandbox commits. Commit from Windows terminal instead:
```
cd C:\Users\jesse\Desktop\codex
git add -A && git commit -m "..."
```
`.git/config` has `[index] version = 2` — do not remove.

---

## Known Gaps / TODO

- **Alchemy Mixer wheel** — On hold. Radial wheel concept discussed, design notes in previous handoff.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.
- **Nightwave challenge names** — Some path keys still fall back to CamelCase split. Add to `_NW_NAMES` as identified.
- **Deployment** — Railway blocks `api.warframe.com`. Use VPS (DigitalOcean, Hetzner) or Fly.io.
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
