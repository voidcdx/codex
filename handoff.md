# Void Codex — Session Handoff

## Session summary
Implemented damage falloff feature (full stack: data pipeline → models → loader → calculator → API → UI), added falloff tooltip, fixed mobile sidebar layout (removed hexagon brand icon, aligned burger/X button).

---

## Changes made this session

### Damage Falloff — full stack implementation
- `scripts/parse_wiki_data.py` — `_parse_attack()` now extracts `Falloff` dict (`StartRange`, `EndRange`, `Reduction`) from raw wiki data
- `data/weapons.json` — regenerated; ~410/590 weapons now have `falloff_start`, `falloff_end`, `falloff_reduction` per attack
- `src/models.py` — added `falloff_start: float | None`, `falloff_end: float | None`, `falloff_reduction: float` to both `WeaponAttack` and `Weapon` dataclasses
- `src/loader.py` — reads falloff fields from JSON into models; copies selected attack's falloff to Weapon; includes falloff in `list_attacks()` API output
- `src/calculator.py` — `calculate_falloff_multiplier()` helper + `distance: float = 0.0` param on `calculate()`. Applied after multishot as `math.floor(v * multiplier)`. DoT procs unaffected.
- `web/api.py` — `distance` field on `CalcRequest`; passed to `calculate()` and CO curve calls; falloff fields in `GET /api/weapons` per-attack response
- `web/static/js/weapons.js` — displays `Falloff: 10–20m (20% min)` on weapon card when attack has falloff data; `data-tooltip="falloff"` added
- `web/static/js/constants.js` — `TOOLTIPS.falloff` added
- `web/static/js/calculate.js` — sends `distance` in POST body
- `web/static/index.html` — distance input in Options panel (hidden for weapons without falloff)
- `tests/test_calculator.py` — 10 new tests: falloff multiplier unit tests, integration with calculate(), no-falloff unchanged, procs unaffected

### Mobile sidebar layout fix
- `web/static/index.html` — removed `.brand-icon` hexagon SVG from sidebar brand area
- `web/static/layout.css` — removed `.burger-btn.open` position override (no movement on toggle); reduced mobile sidebar `padding-top: 10px` to align brand text with burger button at `top: 14px`

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

---

## Feature backlog

1. Side-by-side Build Compare (panel hidden, placeholder exists)
2. Mod Optimizer — brute-force best mod per slot
3. EHP Calculator (needs Warframe DB)
4. Status Simulator (needs research — complex proc weighting)
5. Build Cards (export image)
6. Build Sharing (URL-encoded state)
7. Live Data — Cycles + Events cards

---

## Current state
- Branch: `claude/review-handoff-nElCt`
- Version: `0.5.4`
- Game data: Update 41 — The Old Peace
- Tests: 304 passing
- Railway deploy branch: `codex`

## Private notes
`accuracy-notes.md` — accuracy self-assessment (what the calculator gets right, where the gaps are). In repo, deletable any time. Read on request.

---

## Start-of-session checklist

> **Ask at HANDOFF, not session start:**
> 1. "Should I bump the version? Current: `0.5.4`"
> Changelog tracking deferred until v1.0.0 — do not ask about it.

- [ ] Run `pytest` — confirm 304 passing
- [ ] `git log --oneline -5` to orient
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism without local glow / `▶` in CSS / Share Tech Mono / purple in UI
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
