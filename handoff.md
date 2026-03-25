# Void Codex — Session Handoff

## Session summary
Major UI layout overhaul (v0.5.0): merged panels, collapsible Options, extracted all inline styles to CSS classes, sidebar widened, content centered at 1440px, scan-line overlay removed, Builds panel hidden, header links removed, copyright footer added.

---

## Changes made this session

### Layout (`web/static/layout.css`)
- `grid-template-columns: 1fr 480px` (was `300px 1fr 480px` — removed left/builds column)
- `.content-left { display: none }` — Builds panel hidden
- `.sidebar { width: 260px }` (was 220px)
- `.app { max-width: 1440px; margin: 0 auto; width: 100% }` — full layout centered

### Panels (`web/static/panels.css`)
- `.we-col:first-child::after` — bright-in-middle gradient divider between Weapon + Enemy columns:
  ```css
  background: linear-gradient(180deg, transparent, rgba(220, 20, 60, 0.5), transparent)
  ```
  Mobile variant uses `90deg` horizontal gradient.
- `.panel-sub-h` — section divider heading within merged panels (used in Options + Mods panels)
- `.btn-add` — shared class for `+ ADD` buttons (replaced repeated inline styles on `btn-add-buff`, `btn-add-arcane`)
- `.input-sm { width: 44px; padding: 2px 5px }` — compact number inputs (Viral/Corr/Active/Galv stacks)
- `.input-sm-wide { width: 52px }` — slightly wider variant
- `.input-level { width: 72px }` — enemy level input
- `.bonus-element-label`, `.bonus-element-row`, `.bonus-element-unit` — bonus element form layout
- `.enemy-level-col { display: flex; flex-direction: column }` — level/SP/Eximus stack
- `.panel-toggle` / `.chevron` / `.collapsible-body.hidden` — Options panel collapse/expand

### HTML (`web/static/index.html`)
- Weapon + Enemy already merged into `.we-grid` (prior session); divider now glowing
- Hit Options + Warframe Buffs merged → single collapsible "Options" panel in `.content-side`
  - Order in right column: Results → Options (collapsible) → Calculate button
  - Renamed: "Corrosive Stacks" → "Corr. Stacks", "Active Statuses" → "Active Status"
- Arcanes merged as sub-section of Mods panel (`.panel-sub-h` divider below element badges)
- Guide + Changelog buttons removed from header (accessible via sidebar nav)
- Sidebar footer updated: copyright `© 2026 Void Codex` + `Data: wiki.warframe.com`
- All hardcoded `style=` attributes removed from non-SVG elements — moved to CSS classes
- Scan-line `html::before` overlay removed from `base.css`

### Modals (`web/static/modals.css`)
- `.guide-content ol { padding-left: 18px; margin: 6px 0 10px; line-height: 1.65 }`
- `.guide-content strong { color: var(--text) }`
- `.guide-content .badge-vuln { color: #4caf50; background: #1a3a1a; border-color: transparent }`
- `.guide-content .badge-res { color: #f44336; background: #3a1a1a; border-color: transparent }`
- `.guide-content .code-riven { color: var(--riven); border-color: rgba(208,160,255,0.3) }`

### Base (`web/static/base.css`)
- `html::before` scan-line overlay — **removed entirely**
- All CSS variables remain at original values (multiple glassmorphism attempts all rejected/reverted)

### Version + changelog
- `src/version.py` → `0.5.0`
- `CHANGELOG.md` + `CHANGELOG_ENTRIES` in `constants.js` — full 0.5.0 entry added

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
- Glassmorphism on `#050505` background doesn't work — `backdrop-filter: saturate()` has nothing to act on. User has rejected all glass attempts. Do NOT attempt again without explicit request.

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
| `.guide-content ol` | modals.css | Guide modal ordered list |
| `.badge-vuln` | modals.css | Green vulnerability badge in guide |
| `.badge-res` | modals.css | Red resistance badge in guide |
| `.code-riven` | modals.css | Riven code snippet in guide |

---

## Known issues / next priorities

### Glassmorphism
User asked multiple times for more visible panel distinction. True glassmorphism requires colorful content behind the glass surface — on `#050505` background it's invisible. User rejected all 5 attempts this session. Current state: `rgba(13,13,13,0.7)` — original. Do not revisit unless user explicitly asks with new approach in mind.

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
- Branch: `claude/review-handoff-cCjkJ`
- Version: `0.5.0`
- Game data: Update 41 — The Old Peace
- Tests: 281 passing (no backend changes this session)

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
- [ ] When adding new features, update User Guide in `index.html` (`#guide-overlay`)
- [ ] Keep mobile optimization in mind (test at ≤375px and ≤900px breakpoint)
