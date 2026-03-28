# Void Codex — Session Handoff

## Session summary
Live page work: refactored Void Fissures filter tabs from tier-based to
gameplay category tabs (Origin System / Steel Path / Requiem / Railjack),
updated tier badge colors, fixed open world cycles (added Earth epoch formula,
Duviri API read, moved Zariman to epoch-based), replaced _parse_cycles with
cleaner epoch-formula approach for Cetus/Vallis/Cambion, and enforced
wiki.warframe.com as sole data source in CLAUDE.md.

---

## Changes made this session

### CLAUDE.md
- Added hard rule: `wiki.warframe.com` is the **only** permitted source for
  all Warframe game data, constants, formulas, and scraping. No third-party
  community tools, GitHub repos, or other external sources.

### scripts/parse_worldstate.py
- `_parse_fissures()`: added `expiry_ts` field (Unix timestamp float) for
  frontend sort-by-ETA
- `_parse_cycles()`: full replacement with cleaner epoch-formula blocks:
  - Cetus: epoch=1510444800, cycle=8998s, day=5998s
  - Orb Vallis: epoch=1542318000, cycle=1600s, warm=400s
  - Cambion Drift: epoch=1604085600, cycle=8998s, fass=4499s
  - **Earth (new)**: epoch=0, cycle=14400s, day=10800s, night=3600s
  - **Duviri (new)**: reads `DuviriCycle` from raw worldstate API
  - Zariman: reads `ZarimanCycle` from raw worldstate API

### web/static/live.css
- `.tier-btn`: replaced bordered pill style with underline-gradient tabs
  matching `.attack-tab` (0.85rem body font, crimson gradient, text-shadow
  glow on active, no border)

### web/static/live.html (inline JS)
- `TIER_COLORS`: Lith=`#b87333`, Meso=`#00bcd4`, Neo=`#3949ab`,
  Axi=`#ffd700`, Requiem=`#8b0000`, Omnia=`#e0e0e0`
- Fissure filter: `activeTier` → `activeCategory`; added `getFissureCategory()`
  (origin / steelpath / requiem / railjack based on `is_storm`, `is_steel_path`,
  `tier`); `setTier()` → `setCategory()`; removed "All" tab; default = `'origin'`
- `renderFissureRows()`: filters by category, sorts by `expiry_ts` ascending
- `buildFissureCard()`: 4 tabs — Origin System / Steel Path / Requiem / Railjack
- `buildCyclesCard()`: added `Joy`, `Anger` to WARM set for Duviri styling

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
| Data sources | **wiki.warframe.com ONLY** — no third-party sources for any game data, constants, or formulas |

**CSS variable reference:**
`--bg` `--surface` `--surface-solid` `--surface2` `--border` `--border-highlight` `--border-red` `--accent` `--accent2` `--accent-glow` `--panel-glow` `--text` `--text-field` `--text-dim` `--text-primary` `--crimson` `--crimson-bright` `--crimson-glow` `--riven`

---

## Live page typography scale (established — do not regress)

| Tier | Size | Classes |
|---|---|---|
| Panel headings | 1rem Orbitron | `.panel h2` (global, panels.css) |
| Primary row data | 1rem Rajdhani | `.fissure-node`, `.mission-node`, `.trader-location`, `.nw-title`, `.alert-reward`, `.invasion-node`, `.event-title`, `.cycle-state`, `.sortie-boss` |
| Secondary text / ETAs | 0.85rem | `.fissure-sub`, `.mission-sub`, `.trader-eta`, `.nw-eta`, `.alert-sub`, `.invasion-factions`, `.cycle-eta`, `.event-desc`, `.live-eta`, `.eta-chip` |
| Tags / badges / buttons | 0.73rem | `.fissure-tier`, `.fissure-tag`, `.nw-tag`, `.modifier-badge`, `.reward-chip`, `.invasion-vs`, `.live-count`, `.refresh-btn`, `.news-section-label` |
| Micro labels | 0.67rem | `.news-section-label` (section category labels) |

### Fissure category tab style (`.tier-btn`)
Matches `.attack-tab` in `results.css`: borderless, 0.85rem body font,
`background: transparent no-repeat bottom / 0% 2px`, hover slides in crimson
gradient underline, active adds text-shadow glow. No `--tier-color` on tabs.

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
| `.attack-tab` | results.css | Multi-attack mode tab (underline-gradient style) |
| `.riven-header-icon` | riven.css | 20px crimson hex icon in riven editor header |
| `.riven-mod-name` | riven.css | "Riven" label on mod card — crimson |
| `.riven-stat-pos` | riven.css | Positive stat on riven card — white |
| `.riven-stat-neg` | riven.css | Negative stat on riven card — red |
| `.faction-matrix` | factions.css | CSS grid: `170px repeat(13, minmax(68px, 1fr))` |
| `.dmg-badge` / `.badge-weak` / `.badge-resist` | factions.css | Inline element badges |
| `.filter-pill` / `.filter-pill.active` | factions.css | All/Vulnerable/Resistant filter buttons |

---

## Known issues / pending

- **SolNode45** — appears as "Node45 (Sol)" in live fissure data; unknown what node this is
- **Railway 403** — `api.warframe.com/cdn/worldState.php` blocked from Railway's cloud IP. Duviri and Zariman cycles won't display on Railway (Earth/Cetus/Vallis/Cambion always work — epoch formula). Live data works on localhost. Consider Cloudflare Worker proxy if block remains long-term.
- Refresh `weapons.json` + `mods.json` via wiki ApiSandbox (27 MEDIUM 100.0 placeholder issues remain)
- Arcane Crepuscular, Tenacious Bond, Shroud of Dynar absolute CD bonuses (low priority)

---

## Feature backlog

1. Side-by-side Build Compare (panel hidden, placeholder exists)
2. Mod Optimizer — brute-force best mod per slot
3. EHP Calculator (needs Warframe DB)
4. Status Simulator (needs research — complex proc weighting)
5. Build Cards (export image)
6. Build Sharing (URL-encoded state)
7. Live Data — surface worldstate on main calculator page (fissure banner? void trader alert?)

---

## Current state
- Branch: `claude/review-handoff-w0wqr`
- Version: `0.5.5`
- Game data: Update 41 — The Old Peace
- Tests: 304 passing
- Railway deploy branch: `codex`

## Private notes
`accuracy-notes.md` — accuracy self-assessment (what the calculator gets right, where the gaps are). In repo, deletable any time. Read on request.

---

## Start-of-session checklist

> **Ask at HANDOFF, not session start:**
> 1. "Should I bump the version? Current: `0.5.5`"
> Changelog tracking deferred until v1.0.0 — do not ask about it.

- [ ] Run `pytest` — confirm 304 passing
- [ ] `git log --oneline -5` to orient
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism without local glow / `▶` in CSS / Share Tech Mono / purple in UI
- [ ] Update Guide modal when adding UI features
- [ ] **wiki.warframe.com ONLY** for all game data — no third-party sources ever
- [ ] **Railway deploy** — after every `git push` to the feature branch, immediately run:
  ```bash
  git checkout codex && git merge <feature-branch> --no-ff && git push -u origin codex && git checkout <feature-branch>
  ```
  Never leave the session without doing this — do NOT make the user merge manually.
