# Void Codex — Session Handoff

## Session summary
UI/UX pass: improved panel visibility with local-glow glassmorphism, fluid typography (clamp + rem), layout tweaks (mods panel repositioned, options collapsed by default), help text readability, crimson tooltip theme, mobile horizontal scroll fix, and armor strip label fix.

---

## Changes made this session

### Panel glassmorphism (local-glow pattern)
- `web/static/base.css` — `--surface` changed to `rgba(18,10,10,0.50)` (was `#181818` solid), `--surface2` to `rgba(12,6,6,0.55)`, `--surface-solid: #201818`
- `web/static/base.css` — `--panel-glow: rgba(139, 0, 0, 0.13)` added (NEW variable)
- `web/static/panels.css` — `.panel::after` now renders a local radial glow halo (`inset: -24px; background: radial-gradient(...var(--panel-glow)...); z-index: -1`) giving `backdrop-filter` something to work with per panel

**Key insight:** `backdrop-filter` on `#050505` blurs nothing (no content behind it). Solved by making each panel generate its own crimson atmosphere behind itself via `::after`. Semi-transparent surface (`rgba`) then blurs that glow.

### Fluid typography
- `web/static/base.css` — `body { font-size: clamp(13px, 1.1vw, 16px) }` (was 14px fixed)
- All text sizes across `panels.css` and `results.css` converted from `px` to `rem` so they scale proportionally with the body font

### Layout changes
- `web/static/index.html` — Mods panel moved from `.content-side` to `.content-main` (now below weapon/enemy grid)
- `web/static/index.html` — Options panel collapsed by default (removed `open` class from h2, added `hidden` to `options-body`)

