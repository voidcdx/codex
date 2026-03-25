# Void Codex — Session Handoff

## Session summary
Applied Stalker theme consistently to Guide and What's New (Changelog) modals. Fixed a series of progressive layout bugs (top cut off, X button unstyled, "Quick Start" heading hidden, side borders invisible on mobile). Replaced all hardcoded `rgba()` crimson values in `modals.css` with proper CSS variables. Fixed real-phone viewport cut-off with `dvh` units.

---

## Changes made this session

### Modal theme + layout fixes (`web/static/modals.css`)
- Restored `position: relative` on `.guide-modal` / `.changelog-modal` shell (was lost in prior refactor)
- Added `min-height: 0` to `.guide-modal-body` and `.changelog-modal-body` — critical fix for flex overflow; without it the body grows to full content height, overflowing `max-height: 88vh` and getting clipped by the overlay
- Added `position: relative; z-index: 2` to both modal headers so the `::before` glow (z-index 1) doesn't paint over the X button and title
- Added `.riven-modal-close` styles — this class was lost during the `style.css` → multiple-files split and was never defined in any new file
- Changed modal border from `var(--border)` (too subtle at 0.15 opacity against the dark overlay) to `var(--border-red)` (0.30 opacity)
- Removed `@media (max-width: 480px)` rule that was explicitly stripping `border-left: none; border-right: none` from modals
- Applied full stalker theme to guide/changelog — `var(--surface)`, `var(--surface2)`, `var(--border-red)`, `var(--radius)`, `var(--glass-blur)`, `::before` gradient glow — matching `.panel` exactly
- Replaced ALL hardcoded `rgba(139,…)` / `rgba(220,20,60,…)` with CSS variables: `var(--crimson-glow)`, `var(--accent)`, `var(--accent2)`, `var(--border-red)`, `color-mix(in srgb, var(--accent…) X%, transparent)`
- Mobile `max-height` switched to `min(Xvh, Xdvh)` — fixes real-phone address-bar clipping that devtools emulation doesn't show

### Version + changelog
- `src/version.py` → `0.4.2`
- `CHANGELOG.md` + `CHANGELOG_ENTRIES` in `constants.js` — "Design tweaks — modal theme consistency, CSS variable cleanup, mobile viewport fix"

---

## Design system rules (ENFORCE THESE)
The user is very strict about this — **never use hardcoded `rgba()` for theme colors**. Always use CSS variables:

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

For one-off opacities: use `color-mix(in srgb, var(--accent) 8%, transparent)` — **not** hardcoded rgba.

---

## Known issues / next priorities

### Riven modal
Not touched this session. Ask user for a screenshot before touching code. Key file: `web/static/js/modals.js:273-293` (`toggleRivenDropdown()`).

### Cycles + Events not yet rendered in live.html
`_parse_cycles()` and `_parse_events()` data is present in `/api/worldstate` response but `renderAll()` in `live.html` doesn't call `buildCyclesCard()` or `buildEventsCard()` — those functions don't exist yet.

---

## Feature backlog (discussed with user)

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
- Branch: `claude/review-handoff-7pzk5`
- Version: `0.4.2`
- Game data: Update 41 — The Old Peace
- Tests: 281 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.4.2`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 281 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] **Check riven modal** — ask user if it still looks broken, get screenshot before touching code
- [ ] If cycles/events cards are wanted, add `buildCyclesCard()` + `buildEventsCard()` to `live.html` and wire into `renderAll()`
- [ ] When adding new features, update User Guide in `index.html` (`#guide-overlay`)
- [ ] Keep mobile optimization in mind (test at ≤375px and ≤900px breakpoint)
- [ ] **Never use hardcoded rgba() for theme colors** — always use CSS variables (see Design System Rules above)
