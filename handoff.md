# Void Codex — Session Handoff

## Session summary
Attempted to fix riven builder modal alignment and rounded corner issues on mobile. Multiple CSS patch attempts failed. Ended with a full CSS+HTML rebuild of the modal — but the user reports it still doesn't look right. **Next session needs to visually verify and fix the riven modal.**

---

## Changes made this session

### Riven Modal Rebuild (8 commits, still broken)
The riven builder modal had two persistent bugs:
1. **Rounded corners missing on mobile** — Safari `backdrop-filter` + `border-radius` clipping bug
2. **Dropdown and input fields misaligned** — conflicting `padding: 3px !important` mobile overrides fighting with fixed `height: 26px`

Attempted fixes (all on branch `claude/review-handoff-Cuk26`):
- Tried `-webkit-mask-image` hack for Safari clip bug
- Tried removing `!important` overrides selectively
- Finally did a **full teardown and rebuild** (commit `e63ffd6`):
  - Replaced translucent `backdrop-filter` bg with near-opaque `rgba(14,10,22,0.97)`
  - New two-column layout: left panel (160px) with static hexagon glyph `⬡`, right panel with form
  - All row elements share `height: 36px` + `box-sizing: border-box` + `font-size: 13px`
  - Removed all purple theming from modal chrome
  - Removed all `!important` font-size/padding overrides for riven elements in mobile breakpoints
  - Mobile (≤520px): stacks vertically with 80px glyph banner

**User says it still doesn't look right.** The next session should:
1. Ask the user for a screenshot or specific description of what's wrong
2. Actually test in a browser / mobile viewport before committing
3. Consider whether the portal dropdown positioning (`getBoundingClientRect` → fixed position) is the alignment culprit rather than CSS sizing

### Key files touched
- `web/static/style.css` — lines ~957–1164 (riven modal section), mobile overrides in `@media 520px` block
- `web/static/index.html` — lines 87–99 (riven modal HTML)
- `web/static/js/modals.js` — **NOT changed** (all class names preserved)

---

## Known issue: Riven modal still broken

The riven modal rebuild didn't satisfy the user. Possible remaining problems:
- **Portal dropdown misalignment**: `toggleRivenDropdown()` in `modals.js:273-293` positions the dropdown via `getBoundingClientRect()` on the button. If the modal scrolls or the button padding changed, the dropdown won't line up with the button.
- **Mobile corner rendering**: Even with opaque bg, `overflow: hidden` + `border-radius` can still fail on iOS Safari in some cases. May need to test with `clip-path: inset(0 round 14px)` instead.
- **Visual design**: User may want a more significant layout redesign, not just alignment fixes. They mentioned liking the Guide modal design — consider using that as the reference for the riven modal style.

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

---

## Current state
- Branch: `claude/review-handoff-Cuk26`
- Version: `0.3.1` (no bump this session)
- Game data: Update 41 — The Old Peace
- Tests: 281 passing
- **Riven modal needs visual fix — priority for next session**

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.3.1`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 281 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] **Priority: Fix riven modal** — ask user for screenshot, test in browser before committing
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
- [ ] When adding new features, update User Guide in `index.html` (`#guide-overlay`)
- [ ] Keep mobile optimization in mind (test at ≤375px)
