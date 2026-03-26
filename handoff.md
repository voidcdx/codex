# Void Codex — Session Handoff

## Session summary
Removed Shattering Impact from the Armor Strip panel entirely. It was rarely used and added unnecessary complexity. Also completed the panel help (?) system and cleaned up all SI references across the codebase.

---

## Changes made this session

### Shattering Impact removal
- `src/calculator.py` — removed `shattering_impact_flat` param and flat-subtraction block from Step 4
- `web/api.py` — removed `shattering_impact_flat` from `CalcRequest`, all forwarding calls removed
- `web/static/index.html` — SI row and help text removed from Armor Strip panel
- `web/static/js/armorstrip.js` — SI inputs, logic, and payload field removed
- `tests/test_armor_strip.py` — removed 4 SI test cases (`test_shattering_impact_flat`, `test_si_cannot_go_below_zero`, `test_all_combined`, cleaned `test_zero_armor_enemy_no_op`)
- `web/static/panels.css` — removed `.strip-si-row`, `.strip-si-field`, `.strip-si-sep`, `.strip-si-total`, `.strip-sublabel`

### Armor Strip panel (completed previous session, documented here)
Armor Strip models two inputs only:
- **Ability strip %** (0–100%) — Warframe ability-based strip (e.g. Seeking Shuriken, Tharros Strike)
- **Corrosive Projection %** (0–100%) — aura mod strip per player count

Both are additive, capped at 100%. Formula: `armor × (1 − min(1, ability_pct + cp_pct))`

### Panel help (?) system (completed previous session)
- `togglePanelHelp(btn)` in `utils.js` — finds `.panel-help` sibling of nearest h2/.panel-sub-h, toggles `.hidden`
- `.btn-help` in `panels.css` — crimson, no border, hover `var(--crimson-bright)`
- `.panel-help` / `.panel-help.hidden` in `panels.css`
- `.panel-toggle-with-help` modifier — transfers `margin-left: auto` from `.chevron` to `.btn-help`
- Help blocks added to: Results, Options, Warframe Buffs, Armor Strip, Mods, Weapon Arcanes panels

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
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism / `▶` in CSS
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
