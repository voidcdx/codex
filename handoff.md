# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/continue-documentation-l3g96`

---

## What Was Done This Session

### Worldstate Parser Fixes
- **`SORTIE_MODIFIER_POISON`** → `"Enemy Elemental Enhancement: Toxin"`
- **`MT_EVACUATION`** → `"Defection"` (was showing raw key)
- **`AimGlide`** added to `_NW_NAMES` / `_NW_DESCRIPTIONS` — daily Nightwave challenge was falling back to regex → "Aim Glide" instead of "Glider"

### Invasion Reward Colors
- `.reward-chip` in invasion rows now colored by faction via `data-faction` attribute + CSS selectors
- Grineer = `#c07828`, Corpus = `#4090c0`, Infested = `#60a030`, Other = `#9060c0`

### Reliquary Controls — Single Row
- Collapsed two-row layout (search row + filter row) into one flex row
- Order: `[🔍 expandable search] [All·Lith·Meso·Neo·Axi·Requiem] [All·Unvaulted·Vaulted] [count]`
- Tier pills restyled as single connected segmented control (matching vault-seg)
- Vault seg: `margin-left: auto` keeps it right-aligned

### Reliquary Search — Expandable Pill
- Glass icon button — click to slide open input (210px), click again or click-outside to collapse
- Escape key also closes
- Unified border on outer wrapper (`.relic-search-expand`), `border-radius: 20px`
- Mobile: tier pills scroll horizontally (no wrap + `overflow-x: auto`)
- `-webkit-tap-highlight-color: transparent` on tier pills for mobile active state
- **Known issue: search input text vertical centering is not resolved.** Text appears pushed up inside the pill. Multiple attempts made — `panels.css` global `input[type=text]` rule with `border-radius`, `border`, `box-shadow`, `padding: 8px 10px` keeps fighting the override. Next session should investigate this more carefully — try `!important` on padding or move search to a standalone input not fighting global rules.

### Reliquary Pagination
- **Relic count moved** from controls row to below the paginator
- Count now rendered inside `renderPagination()` as `"1–50 of 347 relics"` below the controls
- **Prev/Next restyled** — Rajdhani font + chevron SVGs + `surface2` background, matches UI language
- Scroll-to-top on page change **kept** (`.factions-wrap scrollTop = 0`)
- `pagination-preview.html` added to `web/static/` as a design reference (can be deleted)

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables
web/static/layout.css      # shared dot bg on .content/.live-wrap/.factions-wrap
web/static/panels.css      # .panel, global input[type=text] styles (CAUTION: fights search input)
web/static/live.css        # live page — invasion reward-chip faction colors
web/static/factions.css    # faction roster
web/static/reliquary.css   # all reliquary styles — controls, search pill, tier seg, pagination
web/static/js/reliquary.js # filter state, search toggle, renderGrid, renderPagination
web/static/js/worldstate-parser.js  # SORTIE_MODIFIERS, MT_MISSION_TYPES lookups
scripts/parse_worldstate.py         # _NW_NAMES, _NW_DESCRIPTIONS, SORTIE_MODIFIERS, MT_MISSION_TYPES
```

---

## Current State — Themes
```
stalker  (default, no class)   bg: #0a0a0a   surface: #121212   accent: #8b0000 → #e53e3e
jade     body.theme-jade        bg: #080808   surface: rgba(10,18,16,0.85)   accent: #00897b → #00e5c8
ash      body.theme-ash         bg: #080808   surface: rgba(16,16,16,0.85)   accent: #466482 → #7393b3
```

---

## Pending / Known Issues
- **Search input text vertical centering** — unresolved. `panels.css` global `input[type=text]` rule (border, border-radius, padding: 8px 10px, box-shadow) overrides are tricky. Try `!important` or refactor the input to not be `type=text`.
- **Pagination scroll-to-top** — intentional but user may revisit. Option 2 (sticky bar) or Option 3 (floating arrows) were discussed but not implemented.
- **pagination-preview.html** — throwaway file in `web/static/`, can be deleted.
- **Drop location data** — not in `Module:Void/data`. Requires separate wiki module.
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **Enkaus weapon** — re-run data refresh once wiki module is updated.
- **URL state / sharing** — high-value missing feature (no work started).

---

## Git Notes
- Working branch: `claude/continue-documentation-l3g96`
- User is on branch `codex` locally on Windows — merge with:
  ```
  git fetch origin
  git merge origin/claude/continue-documentation-l3g96
  ```
- `&&` not supported in Windows PowerShell — run git commands separately
