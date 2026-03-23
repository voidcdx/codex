# Void Codex — Session Handoff

## Session summary
Two sessions of housekeeping + polish. No logic changes; all 256 pytest tests pass.

---

## Changes made

### 1. Branding cleanup
- Removed "100% accurate" from all user-facing strings:
  - `CLAUDE.md` heading
  - `__main__.py` argparse description
  - `web/static/index.html` guide modal subtitle

### 2. Semantic versioning (`src/version.py`)
Single source of truth for two strings:
```python
APP_VERSION       = "0.1.0"
GAME_DATA_VERSION = "Update 41 — The Old Peace"
```
- `web/api.py` imports both; `GET /api/version` endpoint returns `{"app": ..., "game_data": ...}`
- `__main__.py` `--version` flag prints `Void Codex v0.1.0 · Update 41 — The Old Peace`
- Guide modal bottom shows both strings, fetched dynamically from `/api/version` on DOMContentLoaded

### 3. Input / focus styling
Removed yellow/gold focus borders from all inputs and selects.
Three CSS blocks in `style.css` (lines ~192, ~238, ~539):
- Before: `border-color: var(--accent)` + `box-shadow: 0 0 0 2px var(--accent-glow)`
- After: `border-color: rgba(255,255,255,0.25)` + `box-shadow: 0 0 0 2px rgba(255,255,255,0.06)`
- Riven modal inputs intentionally kept purple — untouched.

---

## Current state
- Branch: `claude/continue-handoff-xwp5Y`
- Version: `0.1.0` (early alpha)
- Game data: Update 41 — The Old Peace
- Tests: 256 passing

---

## Start-of-session checklist for next Claude

> **Ask the user:** "Should I bump the version in `src/version.py` before we start? Current version is `0.1.0`."

- [ ] Run `pytest` — confirm 256 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump (see above)
