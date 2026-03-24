# Void Codex — Session Handoff

## Session summary
Implemented Weapon Arcanes — stack-based endgame bonuses (Merciless, Deadhead, Cascadia, Dexterity). Full pipeline: dataclass, preset factories, calculator integration (Step 1 damage, Step 2 headshot, CC/CD/reload), API endpoints, CLI flag, Web UI panel. 19 new tests, 275 total passing.

---

## Changes made this session

### 1. Weapon Arcanes — Backend
- `src/models.py`: Added `WeaponArcane` dataclass (damage_bonus, cc_bonus, cd_bonus, headshot_bonus, reload_bonus, flat_damage, max_stacks, stacks)
- `src/arcanes.py`: **New file** — 11 preset factories (`ARCANE_PRESETS`), display names, restrictions, max stacks, `make_arcane()` factory
- `src/calculator.py`: Both `calculate()` and `calculate_procs()` accept `arcanes` parameter. Arcane damage_bonus additive with Serration in Step 1. Deadhead headshot_bonus additive to body_part_multiplier in Step 2 (headshot only). Cascadia Overcharge flat_damage distributed proportionally among IPS types.

### 2. Weapon Arcanes — API
- `web/api.py`: `ArcaneSpec` model, `GET /api/arcanes` endpoint, `arcanes` field on `CalcRequest` and `ModdedWeaponRequest`. CC/CD/reload bonuses pre-computed and added to existing galvanized totals. `modded_reload` added to calculate response.

### 3. Weapon Arcanes — CLI
- `__main__.py`: `--arcane NAME:STACKS` flag (repeatable, max 2). Arcane bonuses integrated into stat computation. Active arcanes displayed in results header.

### 4. Weapon Arcanes — Web UI
- `web/static/js/constants.js`: `ARCANE_OPTIONS` array (11 arcanes), `arcaneRowId` counter
- `web/static/js/modals.js`: `addArcaneRow()`, `removeArcaneRow()`, `getActiveArcanes()`, `clearIncompatibleArcanes()`, `updateArcaneStackMax()`. Dropdown filtered by weapon slot. Max 2 rows.
- `web/static/js/calculate.js`: `arcanes: getActiveArcanes()` in POST body
- `web/static/js/weapons.js`: `arcanes` in modded-weapon POST body. `clearIncompatibleArcanes()` called on weapon change.
- `web/static/index.html`: "Weapon Arcanes" panel between Buffs and Calculate button

### 5. Tests
- `tests/test_arcanes.py`: **New file** — 19 tests covering make_arcane factory, stack clamping, Merciless damage (additive with Serration), Deadhead headshot bonus, Deadhead no-effect on body shots, two arcanes, Cascadia Overcharge flat damage, procs with arcane bonus

### 6. Documentation
- `CLAUDE.md`: Added Weapon Arcanes section (pipeline placement, presets table, usage). Removed from "Known unimplemented". Updated test count 256→275. Added arcanes.py and test_arcanes.py to project structure.

---

## Feature backlog (discussed with user this session)

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
- Version: `0.2.2` (pending bump decision)
- Game data: Update 41 — The Old Peace
- Tests: 275 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.2.2`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 275 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
- [ ] Remind user of feature backlog (see list above)
