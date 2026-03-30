# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional.

**Version:** `0.5.8`
**Branch:** `claude/review-handoff-md-D3h2l` — last commit `d084b1a`

---

## What Was Done This Session

### 1. Shared brand header across all pages
- `.live-header-brand` + `.live-subtext` + glitch keyframes moved from `live.css` → `layout.css` (shared by all pages)
- `index.html` (calculator): header now shows `VOID CODEX` / `DAMAGE CALCULATOR` with glitch subtext
- `factions.html`: header now shows `VOID CODEX` / `FACTION WEAKNESS` with glitch subtext
- `live.html` (live tracker): already had the structure, unchanged

### 2. File rename + route restructure
- `live.html` → `index.html` (live tracker is now the default page)
- `index.html` → `calculator.html`
- Routes in `web/api.py`:
  - `GET /` → `index.html` (live tracker)
  - `GET /live` → `index.html` (same, alias)
  - `GET /calculator` → `calculator.html`
  - `GET /factions` → `factions.html`
- Nav links updated across all pages — Calculator links point to `/calculator`

### 3. Weapon/Enemy picker — modal overlay
- Replaced inline combobox search bars with a magnifier icon button in each panel h2 (right-aligned via `margin-left: auto`)
- Clicking the icon opens a centered modal overlay (`#item-picker-overlay`) reusing `.mod-picker-overlay` / `.mod-picker` styling
- Modal has dynamic title (SELECT WEAPON / SELECT ENEMY), search input, scrollable item list with weapon images
- ESC, click-outside, and touch all close the modal
- `#weapon-search` and `#enemy-search` kept as hidden inputs — all existing JS (`getCurrentWeapon()`, `getCurrentEnemy()`, `calculate.js`) reads `.value` unchanged
- New functions in `combobox.js`: `setupPickerModal()`, `openPickerModal()`, `closePickerModal()`, `renderPickerResults()`
- `app.js` updated to call `setupPickerModal` instead of `setupCombobox` for weapon/enemy

### 4. Weapon/Enemy split into separate panels (mobile fix)
- Previously: one `.panel` containing `.we-grid > .we-col × 2`
- Now: `.we-panel-row` containing two independent `.panel` divs
- Desktop: side by side (`grid-template-columns: 1fr 1fr`, `gap: 12px`)
- Mobile ≤600px: stacks to 1 column — weapon first, enemy second (DOM order)
- Fixes mobile layout where enemy header was flush against weapon stats with no visual separation
- Old `.we-grid` / `.we-col` CSS removed from `panels.css`

---

## Pending / TODO

- Nothing critical. UI is in good shape.
- Potential: review calculator page on mobile end-to-end now that panels are split

---

## Key Files Changed This Session
- `web/api.py` — route definitions
- `web/static/index.html` — live tracker (was live.html)
- `web/static/calculator.html` — damage calculator (was index.html)
- `web/static/factions.html` — faction weakness page
- `web/static/layout.css` — shared brand/glitch styles
- `web/static/live.css` — duplicate brand styles removed
- `web/static/panels.css` — we-panel-row replaces we-grid/we-col; picker-open-btn; item-picker-item
- `web/static/js/combobox.js` — setupPickerModal + modal functions
- `web/static/js/app.js` — switched to setupPickerModal for weapon/enemy
- `src/version.py` — bumped to 0.5.8

---

## Git Notes
- Working branch: `claude/review-handoff-md-D3h2l`
- Commits are pushed to remote; user merges to main on their Windows machine
