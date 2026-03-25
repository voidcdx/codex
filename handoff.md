# Void Codex — Session Handoff

## Session summary
Short session. Diagnosed intermittent live data loading failures on `/live`. Fixed two issues:
1. **Stale cache fallback** — `get_worldstate()` now serves the last-good cached response when the DE upstream is temporarily down, instead of raising 503.
2. **UI refresh reduced** — auto-refresh changed from 60s → 180s. The server-side cache is 5 minutes, so 60s polls were just hitting cached data anyway.

---

## Changes made this session

### Worldstate resilience (commit `76272b7`)
- **`web/api.py`** — `get_worldstate()`: wrapped `_fetch_worldstate()` in try/except; on failure serves stale `_ws_cache` entry if available, only raises if no cache exists at all.
- **`web/static/live.html`** — `countdownVal` and initial display changed from `60` → `180`.

### Prior session (already committed, not touched this session)
- **`scripts/parse_worldstate.py`** (commit `c4ba6b6`) — Added `_parse_cycles()` (Cetus/Orb Vallis/Cambion Drift/Zariman cycle states) and `_parse_events()` (active game events). These are parsed but not yet rendered in `live.html` — they exist in the parsed output from `/api/worldstate` but `renderAll()` doesn't call them yet.
- **`live.html`** — Full Stalker/Shadow Acolyte theme redesign + sidebar + mobile hamburger drawer (commits `cf768ea` through `c944090`).

---

## Known issues / next priorities

### Riven modal (carried over from previous session)
Still broken — user confirmed it doesn't look right. Possible causes:
- **Portal dropdown misalignment**: `toggleRivenDropdown()` in `modals.js:273-293` positions via `getBoundingClientRect()`. If modal scroll or padding changed, dropdown won't align.
- **Mobile corner rendering**: `overflow:hidden` + `border-radius` can fail on iOS Safari. Try `clip-path: inset(0 round 14px)` instead.
- **Next session:** Ask user for screenshot before touching code.

### Cycles + Events not yet rendered in live.html
`_parse_cycles()` and `_parse_events()` data is present in `/api/worldstate` response but `renderAll()` in `live.html` doesn't call `buildCyclesCard()` or `buildEventsCard()` — those functions don't exist yet. Could be a good next feature to add cards for open-world cycles and active events.

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
- Branch: `claude/review-previous-work-1IYpw`
- Version: `0.4.0` (no bump this session)
- Game data: Update 41 — The Old Peace
- Tests: 281 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.4.0`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 281 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] **Priority: Fix riven modal** — ask user for screenshot first, test before committing
- [ ] If cycles/events cards are wanted, add `buildCyclesCard()` + `buildEventsCard()` to `live.html` and wire into `renderAll()`
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
- [ ] When adding new features, update User Guide in `index.html` (`#guide-overlay`)
- [ ] Keep mobile optimization in mind (test at ≤375px)
