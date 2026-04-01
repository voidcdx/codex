# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/review-handoff-0NdQw`

---

## What Was Done This Session

### Reliquary Page (`/reliquary`) — NEW
Full relic browser page. 732 relics: Lith 188, Meso 177, Neo 175, Axi 183, Requiem 5, Vanguard 4.

**Files added:**
- `scripts/fetch_wiki_playwright.py` — Playwright-based wiki fetcher (bypasses 403s). Fetches `weapons_data.lua`, `mods_data.lua`, `enemies_data.lua`, `void_data.lua`. Must run on Windows (sandbox has no outbound internet). Handles both old (`stealth_async`) and new (`Stealth` class) playwright-stealth APIs.
- `scripts/parse_relic_data.py` — Parses `data/void_data.lua` → `data/relics.json`. Key fix: `_extract_block()` skips the empty `RelicData = {}` declaration (line 51 in the Lua file) and finds the real data block.
- `data/relics.json` — 732 entries. Each: `{name, tier, vaulted, is_baro, introduced, rewards: [{item, part, rarity}]}`
- `web/static/reliquary.html` — Page at `/reliquary`. Sidebar nav matches calculator/factions/live. Controls: search row (search input + count) + filter row (tier pills + vault segmented control).
- `web/static/reliquary.css` — Styles for controls, tier pills, vault segmented control, relic card grid, reward rows with rarity coloring.
- `web/static/js/reliquary.js` — Filters by tier/vault/search. `matchesSearch()` checks relic name + all reward items + parts.

**Files modified:**
- `src/loader.py` — Added `_raw_relics()` lru_cache loader
- `web/api.py` — Added `GET /api/relics` (tier/vaulted/reward query params) + `GET /reliquary` route
- All sidebar HTML pages (index, calculator, factions) — Added Reliquary nav link (lock icon SVG)

### Incarnon Mode Toggle — NEW
Weapons with attacks named `*incarnon*` get a `Normal | Incarnon` pill toggle in the weapon panel instead of raw attack tabs. Multi-variant Incarnon (e.g. Form + Form AoE) get sub-tabs when Incarnon is active.

**Files modified:**
- `web/static/js/weapons.js` — `selectIncarnonMode()`, `renderAttackTabs()` updated
- `web/static/results.css` — `.incarnon-toggle`, `.incarnon-btn`, `.incarnon-btn.active` styles

---

## Unresolved UI Issue — Reliquary Layout
The user flagged two issues that were NOT fully resolved:
1. **Empty space to the right of cards** — The relic grid shows cards only on the left with a large empty area on the right. Root cause not yet diagnosed. Likely the `.relic-grid` inside `.factions-wrap` (flex column) is not expanding to full width, or `auto-fill` is only creating 1 column. Needs investigation.
2. **Rounded corners inconsistency** — `border-radius: 20px` on search input, tier pills, and vault seg doesn't match the app's `var(--radius-sm)` standard. An attempt to fix this was reverted by user ("no that's not it") — unclear what the user actually wants. Needs clarification before touching.

---

## Current State — Themes
```
stalker  (default, no class)   bg: #0a0a0a   surface: #121212   accent: #8b0000 → #e53e3e
jade     body.theme-jade        bg: #080808   surface: rgba(10,18,16,0.85)   accent: #00897b → #00e5c8
ash      body.theme-ash         bg: #080808   surface: rgba(16,16,16,0.85)   accent: #466482 → #7393b3
```

## CSS File Map
```
web/static/base.css        # :root (Stalker) + body.theme-jade + body.theme-ash — all CSS variables
web/static/layout.css      # .header, .sidebar, .brand, .theme-switcher, .sidebar-footer, mobile media
web/static/panels.css      # .panel, .panel::before, .mod-grid, .mod-card, .mod-picker, dropdowns
web/static/live.css        # live page only — event rows, cycles, fissures, news/events panel
web/static/results.css     # .btn-calc, result display, incarnon toggle
web/static/responsive.css  # breakpoint overrides
web/static/factions.css    # faction roster styles
web/static/reliquary.css   # reliquary page styles (NEW)
web/static/js/theme.js     # applyTheme(), initTheme(), localStorage key: 'void-theme'
web/static/js/reliquary.js # relic browser logic (NEW)
```

---

## Tier Color Tokens (reliquary.css :root)
```css
--tier-lith:    #9ca3af;   /* cool gray-silver */
--tier-meso:    #4ade80;   /* soft green */
--tier-neo:     #60a5fa;   /* sky blue */
--tier-axi:     #fbbf24;   /* warm gold */
--tier-requiem: #c084fc;   /* violet */
--tier-vanguard:#fb923c;   /* orange — legacy tier */
```

---

## Pending / Known Issues
- **Reliquary empty space bug** — see above. Diagnose why grid doesn't fill full width.
- **Reliquary rounded corners** — user wasn't happy with 20px pills but also rejected `var(--radius-sm)` fix. Needs clarification.
- **Drop location data** — not present in `Module:Void/data`. Would require scraping a separate wiki module. Not started.
- **27 placeholder weapons** — have fake IPS values in `data/weapons.json`. Data quality issue.
- **Enkaus weapon** — re-run data refresh once wiki module is updated.
- **URL state / sharing** — high-value missing feature (no work started).

---

## Git Notes
- Working branch: `claude/review-handoff-0NdQw`
- User is on branch `codex` locally on Windows — they merge from the claude branch
- `&&` not supported in Windows PowerShell — run git commands separately
