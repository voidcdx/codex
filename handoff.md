# Void Codex — Session Handoff

## Session summary
Two-session UI pass: mobile scroll fix, enemy panel redesign (Threat Intel Card), full font-size standardization to a 7-step rem scale, Share Tech Mono removed, weapon/enemy name style unified.

---

## Changes made this session

### Mobile horizontal scroll fix
- `web/static/layout.css` — `overflow-x: hidden` on `.content`
- `web/static/live.css` — `overflow-x: hidden` on `.live-wrap`
- Root cause: `.panel::after { inset: -24px }` glow halos extend 24px past panel edges; `overflow-y: auto` on a parent promotes `overflow-x` from `visible` to `auto`, making them swipeable

### Enemy panel — Threat Intel Card
- `web/static/panels.css` — `.threat-card` block added; `.threat-card-name`, `.threat-badge-faction`, `.threat-bar-fill-hp/sh/ar/og` gradient fills
- `web/static/js/enemy.js` — fully rewritten; `showEnemyStats()` renders the card; `refreshEnemyScaling()` updates `#threat-bars` with live bars normalized to `Math.max(all bar values)`
- Bar widths are set via `fill.style.width` (JS property after innerHTML render — avoids inline HTML attribute rule)
- DR shown as `Math.round(armor / (armor + 300) * 100)%`

### Font standardization
7-step rem scale applied across **all** CSS files:

| px range | rem |
|---|---|
| 8–9px | 0.67rem |
| 10–11px | 0.73rem |
| 12–13px | 0.85rem |
| 14–15px | 1rem |
| 18px | 1.1rem |
| 24px | 1.5rem |

- Icon/structural sizes (×-buttons, emoji, iOS anti-zoom `16px !important`) kept as px
- Files touched: `panels.css`, `results.css`, `layout.css`, `factions.css`, `modals.css`, `live.css`, `riven.css`, `responsive.css`

### Share Tech Mono removed
- `panels.css` — `.btn-add` → `var(--font-display)`, `.btn-help` → `var(--font-body)`
- `live.css` — `code` element → plain `monospace`
- `matrix.js` — canvas font → `'Rajdhani', sans-serif`
- `index.html`, `live.html`, `factions.html` — removed from Google Fonts import URL

**Two fonts only going forward:** Orbitron (headings, names, values) · Rajdhani (body, labels, buttons)

### Name style unified
- `results.css` — `.weapon-stats-name` now matches `.threat-card-name`: `font-family: var(--font-display)`, `font-size: 0.85rem`, `font-weight: 700`, `letter-spacing: 0.5px`, `color: var(--crimson-bright)`

---

## Design system rules (ENFORCE THESE)

| Rule | Detail |
|---|---|
| No hardcoded `rgba()` | Always use CSS variables |
| No `style=` inline attrs | Extract to CSS classes (SVG attrs + `el.style.setProperty('--elem-color', …)` excepted) |
| No rounded corners | `--radius: 0`, `--radius-sm: 0` everywhere |
| No glassmorphism WITHOUT local glow | `backdrop-filter` on `#050505` is invisible — use `.panel::after` local-glow pattern |
| No `▶` in CSS `content:` | Renders as emoji on iOS — use `→` (U+2192) |
| No native `<select>` | Use `setupSelectDropdown()` — native renders as iOS picker |
| No green UI accents | `--accent-green` maps to crimson. Only game-data colors stay green. |
| No Share Tech Mono | Orbitron + Rajdhani only |
| Font sizes | `rem` for text. `px` only for icons/structural. `16px !important` iOS anti-zoom overrides are intentional — do not convert. |
| Bar widths | Set via `fill.style.width` in JS after innerHTML render — never inline HTML `style=` attribute |

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
| `.attack-tab` | results.css | Multi-attack mode tab |
| `.faction-matrix` | factions.css | CSS grid: `170px repeat(13, minmax(68px, 1fr))` |
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
- Branch: `claude/review-handoff-764d1`
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
> 2. "Should this session be tracked in the changelog?"
> Do NOT auto-bump or add entries without confirmation.
> Update BOTH `CHANGELOG.md` AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 294 passing
- [ ] `git log --oneline -5` to orient
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism without local glow / `▶` in CSS / Share Tech Mono
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
