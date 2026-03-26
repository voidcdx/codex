# Void Codex — Session Handoff

## Session summary
Two sessions of UI work on top of v0.5.0: (1) Figma MCP integration exploration, (2) weapon stat panel redesign — replaced cramped `.stat-rows` grid with a two-column "Option C" split layout (`.sc-wrap`), (3) iOS emoji fix for `▶` → `→` in `::before` pseudo-elements.

---

## Changes made this session

### Weapon Stats Panel (`web/static/js/weapons.js`, lines ~562–613)
- Replaced `.stat-rows > .stat-row > .stat-block` grid with `.sc-wrap` two-column split
- **Left column ("Combat"):** Crit Chance, Crit Mult, Status — large 18px values (`sc-val-lg`)
- **Right column ("Mechanics"):** Fire Rate, Magazine, Max Ammo (conditional), Reload, Multishot — compact 13px values (`sc-val-sm`)
- Crimson vertical divider (`.sc-div`) between columns
- All `sv-*` / `sm-*` element IDs preserved — `updateModdedStats()` unchanged

### CSS (`web/static/results.css`)
- Added `.sc-wrap`, `.sc-div`, `.sc-title`, `.sc-stat`, `.sc-label`, `.sc-val-lg`, `.sc-val-sm`, `.sc-modded` classes after `.stat-modded::before`
- **iOS fix:** Changed `content: '▶ '` → `content: '→ '` in both `.stat-modded::before` and `.sc-modded::before`
  - `▶` (U+25B6) renders as the colored ▶️ play button emoji on iOS Safari
  - `→` (U+2192) renders as plain text on all platforms

### Mockups (`web/static/mockups.html`)
- Standalone browser-viewable preview of 5 stat panel layout options (A–E)
- Created as fallback when Figma MCP hit rate limit
- Served at `/static/mockups.html` — not linked from main UI

### Figma MCP (`~/.claude/mcp.json`)
- Figma MCP server added: `https://mcp.figma.com/mcp` (transport: http)
- Calculator HTML pushed to Figma file "Void Codex — Calculator" (key: `DW9HEiO9qs6RuBUxtFwKUt`, node `1:23`)
- **Note:** Figma Starter plan has strict rate limits on `use_figma` calls — avoid creating multiple frames in one session

---

## Design system rules (ENFORCE THESE)

**Never use hardcoded `rgba()` for theme colors — always use CSS variables:**

| Color | Variable |
|---|---|
| Crimson glow (0.4 alpha) | `var(--crimson-glow)` |
| Dark red border (0.3) | `var(--border-red)` |
| Subtle border (0.15) | `var(--border)` |
| Bright crimson | `var(--accent2)` |
| Dark crimson | `var(--accent)` |
| Surface (glass) | `var(--surface)` |
| Surface darker | `var(--surface2)` |
| Glow blur | `var(--glass-blur)` |
| Border radius | `var(--radius)` |

For one-off opacities: `color-mix(in srgb, var(--accent) 8%, transparent)` — **not** hardcoded rgba.

**Layout / style rules:**
- `border-radius: 0` everywhere (`--radius: 0`, `--radius-sm: 0`) — sharp edges throughout
- No hardcoded inline `style=` attributes on HTML elements (SVG attributes excepted)
- No scan-line or noise overlays
- No green UI accents — `--accent-green` maps to crimson; only game-data colors stay green
- Glassmorphism on `#050505` background doesn't work — `backdrop-filter: saturate()` has nothing to act on. User has rejected all 5 attempts. Do NOT attempt again without explicit request.
- **No `▶` (U+25B6) in CSS `content:`** — renders as emoji on iOS. Use `→` (U+2192) or other safe characters.

---

## CSS class inventory (introduced/relevant)

