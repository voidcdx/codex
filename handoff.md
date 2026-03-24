# Void Codex — Session Handoff

## Session summary
Bugfix session: fixed Riven modal not centering on mobile and background page scrolling while modal is open.

---

## Changes made this session

### 1. Riven Modal — Mobile Centering
- `web/static/style.css`: Added `#riven-picker-overlay` to the `align-items: center` override at ≤520px (was only on `#alchemy-mixer-overlay` before). Without this, the `.mod-picker-overlay` base rule of `align-items: flex-end` pushed the riven modal to the bottom of the screen on mobile.

### 2. Riven Modal — Background Scroll Lock
- `web/static/js/modals.js`: `openRivenBuilder()` now sets `document.body.style.overflow = 'hidden'`; `closeRivenBuilder()` restores it to `''`. Prevents page scrolling behind the open modal.
- `web/static/style.css`: Added `overscroll-behavior: contain` and `-webkit-overflow-scrolling: touch` to `.riven-modal` at ≤520px for proper mobile scroll containment.

---

## Feature backlog (discussed with user in prior sessions)

1. ~~Weapon Arcanes~~ — **DONE**
2. Side-by-side Build Compare — two weapon+mod setups against same enemy
3. Mod Optimizer — brute-force best mod per slot given weapon + enemy
4. Condition Overload curves — damage scaling with 1, 2, 3... unique statuses
5. Armor Strip modeling — remaining armor after N Corrosive procs or abilities
6. Damage Falloff — distance-based damage reduction for applicable weapons
7. EHP Calculator (v2.0) — Warframe survivability (needs Warframe database)
8. Status Simulator — steady-state active proc count given fire rate + status chance
9. Build Cards — export styled build image for Discord/Reddit sharing
10. Build Sharing — URL-encoded state for copy-paste build links

---

## Current state
- Branch: `claude/review-handoff-notes-UNpPq`
- Version: `0.3.0` (no bump needed)
- Game data: Update 41 — The Old Peace
- Tests: 275 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.3.0`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 275 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
- [ ] Remind user of feature backlog (see list above)
