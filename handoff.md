# Void Codex — Session Handoff

## Session summary
Versioning and changelog session. Bumped to v0.2.0 (SemVer minor) and added changelog in two places: `CHANGELOG.md` repo file and a "What's New" modal in the Web UI.
No logic changes; all 256 pytest tests still pass.

---

## Changes made

### 1. Version bump
- `src/version.py`: `APP_VERSION` → `"0.2.0"`
- Guide modal footer placeholder updated to match

### 2. CHANGELOG.md (new file, repo root)
- Keep a Changelog format + SemVer
- Two entries: v0.2.0 (Alchemy Guide redesign, API field, fixes) and v0.1.0 (initial release)
- Professional, user-facing language — no code paths or sensitive info

### 3. "What's New" modal (Web UI)
- **Nav button:** "What's New" added to header nav bar, same inline style as Guide button
- **Overlay:** `#changelog-overlay` using `.mod-picker-overlay` base class
- **Modal:** `.changelog-modal` — glassmorphism card (560px), scrollable body, sticky header
  - Reuses Guide modal's blur/saturate/border treatment
  - Version headers (gold) with dates, section headings (Added/Improved/Fixed), bullet lists
  - Close via × button, backdrop click
- **JS:** `CHANGELOG_ENTRIES` constant (array of `{version, date, sections[]}`) rendered by `renderChangelog()`
  - `openChangelog()` / `closeChangelog()` follow existing open/close pattern
  - Backdrop click handler added to existing unified listener
- **CSS:** `.changelog-modal`, `.changelog-modal-header`, `.changelog-modal-body`, `.changelog-entry`, `.changelog-ver`, `.changelog-date`, `.changelog-section-heading`, `.changelog-list`
  - Responsive: bottom-sheet at ≤520px, tighter padding at ≤768px

---

## Current state
- Branch: `claude/review-handoff-pjWUR`
- Version: `0.2.0`
- Game data: Update 41 — The Old Peace
- Tests: 256 passing

---

## Start-of-session checklist for next Claude

> **Ask the user two things:**
> 1. "Should I bump the version in `src/version.py`? Current version is `0.2.0`."
> 2. "Should this session's changes be tracked in the changelog?"
>
> Do NOT auto-bump the version or add changelog entries without explicit confirmation.

- [ ] Run `pytest` — confirm 256 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump and changelog tracking (see above)
- [ ] If version is bumped, update `CHANGELOG.md` and `CHANGELOG_ENTRIES` in `index.html`