| Class | File | Purpose |
|---|---|---|
| `.panel-sub-h` | panels.css | Section heading divider within merged panels |
| `.btn-add` | panels.css | `+ ADD` button (buffs, arcanes) |
| `.input-sm` | panels.css | Compact 44px number input |
| `.input-sm-wide` | panels.css | Compact 52px number input |
| `.input-level` | panels.css | 72px enemy level input |
| `.bonus-element-label` | panels.css | Label in bonus element form row |
| `.bonus-element-row` | panels.css | Flex row for bonus element inputs |
| `.bonus-element-unit` | panels.css | Unit text (`%`) in bonus element row |
| `.enemy-level-col` | panels.css | Column flex wrapper for level/SP/Eximus |
| `.panel-toggle` | panels.css | Clickable h2 to collapse/expand a panel |
| `.chevron` | panels.css | Rotating arrow SVG inside `.panel-toggle` |
| `.collapsible-body` | panels.css | Body that hides with `.hidden` class |
| `.sc-wrap` | results.css | Two-column split grid for weapon stats |
| `.sc-div` | results.css | Crimson vertical divider between columns |
| `.sc-title` | results.css | "Combat" / "Mechanics" column headers |
| `.sc-stat` | results.css | Individual stat block in split layout |
| `.sc-label` | results.css | Stat label (10px, uppercase) |
| `.sc-val-lg` | results.css | Large value (18px) — combat stats |
| `.sc-val-sm` | results.css | Small value (13px) — mechanics stats |
| `.sc-modded` | results.css | Modded value row (with `→` prefix) |
| `.guide-content ol` | modals.css | Guide modal ordered list |
| `.badge-vuln` | modals.css | Green vulnerability badge in guide |
| `.badge-res` | modals.css | Red resistance badge in guide |
| `.code-riven` | modals.css | Riven code snippet in guide |

---

## Known issues / next priorities

### Glassmorphism
User asked multiple times for more visible panel distinction. True glassmorphism requires colorful content behind the glass surface — on `#050505` background it's invisible. User rejected all 5 attempts. Current state: `rgba(13,13,13,0.7)` — original. Do not revisit unless user explicitly asks with new approach in mind.

### Riven modal
Not touched this session. Ask user for a screenshot before touching code. Key file: `web/static/js/modals.js`.

### Cycles + Events not yet rendered in live.html
`_parse_cycles()` and `_parse_events()` data is present in `/api/worldstate` response but `renderAll()` in `live.html` doesn't call `buildCyclesCard()` / `buildEventsCard()` — those functions don't exist yet.

---

## Feature backlog (discussed with user)

1. ~~Weapon Arcanes~~ — **DONE**
2. ~~Condition Overload curves~~ — **DONE**
3. Side-by-side Build Compare — two weapon+mod setups against same enemy (panel hidden, placeholder remains)
4. Mod Optimizer — brute-force best mod per slot given weapon + enemy
5. Armor Strip modeling — remaining armor after N Corrosive procs or abilities
6. Damage Falloff — distance-based damage reduction for applicable weapons
7. EHP Calculator (v2.0) — Warframe survivability (needs Warframe database)
8. Status Simulator — steady-state active proc count given fire rate + status chance
9. Build Cards — export styled build image for Discord/Reddit sharing
10. Build Sharing — URL-encoded state for copy-paste build links
11. Live Data — render open-world cycle states and active events cards (data already parsed)
12. Matrix Rain background — plan exists in plan file, not yet implemented

---

## Current state
- Branch: `claude/review-handoff-oooHw`
- Version: `0.5.0`
- Game data: Update 41 — The Old Peace
- Tests: 281 passing (no backend changes this session)
- Railway deploy branch: `codex`

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.5.0`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 281 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] **Never use hardcoded rgba() for theme colors** — always use CSS variables
- [ ] **Never add `style=` inline attributes** to HTML elements — extract to CSS classes
- [ ] **Never add rounded corners** — `--radius: 0` everywhere
- [ ] **Do not attempt glassmorphism** on `#050505` bg without a completely new approach
- [ ] **Never use `▶` (U+25B6) in CSS `content:`** — use `→` instead (iOS emoji issue)
- [ ] When adding new features, update User Guide in `index.html` (`#guide-overlay`)
- [ ] Keep mobile optimization in mind (test at ≤375px and ≤900px breakpoint)
- [ ] Railway deploys from `codex` branch — always push feature branch AND merge to `codex`