### Help panel readability
- `web/static/panels.css` — `.panel-help { color: var(--text) }` (was `var(--text-dim)` = #666666 — too dark against `--surface-solid: #201818`)

### Crimson tooltip theme
- `web/static/results.css` — `.tippy-box[data-theme~='warframe']` restyled:
  - `background: rgba(28,10,10,0.97)` (dark crimson-black)
  - `border: 1px solid var(--border-red)`
  - `color: var(--text-primary)`
  - `font-size: 0.8rem`
  - `.tippy-arrow` color matches new background

### Mobile horizontal scroll fix
- `web/static/base.css` — `html { overflow-x: hidden }` added
- Root cause: `.panel::after { inset: -24px }` extends 24px past every panel edge including left/right

### Armor strip label fix
- `web/static/panels.css` — `.strip-label { font-size: 0.67rem }` (was hardcoded `10px`)
- Also fixed: `.strip-pct-badge`, `.strip-result-label`, `.strip-result-val`, `.strip-bar-label-left/right`

### Green dropdown fix
- `web/static/panels.css` — Two instances of `rgba(5, 9, 4)` (R=5, G=9, B=4 → green tint) fixed to `rgba(5, 5, 5)`:
  - `.combobox-dropdown` (line ~262)
  - `.mod-picker` (line ~588)

### Changelog
- `CHANGELOG.md` — Added `[Unreleased]` entry documenting all session changes
- `web/static/js/constants.js` — Added matching entry to `CHANGELOG_ENTRIES`

---

## Design system rules (ENFORCE THESE)

| Rule | Detail |
|---|---|
| No hardcoded `rgba()` | Always use CSS variables |
| No `style=` inline attrs | Extract to CSS classes (SVG attrs + CSS custom property `--elem-color` via `style.setProperty()` excepted) |
| No rounded corners | `--radius: 0`, `--radius-sm: 0` everywhere |
| No glassmorphism WITHOUT local glow | `backdrop-filter` on `#050505` is invisible. Use the `.panel::after` local-glow pattern. |
| No `▶` in CSS `content:` | Renders as emoji on iOS. Use `→` (U+2192) |
| No native `<select>` | Use `setupSelectDropdown()` — native renders as iOS picker |
| No green UI accents | `--accent-green` maps to crimson. Only game-data colors stay green. |
| Element colors | Game-data colors (`ELEM_COLORS`) set via `el.style.setProperty('--elem-color', ...)` — CSS uses `var(--elem-color)`. Not inline style attrs. |
| Font sizes | Use `rem` for text content sizes. `px` only for structural/icon sizes. Body uses `clamp(13px, 1.1vw, 16px)`. |

**CSS variable reference:**
`--bg` `--surface` `--surface-solid` `--surface2` `--border` `--border-highlight` `--border-red` `--accent` `--accent2` `--accent-glow` `--panel-glow` `--text` `--text-field` `--text-dim` `--text-primary` `--crimson` `--crimson-bright` `--crimson-glow` `--riven`

---

## CSS class inventory

| Class | File | Purpose |
|---|---|---|
| `.panel-sub-h` | panels.css | Section heading divider |
| `.btn-add` | panels.css | `+ ADD` button |
| `.btn-help` | panels.css | `?` help toggle (crimson, no border) |
| `.panel-help` / `.panel-help.hidden` | panels.css | Inline help block; hidden by default |
| `.panel-toggle-with-help` | panels.css | Transfers auto-margin from chevron to btn-help |
| `.input-sm` | panels.css | Compact 44px number input |
| `.input-sm-wide` | panels.css | Compact 52px number input |
| `.input-level` | panels.css | 72px enemy level input |
| `.sel-wrap` | panels.css | Wrapper for themed select dropdown |
| `.sel-btn` | panels.css | Trigger button for themed select |
| `.sel-dropdown` | panels.css | Dropdown container (extends `.combobox-dropdown`) |
| `.combobox-item.sel-selected` | panels.css | Highlighted selected option |
| `.strip-row` / `.strip-label-row` | panels.css | Armor strip panel row layout |
| `.strip-slider` | panels.css | Range input (crimson thumb, no border-radius) |
| `.strip-result-block` / `.strip-bar-fill` | panels.css | Armor/DR summary + progress bar |
| `.sc-wrap` | results.css | Two-column weapon stat split |
| `.sc-div` | results.css | Crimson vertical divider |
| `.sc-val-lg` / `.sc-val-sm` | results.css | Large/small stat values |
| `.sc-modded` | results.css | Modded value row (`→` prefix) |
| `.attack-tab` | results.css | Multi-attack mode tab; gradient underline + neon glow on `.active` |
| `.faction-matrix` | factions.css | CSS grid: `170px repeat(13, minmax(68px, 1fr))` |
| `.matrix-row-label` | factions.css | Sticky left faction column, z-index 2 |
| `.matrix-col-header` | factions.css | Damage type column header |
| `.matrix-cell` / `.cell-weak` / `.cell-resist` | factions.css | Data cell variants |
| `.faction-cards-wrap` | factions.css | Cards grid: `repeat(auto-fill, minmax(280px, 1fr))` |
| `.faction-card` | factions.css | Per-faction card (also uses `.panel`) |
| `.dmg-badge` / `.badge-weak` / `.badge-resist` | factions.css | Inline element badges |
| `.filter-pill` / `.filter-pill.active` | factions.css | All/Vulnerable/Resistant filter buttons |

---

## Known issues / pending

- Refresh `weapons.json` + `mods.json` via wiki ApiSandbox (27 MEDIUM 100.0 placeholder issues remain)
- Arcane Crepuscular, Tenacious Bond, Shroud of Dynar absolute CD bonuses (low priority)
- Cycles + Events not yet rendered in `live.html` (data parsed, cards not built)
- Riven modal — not touched recently. Get screenshot before changing.

---

## Feature backlog

1. Side-by-side Build Compare (panel hidden, placeholder exists)
2. Mod Optimizer — brute-force best mod per slot
3. Damage Falloff
4. EHP Calculator (needs Warframe DB)
5. Status Simulator (needs research — complex proc weighting)
6. Build Cards (export image)
7. Build Sharing (URL-encoded state)
8. Live Data — Cycles + Events cards

---

## Current state
- Branch: `claude/review-handoff-notes-pszW5`
- Version: `0.5.3`
- Game data: Update 41 — The Old Peace
- Tests: 294 passing
- Railway deploy branch: `codex`

## Private notes
`accuracy-notes.md` — accuracy self-assessment (what the calculator gets right, where the gaps are). In repo, deletable any time. Read on request.

---

## Start-of-session checklist

> **Ask at HANDOFF, not session start:**
> 1. "Should I bump the version? Current: `0.5.3`"
> 2. "Should this session be tracked in the changelog?"
> Do NOT auto-bump or add entries without confirmation.
> Update BOTH `CHANGELOG.md` AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 294 passing
- [ ] `git log --oneline -5` to orient
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism without local glow / `▶` in CSS
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
