# Void Codex — Session Handoff

## Session summary
UI polish pass: changelog removed, riven modal color overhaul (green/purple → crimson), results table alignment fixes, double-arrow bug, mobile header height + burger alignment.

---

## Changes made this session

### Changelog removed
- `CHANGELOG.md` deleted
- `CHANGELOG_ENTRIES` constant removed from `constants.js`
- What's New modal + nav buttons removed from `index.html`, `live.html`, `factions.html`
- `renderChangelog/openChangelog/closeChangelog` removed from `modals.js`
- All `.changelog-*` CSS removed from `modals.css`
- `CLAUDE.md`, `handoff.md`, `.claude/hooks/handoff-reminder.sh` updated accordingly
- **Tracking deferred until v1.0.0 — do not re-add**

### Riven modal — full color + UX overhaul
- `web/static/riven.css` — olive green (`--riven: #5a8a3a`) and purple (`#c49aff`, `rgba(155,109,208,0.25)`) fully replaced with crimson theme vars
- All hardcoded `rgba(139,0,0,...)` replaced with `color-mix(in srgb, var(--crimson) N%, transparent)` and `var(--border-highlight)`
- `.riven-stat-pos` / `.riven-stat-neg` classes added — positive stats white, negative red on mod card
- `web/static/js/weapons.js` — removed inline `style=` from editor hex icon (→ `.riven-header-icon`), removed `style="color:var(--riven)"` from card label (→ `.riven-mod-name`), removed `setTimeout` hack, added pos/neg stat class to card rendering
- `web/static/js/modals.js` — duplicate stat prevention (already-used stats greyed/unclickable in dropdown), viewport clamp on dropdown (flips above button if no room below, clamps left edge)

### Double-arrow bug fixed
- `web/static/js/weapons.js` — `.sc-modded::before` in CSS already injects `→`; JS was also prepending `'→ '` in `textContent`. Removed JS prefix from all 5 stats (multishot, fire rate, reload, magazine, max ammo).

### Results table
- Removed "Bar" column header — `calculate.js`
- Bar column shrinks 180px → 80px on mobile (≤520px) — `results.css`
- Last column (`th` + `td`) right-aligned — `results.css`
- Middle column (`th` + `td`) center-aligned (tbody only rule) — `results.css`
- TOTAL row changed from `colspan="2"` to proper 3 cells — `calculate.js`

### Mobile header
- `responsive.css` — `.header { padding: 14px 16px }` on ≤900px (was 16px 28px desktop)
- `.burger-btn { top: 5px }` on ≤900px — centers 38px burger in 48px header, clears browser chrome

---

## Design system rules (ENFORCE THESE)

| Rule | Detail |
|---|---|
| No hardcoded `rgba()` | Always use CSS variables or `color-mix()` |
| No `style=` inline attrs | Extract to CSS classes (SVG attrs + `el.style.setProperty('--elem-color', …)` excepted) |
| No rounded corners | `--radius: 0`, `--radius-sm: 0` everywhere |
| No glassmorphism WITHOUT local glow | `backdrop-filter` on `#050505` is invisible — use `.panel::after` local-glow pattern |
| No `▶` in CSS `content:` | Renders as emoji on iOS — use `→` (U+2192) |
| No native `<select>` | Use `setupSelectDropdown()` — native renders as iOS picker |
| No green UI accents | `--accent-green` maps to crimson. Only game-data colors stay green (`--riven`, Exilus slot, faction badges). |
| No Share Tech Mono | Orbitron + Rajdhani only |
| No purple in UI | No `#c49aff`, no `rgba(155,109,208,...)` — crimson theme only |
| Font sizes | `rem` for text. `px` only for icons/structural. `16px !important` iOS anti-zoom overrides are intentional — do not convert. |
| Bar widths | Set via `fill.style.width` in JS after innerHTML render — never inline HTML `style=` attribute |
| `.sc-modded` arrows | CSS `::before { content: '→ ' }` provides the arrow — never add it in JS `textContent` too |

