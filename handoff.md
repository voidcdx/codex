# Void Codex — Session Handoff

## Session summary
Added the Faction Weakness Cheatsheet page (`/factions`) — a new standalone page with a full matrix and cards view for all faction/damage-type effectiveness data. Also fixed attack mode tab styling (gradient underline + neon text-shadow glow).

---

## Changes made this session

### Faction Weakness Cheatsheet (`/factions`)
- `web/static/factions.html` — new page; same shell as live.html; sidebar nav "Factions" item active
- `web/static/factions.css` — matrix grid layout (sticky faction column, element-color cells), cards grid, filter pills, search, responsive breakpoints
- `web/static/js/factions.js` — renders matrix + cards from `FACTION_EFFECTIVENESS` / `ELEM_COLORS` / `DMG_ICONS`; filter (All/Vulnerable/Resistant), search, Matrix↔Cards toggle, row/col hover highlights
- `web/api.py` — added `GET /factions` route
- `web/static/index.html` + `web/static/live.html` — Factions nav-item added to sidebar

### Attack tab fix
- `web/static/results.css` — active attack tab: gradient underline via `background-image` trick + `text-shadow` neon glow; removed old box border and hardcoded amber rgba

### Changelog
- `CHANGELOG.md` + `CHANGELOG_ENTRIES` in `constants.js` — entries added under 0.5.3

---

## Design system rules (ENFORCE THESE)

| Rule | Detail |
|---|---|
| No hardcoded `rgba()` | Always use CSS variables |
| No `style=` inline attrs | Extract to CSS classes (SVG attrs + CSS custom property `--elem-color` via `style.setProperty()` excepted) |
| No rounded corners | `--radius: 0`, `--radius-sm: 0` everywhere |
| No glassmorphism | `backdrop-filter` on `#050505` is invisible. Rejected 5+ times. Do not retry. |
| No `▶` in CSS `content:` | Renders as emoji on iOS. Use `→` (U+2192) |
| No native `<select>` | Use `setupSelectDropdown()` — native renders as iOS picker |
| Element colors | Game-data colors (`ELEM_COLORS`) set via `el.style.setProperty('--elem-color', ...)` — CSS uses `var(--elem-color)`. Not inline style attrs. |

**CSS variable reference:**
`--bg` `--surface` `--surface-solid` `--surface2` `--border` `--border-highlight` `--border-red` `--accent` `--accent2` `--accent-glow` `--text` `--text-field` `--text-dim` `--crimson` `--crimson-bright` `--crimson-glow` `--riven`

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
- Branch: `claude/review-handoff-IMvk9`
- Version: `0.5.3`
- Game data: Update 41 — The Old Peace
- Tests: 297 passing
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

- [ ] Run `pytest` — confirm 297 passing
- [ ] `git log --oneline -5` to orient
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism / `▶` in CSS
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
