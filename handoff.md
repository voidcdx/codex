# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/review-handoff-notes-lvohz`

---

## What Was Done This Session

### 1. Drop Tables Auto-Refresh
Automated the `drops.html` refresh that was previously manual.

**How it works:**
- `_drops_bg_loop()` in `web/api.py` fetches drop tables from the official CDN every 7 days
- CDN URL: `warframe-web-assets.nyc3.cdn.digitaloceanspaces.com/uploads/cms/hnfvc0o3jnfvc873njb03enrf56.html`
- `_fetch_drops()`: 3 retries, 2s backoff, 30s timeout; falls back to disk `drops.json`
- `parse_mission_rewards()` in `scripts/parse_drops.py` now accepts `Path | str` — server passes HTML string directly
- `sys.exit()` calls replaced with `raise ValueError()` for clean server error handling
- `POST /api/refresh-drops` — manual trigger for on-demand refresh after game updates
- `GET /api/drops` serves from in-memory cache, falls back to disk if cache not populated
- Lifespan manages both worldstate and drops background tasks

### 2. Reliquary Prime Sets Pivot (IN PROGRESS)
Pivoted the Reliquary page from flat relic grid to goal-oriented Prime Sets browser.

**Architecture:**
- Two-panel layout: 260px sidebar + detail panel (`.reliquary-wrap` CSS grid)
- Data derived **client-side** from `/api/relics` — no new endpoint
- `buildPrimeSets(relics)`: filters unvaulted, groups by `item` name → parts → relics
- 42 unvaulted prime sets: 11 warframes (4 parts each), 31 weapons (2-5 parts each)
- Classification: warframe if parts include Neuroptics/Chassis/Systems, else weapon

**UI flow:**
1. Sidebar: search + category tabs (All/Warframes/Weapons) + scrollable set list
2. Click a set → detail panel shows parts as cards (roster-entry style)
3. Click a part → relic drill-down shows relics with tier badges + top 5 drop locations

**Current state — NEEDS DESIGN WORK:**
- The page is **functionally complete** but visually needs polish
- User feedback: "dead flat design", "AI slop" — multiple CSS passes attempted
- Latest version uses `--accent-a*` vars, sidebar has `background: var(--surface)`, part cards have `::before` gradient bleed + `::after` panel line
- Still needs iteration to match the visual quality of the factions/calculator pages
- **The user should screenshot and iterate live** — blind CSS iteration doesn't work well

**Mobile:** Stacks vertically — sidebar on top (max-height 35vh), detail below. Set click scrolls to detail.

---

## Key Files Changed This Session
```
scripts/parse_drops.py           # accepts Path | str; ValueError instead of sys.exit
web/api.py                       # _drops_bg_loop, _fetch_drops, POST /api/refresh-drops
                                 #   _lifespan manages both ws + drops tasks
web/static/reliquary.html        # two-panel layout: .rq-sidebar + .rq-detail
web/static/reliquary.css         # sidebar, part cards, relic drill-down, tier badges
web/static/js/reliquary.js       # buildPrimeSets, selectSet, selectPart, renderDetail
```

---

## Pending / Known Issues
- **Reliquary visual polish** — functional but user unhappy with the design. Needs live iteration with screenshots. The structure/layout is correct; it's the surface treatment, depth, and visual weight that need work.
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **URL state / sharing** — high-value missing feature (no work started).
- **Chrome mobile toolbar collapse** — different browser behavior, not fixable.

---

## Reliquary Prime Sets — Architecture

```
/api/relics (all 732) → JS filter (vaulted=false) → buildPrimeSets()
                                                         ↓
                                               allSets: {
                                                 "Saryn Prime": {
                                                   type: "warframe",
                                                   parts: {
                                                     "Blueprint": [{ relic, tier, rarity }],
                                                     "Neuroptics Blueprint": [...],
                                                     ...
                                                   }
                                                 }
                                               }
                                                         ↓
                                         renderSidebar() ← search + tab filter
                                               ↓ click
                                         renderDetail() → parts grid
                                               ↓ click part
                                         renderRelicSection() → relics + dropsMap lookup
```

## Drops Auto-Refresh — Architecture

```
Server startup → _drops_bg_loop() (asyncio task)
                       ↓
              _fetch_drops() — GET CDN HTML
                       ↓
              parse_mission_rewards(html_string) — in-memory parse
                       ↓
              _drops_cache = parsed dict (served by GET /api/drops)
                       ↓
              sleep 7 days → repeat

Manual trigger: POST /api/refresh-drops → _fetch_drops() → update cache
Fallback: disk data/drops.json via _raw_drops() from src/loader.py
```

---

## Mobile Architecture (≤900px)
```
window scrolls (body/html: overflow:visible, height:auto)
  └── .app (height:auto)
        └── .main (overflow:visible, height:auto)
              ├── .header (in-flow, scrolls away)
              └── .content / .live-wrap / .factions-wrap (overflow:visible)

position:fixed elements (always visible):
  .burger-btn    top-right, z-index:200
  .back-to-top   bottom-right, z-index:199
  .sidebar       full-height drawer, z-index:100
```

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables (--accent-a* for visible tints on dark bg)
web/static/layout.css      # shared layout, header, sidebar, burger, back-to-top
web/static/panels.css      # .panel, input[type=text] scoped to .panel
web/static/factions.css    # .roster-entry pattern (THE reference for list-style components)
web/static/reliquary.css   # .rq-sidebar, .rq-set-item, .rq-part-card, .rq-relic-row
web/static/js/reliquary.js # prime sets state + rendering
web/static/js/theme.js     # theme switcher + positionBackToTop() (loaded on ALL pages)
```

---

## Current State — Themes
```
stalker  (default, no class)   bg: #0a0a0a   surface: #121212   accent: #8b0000 → #e53e3e
jade     body.theme-jade        bg: #080808   surface: rgba(10,18,16,0.85)   accent: #00897b → #00e5c8
ash      body.theme-ash         bg: #080808   surface: rgba(16,16,16,0.85)   accent: #466482 → #7393b3
```

---

## Design System Notes for Next Session
- **Use `--accent-a*` vars** (defined in base.css) for tints on dark bg — `color-mix()` is invisible at low %
- **Reference: factions.css `.roster-entry`** — the gold standard for list components (left accent bar, `::before` gradient, glass surface)
- **Surface contrast**: `--surface` (#121212) vs `--bg` (#0a0a0a) is only 7% brightness diff — panels need explicit background to be visible
- **Font scale**: 0.55–0.85rem for Orbitron display, all uppercase, 0.08–0.2em letter-spacing

## Git Notes
- Working branch: `claude/review-handoff-notes-lvohz`
- `&&` not supported in Windows PowerShell — run git commands separately