**CSS variable reference:**
`--bg` `--surface` `--surface-solid` `--surface2` `--border` `--border-highlight` `--border-red` `--accent` `--accent2` `--accent-glow` `--panel-glow` `--text` `--text-field` `--text-dim` `--text-primary` `--crimson` `--crimson-bright` `--crimson-glow` `--riven`

---

## CSS class inventory

| Class | File | Purpose |
|---|---|---|
| `.threat-card` | panels.css | Enemy Threat Intel Card wrapper |
| `.threat-card-name` | panels.css | Enemy name — Orbitron 0.85rem 700 crimson |
| `.threat-badge-faction` | panels.css | Faction/health-type pill badges |
| `.threat-bar-row` | panels.css | Label + track + sub-label row |
| `.threat-bar-fill-hp/sh/ar/og` | panels.css | Gradient fills per stat type |
| `.panel-sub-h` | panels.css | Section heading divider |
| `.btn-add` | panels.css | `+ ADD` button |
| `.btn-help` | panels.css | `?` help toggle (crimson, no border) |
| `.panel-help` / `.panel-help.hidden` | panels.css | Inline help block; hidden by default |
| `.panel-toggle-with-help` | panels.css | Transfers auto-margin from chevron to btn-help |
| `.input-sm` | panels.css | Compact 44px number input |
| `.input-sm-wide` | panels.css | Compact 52px number input |
| `.input-level` | panels.css | 72px enemy level input |
| `.strip-row` / `.strip-label-row` | panels.css | Armor strip panel row layout |
| `.strip-slider` | panels.css | Range input (crimson thumb, no border-radius) |
| `.strip-result-block` / `.strip-bar-fill` | panels.css | Armor/DR summary + progress bar |
| `.sc-wrap` | results.css | Two-column weapon stat split |
| `.sc-val-lg` / `.sc-val-sm` | results.css | Large/small stat values |
| `.sc-modded` | results.css | Modded stat row — `::before` injects `→ ` arrow |
| `.attack-tab` | results.css | Multi-attack mode tab |
| `.riven-header-icon` | riven.css | 20px crimson hex icon in riven editor header |
| `.riven-mod-name` | riven.css | "Riven" label on mod card — crimson |
| `.riven-stat-pos` | riven.css | Positive stat on riven card — white |
| `.riven-stat-neg` | riven.css | Negative stat on riven card — red |
| `.faction-matrix` | factions.css | CSS grid: `170px repeat(13, minmax(68px, 1fr))` |
| `.dmg-badge` / `.badge-weak` / `.badge-resist` | factions.css | Inline element badges |
| `.filter-pill` / `.filter-pill.active` | factions.css | All/Vulnerable/Resistant filter buttons |

---

## Known issues / pending

- Refresh `weapons.json` + `mods.json` via wiki ApiSandbox (27 MEDIUM 100.0 placeholder issues remain)
- Arcane Crepuscular, Tenacious Bond, Shroud of Dynar absolute CD bonuses (low priority)
- Cycles + Events not yet rendered in `live.html` (data parsed, cards not built)
- Mobile header burger may still need fine-tuning — user was iterating on alignment at end of session

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
- Branch: `claude/review-handoff-notes-VhtlY`
- Version: `0.5.4`
- Game data: Update 41 — The Old Peace
- Tests: 294 passing
- Railway deploy branch: `codex`

## Private notes
`accuracy-notes.md` — accuracy self-assessment (what the calculator gets right, where the gaps are). In repo, deletable any time. Read on request.

---

## Start-of-session checklist

> **Ask at HANDOFF, not session start:**
> 1. "Should I bump the version? Current: `0.5.4`"
> Changelog tracking deferred until v1.0.0 — do not ask about it.

- [ ] Run `pytest` — confirm 294 passing
- [ ] `git log --oneline -5` to orient
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism without local glow / `▶` in CSS / Share Tech Mono / purple in UI
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
