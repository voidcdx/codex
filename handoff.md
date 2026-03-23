# Void Codex — Session Handoff

## Session summary
Three-part session: (1) versioning + changelog infrastructure, (2) JS extraction from index.html into 8 separate files, (3) patch version bump to v0.2.1 + changelog entry for the refactor.
No logic changes; all 256 pytest tests still pass.

---

## Changes made this session

### 1. Version bump to v0.2.1
- `src/version.py`: `APP_VERSION` → `"0.2.1"` (patch — internal refactor, no user-facing changes)

### 2. Changelog entry for v0.2.1
- `CHANGELOG.md`: new `[0.2.1]` entry added above `[0.2.0]`
- `web/static/js/constants.js`: new entry prepended to `CHANGELOG_ENTRIES` (powers the "What's New" modal)
- Entry text: "Web interface JavaScript reorganised into separate, focused modules for improved maintainability and long-term reliability"

### 3. Version bump to v0.2.0 (previous session work — already committed)
- `src/version.py`: `APP_VERSION` → `"0.2.0"`
- `CHANGELOG.md`: Keep a Changelog format, two entries: v0.2.0 and v0.1.0
- "What's New" nav button + `#changelog-overlay` glassmorphism modal in Web UI
- `CHANGELOG_ENTRIES` constant in `constants.js` rendered by `renderChangelog()`
- CSS: `.changelog-modal*` classes in `style.css` with responsive rules

### 4. JS extraction — index.html split into 8 files (previous session work — already committed)
`index.html` reduced from ~2,450 lines to ~360 (HTML-only, no inline JS).
All JavaScript moved to `web/static/js/` with `<script defer>` tags in `<head>`.

| File | Lines | Contents |
|------|-------|----------|
| `constants.js` | 243 | All global state + data constants |
| `utils.js` | 86 | `esc()`, `fmtNum()`, `dmgIcon()`, `initTooltips()`, `getCurrentWeapon/Enemy()` |
| `combobox.js` | 101 | `setupCombobox()`, `clearCombobox()` |
| `weapons.js` | 882 | Mod grid, picker, weapon stats, element badges, modded stats, special slots |
| `enemy.js` | 126 | Enemy panel, level scaling, Steel Path, Eximus |
| `modals.js` | 333 | Alchemy Guide, Riven Builder, Guide, Changelog, Buffs |
| `calculate.js` | 250 | `runCalculation()`, `showResults()`, `showError()` |
| `app.js` | 49 | `loadData()` bootstrap, DOMContentLoaded handlers |

**Key architecture notes:**
- No bundler — plain `<script defer>` tags execute in document order
- All functions/variables on `window` scope (unchanged from before)
- CDN scripts (SortableJS, Popper, Tippy) in `<head>` with `defer`, before app scripts
- `constants.js` must load first (declares all shared mutable state)
- `app.js` must load last (bootstrap)

---

## Current state
- Branch: `claude/review-handoff-pjWUR`
- Version: `0.2.1`
- Game data: Update 41 — The Old Peace
- Tests: 256 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.2.1`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 256 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
