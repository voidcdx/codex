# Void Codex — Session Handoff

## Session summary
Applied the Stalker/Shadow Acolyte visual design from `stalker-dashboard.html` to the calculator page (`index.html` + `style.css`). Layout is now: inner header + two-column content grid (calculator inputs left, results right) + right sidebar with brand icon, nav links, tools, and version footer. Full crimson theme throughout — no green UI accents.

---

## Changes made this session

### Calculator redesign (commit `b90f3e4`)
- **`web/static/index.html`** — Replaced top header + old right sidebar with stalker-dashboard layout:
  - Inner `.header` bar: "Damage Calculator" title + Guide/Changelog action buttons
  - `.content` grid (1fr 320px): `.content-main` (weapon/mods/enemy/options/buffs/arcanes/Calculate) + `.content-side` (weapon stats, enemy stats, results, placeholders)
  - Right `aside.sidebar`: brand icon + "VOID CODEX", `nav.nav-menu` with Calculator/Live Data nav-items, `.sidebar-tools` (Guide/Changelog buttons), `.sidebar-footer` (version)
  - Mobile: burger btn (top-right fixed) + sidebar slides in from right + `.sidebar-overlay` backdrop
- **`web/static/style.css`** — Full stalker palette + layout:
  - `:root` vars: `--bg: #050505`, `--surface: rgba(13,13,13,0.7)`, `--border: rgba(139,0,0,0.15)`, `--crimson: #8b0000`, `--crimson-bright: #dc143c`; `--accent-green` → crimson (no green UI)
  - Fonts: `--font-display: 'Orbitron'`, `--font-body: 'Rajdhani'`; removed all `'Share Tech Mono'` references
  - Removed blob `body::before`/`body::after` animations
  - New layout classes: `.main`, `.header`, `.header-title`, `.header-actions`, `.content`, `.content-main`, `.content-side`
  - New sidebar classes: `.sidebar`, `.brand`, `.brand-icon`, `.brand-text`, `.nav-menu`, `.nav-item` (with active indicator on right edge), `.nav-icon`, `.sidebar-tools`, `.sidebar-footer`
  - Mobile: `.burger-btn`, `.sidebar-overlay`, `@media (max-width: 900px)` sidebar slide-in
  - `.panel`: stalker style (12px radius, crimson top glow `::before`, no tactical corner marks, no `//` h2 prefix, Orbitron h2)
  - Removed old: `header`, `.nav-brand`, `.nav-sep`, `.nav-links`, `.burger-btn` (old), `.drawer-overlay`, `.mobile-drawer`, `.r-sidebar`, `.r-nav`, `.r-nav-btn`, `.sidebar-section-label`, `.sidebar-divider`, `.r-sidebar-footer`, `.body-row`, `.calc-wrap`, `.calc-wrap-inner`, `.container`
- **`web/static/js/app.js`** — Updated `toggleDrawer()` to toggle `#sidebar` + `#sidebar-overlay` instead of old drawer elements

### Version bump + changelog
- `src/version.py` → `0.4.1`
- `CHANGELOG.md` + `CHANGELOG_ENTRIES` in `constants.js` updated with graphical update entry

---

## Known issues / next priorities

### Riven modal
The riven modal was flagged as broken in a prior session. It was **not touched this session**. With the panel padding/radius changes it may need re-checking. Ask user for a screenshot before touching code. Key file: `web/static/js/modals.js:273-293` (`toggleRivenDropdown()`).

### Cycles + Events not yet rendered in live.html
`_parse_cycles()` and `_parse_events()` data is present in `/api/worldstate` response but `renderAll()` in `live.html` doesn't call `buildCyclesCard()` or `buildEventsCard()` — those functions don't exist yet.

---

## Feature backlog (discussed with user in prior sessions)

1. ~~Weapon Arcanes~~ — **DONE**
2. ~~Condition Overload curves~~ — **DONE**
3. Side-by-side Build Compare — two weapon+mod setups against same enemy
4. Mod Optimizer — brute-force best mod per slot given weapon + enemy
5. Armor Strip modeling — remaining armor after N Corrosive procs or abilities
6. Damage Falloff — distance-based damage reduction for applicable weapons
7. EHP Calculator (v2.0) — Warframe survivability (needs Warframe database)
8. Status Simulator — steady-state active proc count given fire rate + status chance
9. Build Cards — export styled build image for Discord/Reddit sharing
10. Build Sharing — URL-encoded state for copy-paste build links
11. Live Data — render open-world cycle states and active events cards (data already parsed)

---

## Current state
- Branch: `claude/review-handoff-bbSMM`
- Version: `0.4.1`
- Game data: Update 41 — The Old Peace
- Tests: 281 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.4.1`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 281 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] **Check riven modal** — ask user if it still looks broken, get screenshot before touching code
- [ ] If cycles/events cards are wanted, add `buildCyclesCard()` + `buildEventsCard()` to `live.html` and wire into `renderAll()`
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
- [ ] When adding new features, update User Guide in `index.html` (`#guide-overlay`)
- [ ] Keep mobile optimization in mind (test at ≤375px and ≤900px breakpoint)
