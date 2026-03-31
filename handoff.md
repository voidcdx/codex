# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.6.0`
**Branch:** `claude/continue-claude-implementation-84uTe`

---

## What Was Done This Session

### Theme System — Void Ash accent finalized
- Ash accent color decided and applied: **`#7393b3`** (steel blue)
- All alpha steps, border variants, glow, and panel lines updated in `body.theme-ash` block
- Comment updated: "Void Ash (steel blue #7393b3)"

### Panel System Refactor
- Split `--panel-line-color` into `--panel-line-top` + `--panel-line-bottom` (asymmetric — bright top, dim bottom) for all themes
- Stalker: top `rgba(229,62,62,0.65)`, bottom `rgba(139,0,0,0.35)`
- Jade: top `rgba(0,160,130,0.55)`, bottom `rgba(0,120,100,0.30)`
- Ash: top `rgba(115,147,179,0.55)`, bottom `rgba(85,115,145,0.28)`
- Removed top gradient line from panels (only bottom line remains)
- Removed `.mod-picker::after` radial glow
- Fixed `.mod-picker::before` to use new `--panel-line-top`/`--panel-line-bottom` variables

### Header
- Removed `border-bottom` from `.header` (was thin accent line across full width)
- Added `border-radius: 0 0 0 12px` (bottom-left only) to `.header` — all themes
- Added `::after` centered gradient line at header bottom — all themes, uses `--panel-line-top`
- Stalker `--surface` changed to solid `#121212` (was `rgba(18,18,18,0.85)` — useless on black bg)
- Ash `--header-bg` changed to solid `#0d0d0d` (was `rgba(8,8,8,0.90)`)
- Jade `--bg` changed to `#080808` to match Ash

### Dropdowns
- All `--dropdown-bg` values changed to solid hex (were `rgba(...,0.97)`)
- Removed `backdrop-filter: blur` from `.combobox-dropdown`

### Mobile Fixes
- Theme switcher hidden in header on ≤900px
- Theme switcher added to sidebar footer on all 3 pages — 20px dots, `touch-action: manipulation`
- Mobile sidebar background overridden to `var(--surface-solid)` (#141414) — was near-invisible on black page

### Mod Grid / Picker
- Removed `border-style: dashed` from `.mod-card.empty` (solid border only now)

### Sidebar Consistency
- All 3 pages (live, calculator, factions) now have identical sidebar footer:
  - Mobile theme switcher row (`sidebar-theme-switcher`)
  - `#nav-ver` version
  - Copyright lines with `sidebar-footer-copy` class (Rajdhani font, normal case)
- Factions: removed SVG brand icon from sidebar (matched live/calc — text only)
- Calculator: `sidebar-footer-copy` class added to copyright lines

### Live Page
- Removed refresh button and timer display entirely
- `resetCountdown()` simplified to `setTimeout(loadData, 180000)` — auto-refresh still works silently
- Removed dead `countdownVal` variable

### Panel Title
- Removed `border-bottom` from `.panel h2` (all panel titles now borderless)

### Gift of Lotus rows
- Changed from radial glow to linear gradient: `linear-gradient(90deg, var(--accent-a12) 0%, var(--accent-a6) 40%, transparent 100%)`

---

## Current State — Themes

```
stalker  (default, no class)   bg: #0a0a0a   surface: #121212   accent: #8b0000 → #e53e3e
jade     body.theme-jade        bg: #080808   surface: rgba(10,18,16,0.85)   accent: #00897b → #00e5c8
ash      body.theme-ash         bg: #080808   surface: rgba(16,16,16,0.85)   accent: #466482 → #7393b3
```

## CSS File Map
```
web/static/base.css       # :root (Stalker) + body.theme-jade + body.theme-ash — all CSS variables
web/static/layout.css     # .header, .sidebar, .brand, .theme-switcher, .sidebar-footer, mobile media
web/static/panels.css     # .panel, .panel::before, .mod-grid, .mod-card, .mod-picker, dropdowns
web/static/live.css       # live page only — event rows, cycles, fissures, news/events panel
web/static/results.css    # .btn-calc, result display
web/static/responsive.css # breakpoint overrides
web/static/js/theme.js    # applyTheme(), initTheme(), localStorage key: 'void-theme'
```

---

## Pending

- Enkaus weapon: re-run data refresh once wiki module is updated
- Debug endpoints (`/api/worldstate/debug-*`) can be removed once live data is stable
- `theme-preview.html` has a subtext color preview section (`#7393b3 Blue`) that can be cleaned up

---

## Git Notes
- Working branch: `claude/continue-claude-implementation-84uTe`
- User is on branch `codex` locally on Windows — they merge from the claude branch
