# Void Codex — Session Handoff

## Session summary
UI-only session: glassmorphic modal polish, uniform input/field styling, combobox dropdown redesign, mobile bug fixes, and text colour tuning. No logic or data changes — all 256 pytest tests still pass.

---

## Changes made this session

### 1. Version bump to v0.2.2
- `src/version.py`: `APP_VERSION` → `"0.2.2"`
- `CHANGELOG.md`: new `[0.2.2]` entry — "UI polish and mobile optimisations across the web interface"
- `web/static/js/constants.js`: new entry prepended to `CHANGELOG_ENTRIES`

### 2. Glassmorphic modals (`web/static/style.css`)
- All modals (Guide, Changelog, Buffs, Riven, Alchemy) use `backdrop-filter: blur(22px) saturate(1.3)` + `rgba(10,12,22,0.96)` dark glass background
- Custom `<select>` dropdowns restyled to match dark theme
- Toggle/checkbox custom styling

### 3. Combobox dropdown polish
- Glass background (`rgba(10,12,22,0.96)`) — was semi-transparent
- Border switched to `var(--border)` (neutral subtle white) — removed gold/yellow `--border-highlight`
- Uniform 12px font + compact padding across all inputs, fields, and dropdown items

### 4. Text colour — `--text-field`
- Final value: `#8888a4` (blue-gray, matches the placeholder tone)
- Iterated through several values this session; `#8888a4` was approved

### 5. Mobile fixes
- Disabled mod drag on touch devices
- Always-visible remove button on mobile mod cards
- Fixed modal background scroll bleed on iOS
- Fixed alchemy modal header layout (Clear Mods / X button separation)
- Fixed "What's New" modal header clipping + mobile scroll bleed

---

## CSS variable reference (key design tokens)
```css
--border:           rgba(255, 255, 255, 0.12)   /* subtle neutral border */
--border-highlight: rgba(196, 154, 31, 0.3)     /* gold — used on .panel:hover and .stat-block:hover ONLY */
--text:             #e0e0e8                      /* general body text */
--text-field:       #8888a4                      /* input/field/dropdown text */
--text-dim:         #777788                      /* placeholder + dimmed labels */
--accent:           #c49a1f                      /* gold accent */
```
**Note:** `--border-highlight` (gold) was intentionally removed from the combobox dropdown border this session. Do NOT re-add it to dropdowns or modals — it looks yellow and clashes. It stays on `.panel:hover` and `.stat-block:hover` only.

---

## Current state
- Branch: `claude/review-handoff-notes-wQAsQ`
- Version: `0.2.2`
- Game data: Update 41 — The Old Peace
- Tests: 256 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things before touching any code:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.2.2`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.
> When confirming a changelog entry, update BOTH `CHANGELOG.md` (repo root) AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 256 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `constants.js`
