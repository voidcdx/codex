# Void Codex — Session Handoff

## Session summary
Added Condition Overload scaling curve to calculation results. Mobile layout fix. Updated User Guide with Arcanes + CO Curve sections. Trimmed CLAUDE.md from 426 → 377 lines.

---

## Changes made this session

### 1. Condition Overload Curve (backend + frontend)
- `web/api.py`: When any equipped mod has `condition_overload_bonus > 0`, loops `calculate()` for statuses 0–10 and returns `co_curve: [float × 11]` in the `/api/calculate` response. `null` when no CO mod is equipped.
- `web/static/js/calculate.js`: Renders a vertical table (status count | bar | damage | % increase) between procs and DPS sections. Active row highlighted with gold left border.
- `web/static/style.css`: `.co-curve-table` row highlight styles.
- `tests/test_co_curve.py`: 6 new tests (presence/absence, individual match, monotonic increase, baseline equivalence, combo interaction).

### 2. Mobile Layout Fix
- Switched CO curve from horizontal 12-column table (broke on 375px) to vertical 2-column layout with bar chart. No horizontal scrolling needed.

### 3. User Guide Updates
- `web/static/index.html` (`#guide-overlay`): Added Weapon Arcanes section (full table with all 11 presets) and CO Curve description in Reading Results.

### 4. CLAUDE.md Maintenance
- Trimmed redundant implementation details (combobox internals, riven/alchemy CSS, arcane preset table, session history). 426 → 377 lines.
- Added rule: always update User Guide when adding new features.

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
- Branch: `claude/review-handoff-JUSoq`
- Version: `0.3.1`
- Game data: Update 41 — The Old Peace
- Tests: 281 passing

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
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
- [ ] When adding new features, update User Guide in `index.html` (`#guide-overlay`)
- [ ] Keep mobile optimization in mind (test at ≤375px)
- [ ] Remind user of feature backlog (see list above)
