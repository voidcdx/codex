# Void Codex — Session Handoff

## Session summary
Two sessions of worldstate work. `scripts/parse_worldstate.py` is now fully
populated with lookup tables and all parsing functions use them. Verified live
output on localhost — fissures, invasions, sortie, void trader, cycles all
resolve to human-readable names.

---

## Changes made this session

### parse_worldstate.py — lookup tables + parsing
- `FISSURE_TIERS`: VoidT5→Requiem, VoidT6→Omnia added
- `MT_MISSION_TYPES`: 33-entry dict for raw `MT_*` mission keys
- `SORTIE_BOSSES`: 19 bosses
- `SORTIE_MODIFIERS`: 29 modifiers
- `BOSS_FACTION`: 20-entry dict — sortie faction derived from boss key when raw Faction field is empty
- `ALL_NODES`: ~290 entries across all planets, proxima, relays, Zariman, Deimos, Duviri
- `NODE_FACTION`: parallel dict (node key → faction) used as fallback in `_parse_fissures`
- `ITEM_NAMES`: 80 paths → display names
- `_parse_fissures`: enemy field populated via NODE_FACTION fallback
- `_parse_invasions`: fixed field names (Faction/DefenderFaction/AttackerReward/DefenderReward); `_reward()` returns `""` not `"Unknown"` for empty rewards
- `_parse_sortie`: faction derived from BOSS_FACTION when raw Faction is empty
- `_mission_type()`: checks MT_MISSION_TYPES first, then MISSION_TYPES

### Node corrections
- SolNode153: was "Seimeni (Ceres)" / Infested → "Coba (Sedna)" / Grineer
- SolNode181: was "Helene (Saturn)" / Grineer → "Cinxia (Ceres)" / Grineer
- SolNode718 / 744 / 747: added (Deimos / Murmur)
- SolNode230 / 232: added (Zariman / Corpus)

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

- **SolNode45** — appears as "Node45 (Sol)" in live fissure data; unknown what node this is
- **Railway 403** — `api.warframe.com/cdn/worldState.php` still blocked from Railway's cloud IP; server retries every 60s but always fails. Live data works on localhost. Consider Cloudflare Worker proxy if this remains blocked long-term.
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
7. Live Data — Cycles + Events cards (data parsed server-side, JS card builders exist but untested with real data)
8. Live Data — surface worldstate on main calculator page (fissure banner? void trader alert?)

---

## Current state
- Branch: `claude/review-handoff-dgOJU`
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
- [ ] **Railway deploy** — after every `git push` to the feature branch, immediately run:
  ```bash
  git checkout codex && git merge <feature-branch> --no-ff && git push -u origin codex && git checkout <feature-branch>
  ```
  Never leave the session without doing this — do NOT make the user merge manually.
