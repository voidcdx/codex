# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/continue-handoff-docs-dF4Zj`

---

## What Was Done This Session

### CSS Consistency Pass
- **`--radius` token unified** — bumped to `8px` (was `4px`), `--radius-sm` to `4px` (was `3px`). `.panel` and `.cycles-standalone` now use `var(--radius)` instead of hardcoded `8px`. All cards (relic, modal, riven) consistent.
- **Dot background centralized** — `radial-gradient(circle, var(--accent-a18) 1px, transparent 1px) / 20px 20px` moved from `.live-grid` to `layout.css` targeting `.content, .live-wrap, .factions-wrap`. All pages get it automatically.
- **Relic cards match panels** — `.relic-card` updated to use `var(--surface)`, `backdrop-filter`, and `::before` gradient accent lines (same as `.panel`).
- **Roster entries rounded** — `.roster-entry` on factions page now has `border-radius: var(--radius)`.
- **`cycles-standalone::before`** — fixed stale `--panel-line-color` reference → `--panel-line-top`/`--panel-line-bottom`.

### Reliquary Layout Fixes
- **Mobile overflow fixed** — `overflow-x: hidden` on `.factions-wrap`; horizontal padding moved directly to `.relic-controls` (28px desktop / 16px mobile) and `.relic-grid` (same) instead of relying on `.factions-wrap` padding cascade.
- **Mobile sidebar drawer** — `toggleDrawer()` was using `.visible` class on overlay; fixed to `.open` (matches `layout.css`).
- **Duplicate `id="relic-count"`** — removed from search row, kept in filter row.
- **Favicon** — added to `factions.html` and `reliquary.html` (was only on `calculator.html`).

### Reliquary Pagination
- **50 relics per page** with `← Prev / Page N of M / Next →` controls.
- **Default to Unvaulted** — `activeVault = 'unvaulted'` on load; Unvaulted button pre-selected.
- Count label shows range: `1–50 of 347`.
- Any filter/search change resets to page 1.
- Next/Prev scrolls `.factions-wrap` to top.
- Pagination bar hidden when results fit on one page.

### CLAUDE.md Updates
- Added **new page checklist** to CSS rules: dot bg, favicon, sidebar nav, `Cache-Control: no-store` in api.py.

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables incl. --radius:8px, --radius-sm:4px
web/static/layout.css      # shared dot bg on .content/.live-wrap/.factions-wrap
web/static/panels.css      # .panel (uses var(--radius)), .panel::before gradient lines
web/static/live.css        # live page — dot bg removed (now in layout.css)
web/static/factions.css    # .factions-wrap, .roster-entry (now rounded)
web/static/reliquary.css   # relic cards, pagination, mobile layout
web/static/reliquary.css:  #   .relic-card matches .panel style
                           #   .relic-controls/.relic-grid own their horizontal padding
                           #   .relic-pagination — Prev/page-info/Next bar
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
- **Drop location data** — not present in `Module:Void/data`. Would require scraping a separate wiki module.
- **27 placeholder weapons** — have fake IPS values in `data/weapons.json`.
- **Enkaus weapon** — re-run data refresh once wiki module is updated.
- **URL state / sharing** — high-value missing feature (no work started).

---

## Git Notes
- Working branch: `claude/continue-handoff-docs-dF4Zj`
- User is on branch `codex` locally on Windows — merge with:
  ```
  git fetch origin
  git merge origin/claude/continue-handoff-docs-dF4Zj
  ```
- `&&` not supported in Windows PowerShell — run git commands separately
