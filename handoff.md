# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/continue-handoff-docs-2Mf89`

---

## What Was Done This Session

### Relic Drop Locations — Full Pipeline
Added "where to farm this relic" data to the Reliquary page.

**Data source:** `data/drops.html` — official Warframe drop tables page saved locally.

**Parser:** `scripts/parse_drops.py`
- BeautifulSoup4 parses `#missionRewards` section (lines 114–994)
- State machine: mission header → rotation header → item rows → blank-row separator
- Normalizes relic names: "Lith D7 Relic" → "Lith D7" (matches `relic.name` in relics.json)
- Deduplicates by `(location, mission_type, rotation, rarity, chance)` tuple
- Output: `data/drops.json` — 34 relics, 3409 entries, keyed by relic name

**Schema:**
```json
{
  "Lith D7": [
    {"location": "Void/Taranis", "mission_type": "Defense", "rotation": "A", "rarity": "Rare", "chance": 6.67}
  ]
}
```
- `rotation` is `null` for no-rotation missions (Capture, Exterminate, etc.)
- 34 relics = only currently-unvaulted, actively-dropping relics (correct — vaulted ones don't appear in mission drop tables)

**Backend:**
- `src/loader.py` — `_raw_drops()` cached loader (same pattern as `_raw_relics()`)
- `web/api.py` — `GET /api/drops` endpoint

**Frontend (`web/static/js/reliquary.js`):**
- Parallel fetch: `Promise.all([fetch('/api/relics'), fetch('/api/drops')])`
- `renderDropSection(relic)` — looks up `dropsMap[relic.name]`, renders top 5 by highest % 
- Button toggle: `<button onclick="toggleDrops(this)">` → `btn.closest('.relic-drops-section').classList.toggle('open')`
- `IntersectionObserver` on each `.relic-card` — removes `.open` when card scrolls out of view
- `<details>`/`<summary>` was tried and abandoned — caused multi-card expansion issues in grid

**CSS (`web/static/reliquary.css`):**
- `.relic-drops-section` — `border-top: 1px solid var(--border)`
- `.relic-drops-toggle` — full-width button, Rajdhani 0.75rem, chevron rotates on open
- `.drop-list { display: none }` / `.relic-drops-section.open .drop-list { display: flex }`
- `.drop-row` — grid: `1fr auto auto auto` (location | mission | rotation badge | chance%)
- Rarity-colored chance %: Common=dim, Uncommon=accent2, Rare=gold, Ultra Rare=#e879f9, Legendary=tier-axi

### Back-to-Top Button — Desktop Position Fix
Button was `position: fixed; right: 16px` which overlapped the right sidebar (260px wide).

**Fix:** `positionBackToTop()` in `theme.js` — reads `sidebar.getBoundingClientRect().left` at runtime and sets `btn.style.right = (window.innerWidth - sidebarLeft + 16) + 'px'`. Also fires on `resize`. This handles `.app`'s `max-width: 1440px; margin: 0 auto` centering correctly at any viewport width.

### Grid Card Height Fix
`align-items: start` was tried on `.relic-grid` to prevent card stretching when a drop list opened. Reverted — it caused gaps below Baro/vaulted relics (no drop data = shorter cards). Default `stretch` is fine because the CSS class toggle means only the clicked card's content changes; neighbours just grow taller without showing content.

### Vercel Agent Skills
Installed via `npx skills i vercel-labs/agent-skills -y`:
- `web-design-guidelines` — audits UI against 100+ Vercel design rules
- `vercel-react-best-practices`, `vercel-composition-patterns`, `vercel-react-view-transitions`
- `vercel-cli-with-tokens`, `deploy-to-vercel`, `vercel-react-native-skills`
- Committed to `.agents/skills/` + `.claude/skills/` symlinks + `skills-lock.json`

---

## Key Files Changed This Session
```
data/drops.html                  # raw Warframe drop tables HTML (source data)
data/drops.json                  # parsed: 34 relics, 3409 drop entries
scripts/parse_drops.py           # BeautifulSoup parser for missionRewards section
requirements.txt                 # added beautifulsoup4>=4.12
src/loader.py                    # _raw_drops() cached loader
web/api.py                       # GET /api/drops endpoint
web/static/js/reliquary.js       # dropsMap fetch, renderDropSection, toggleDrops, IntersectionObserver
web/static/reliquary.css         # drop section styles — toggle button, drop-row grid, rarity colors
web/static/js/theme.js           # positionBackToTop() — reads sidebar BoundingClientRect
web/static/layout.css            # minor back-to-top tweaks
.agents/skills/                  # Vercel agent skills
.claude/skills/                  # symlinks
skills-lock.json                 # skills lock file
```

---

## Pending / Known Issues
- **Back-to-top button** — desktop position fix pushed but user reported still wrong; may need `git pull` + hard refresh (Ctrl+Shift+R). JS-based fix (`positionBackToTop`) reads sidebar BoundingClientRect — should work at any viewport width.
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **URL state / sharing** — high-value missing feature (no work started).
- **Chrome mobile toolbar collapse** — different browser behavior, not fixable.
- **drops.html refresh** — when Warframe updates add new relics to mission rotation, re-save drops.html from the official drop tables page and re-run `python scripts/parse_drops.py`.

---

## Reliquary Drop Locations — Architecture Notes

```
drops.html (raw) → parse_drops.py → drops.json → GET /api/drops → dropsMap (JS)
                                                                        ↓
                                                          renderDropSection(relic)
                                                          top 5 by highest chance%
                                                          IntersectionObserver closes on scroll-away
```

**Why only 34 relics in drops.json:** The missionRewards section only lists currently-active relics in mission rotation. Vaulted relics don't drop from missions so they correctly have no entries. When vault rotations change, refresh drops.html + re-parse.

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

Desktop (>900px) is completely unchanged — inner div scroll as before.

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables; html/body rules; mobile overflow override
web/static/layout.css      # shared layout, header, sidebar, burger, back-to-top, mobile scroll refactor
web/static/panels.css      # .panel, input[type=text] scoped to .panel
web/static/reliquary.css   # all reliquary styles — search pill, vault button, tier seg, pagination, drop section
web/static/js/reliquary.js # filter state, search pill, vault toggle, renderGrid, pagination, drop locations
web/static/js/theme.js     # theme switcher + initBackToTop() + positionBackToTop() (loaded on ALL pages)
```

---

## Current State — Themes
```
stalker  (default, no class)   bg: #0a0a0a   surface: #121212   accent: #8b0000 → #e53e3e
jade     body.theme-jade        bg: #080808   surface: rgba(10,18,16,0.85)   accent: #00897b → #00e5c8
ash      body.theme-ash         bg: #080808   surface: rgba(16,16,16,0.85)   accent: #466482 → #7393b3
```

---

## Git Notes
- Working branch: `claude/continue-handoff-docs-2Mf89`
- User is on same branch locally
- `&&` not supported in Windows PowerShell — run git commands separately
