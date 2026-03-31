# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional.

**Version:** `0.5.8`
**Branch:** `claude/continue-handoff-8bCEE` — last commit `b575e0c`

---

## What Was Done This Session

### 1. Nightwave challenge descriptions
- Added `_nw_description()` helper and `_NW_DESCRIPTIONS` dict (~120 entries) in `parse_worldstate.py`
- Each parsed challenge now includes a `description` field (e.g. "Kill 150 Enemies with Toxin Damage")
- Elite/weekly key collision fixed with `_NW_ELITE_NAMES` / `_NW_ELITE_DESCRIPTIONS` dicts — e.g. `KillEximus` resolves to different text depending on `is_elite`
- `buildNightwaveCard` in `index.html` renders `.nw-desc` when `ch.description` is present
- Known gap: `KillEnemiesWithPrimary` has no description entry yet (shows auto-spaced title only)

### 2. News & Events panel redesign
- Removed old news image slider (`.news-card`, `.news-thumb`, `.news-slider`, all `.news-*` CSS)
- `buildNewsEventsPanel(news, events, gifts)` replaces both `buildNewsSection()` and `buildEventsCard()`
- Two-column layout (`.ne-body--split`) when events/gifts are present; auto-reverts to single "News" column when none active
- Mobile ≤600px: columns stack, border-bottom separates them
- New CSS classes in `live.css`: `.ne-body`, `.ne-body--split`, `.ne-col`, `.ne-news`, `.ne-events`, `.ne-sub-header`, `.ne-news-list`, `.ne-news-link`, `.ne-news-plain`, `.event-row--gift`, `.alert-gift-label`, `.nw-desc`

### 3. Removed alert banner ticker
- `#alert-banner` div, `buildAlertBanner()` JS function, and all `.ab-*` / `.alert-banner` CSS removed
- The `.live-page-wrap` flex wrapper kept (handles centering/sizing), comment updated

### 4. Gifts of the Lotus — full fix
**Root cause investigation:** Gifts come from TWO separate worldstate keys:
- `raw["Alerts"]` — regular LotusGift alerts (Tag: "LotusGift") — missions with node/faction/reward
- `raw["Goals"]` — anniversary tactical alert gifts (Tag: "Anniversary*TacAlert") — the named "Stolen!" and "Elite" variants

**`parse_worldstate.py` changes:**
- Added `_parse_goals(raw: list) -> list[dict]` — detects Goals entries with "TacAlert" or "Anniversary" in Tag, maps to human-readable names:
  - Tags containing "ChallengeMode" or ending "CMA" → `"Gifts of the Lotus – Elite"`
  - Other anniversary TacAlert tags → `"Gifts of the Lotus – Stolen!"`
  - Reward resolved via `_item_name()` (e.g. "Rhino Dex Skin", "Orokin Catalyst")
- `_parse_alerts()` updated: all alerts now include `name` field (e.g. `"Sabotage — Cervantes (Earth)"`), `is_gift` always `False` (alerts are not shown as gift events)
- `parse()` merges: `_parse_alerts(...) + _parse_goals(...)` into `"alerts"` key

**`index.html` / `renderAll()` changes:**
- `gifts` = `allEvents.filter(is_gift)` + `allAlerts.filter(is_gift)` (Goals-based gifts end up here)
- `plainAlerts` = alerts with `is_gift: false`
- `allEventsAndAlerts = [...plainAlerts, ...plainEvents]` passed as events column
- No separate Alerts card in the grid — everything goes in the Active Events column
- Gift row template uses `g.name` as title, `g.reward` as subtitle

**Result:** 5 items in Active Events — 3 Gifts of the Lotus (from Goals) + 2 mission alerts (from Alerts) with proper labels.

### 5. Debug endpoints added to `web/api.py`
- `GET /api/worldstate/debug-nightwave` — raw challenge paths + parsed output
- `GET /api/worldstate/debug-gifts` — full goals dump, all alerts summary, broad scan for gift strings across all worldstate keys; useful for diagnosing future gift location changes
- `GET /api/worldstate/debug-alerts` — full raw alerts + parsed alerts + key scan (kept for reference)

---

## Pending / TODO

- Version bump pending — user deferred, ask at start of next session
- Enkaus weapon: re-run data refresh once wiki module is updated (check `Module:Weapons/data?action=raw`)
- `KillEnemiesWithPrimary` nightwave challenge: no description entry yet — needs correct wiki display name confirmed
- Debug endpoints can be removed or rate-limited further once live data is stable

---

## Key Files Changed This Session
- `scripts/parse_worldstate.py` — `_nw_description()`, `_NW_DESCRIPTIONS`, `_NW_ELITE_*`, `_parse_goals()`, `_parse_alerts()` name field, `parse()` merges goals
- `web/api.py` — debug-nightwave, debug-gifts, debug-alerts endpoints
- `web/static/index.html` — `buildNewsEventsPanel()`, removed banner + `buildAlertBanner()`, `renderAll()` gift/alert routing
- `web/static/live.css` — removed all `.ab-*` / `.alert-banner` CSS, added `.ne-*` layout classes, `.event-row--gift`, `.nw-desc`

---

## Worldstate Structure Notes (for future sessions)
The DE worldstate (`api.warframe.com/cdn/worldState.php`) has these relevant top-level keys:
- `Alerts` — regular alerts; LotusGift alerts have `Tag: "LotusGift"` and `descText: "/Lotus/Language/Alerts/LotusGiftDesc"`. These are MISSIONS (have node/faction/reward), not "Gifts of the Lotus" in the UI sense.
- `Goals` — anniversary tactical alert gifts; have `Tag: "Anniversary*TacAlert"`, `MissionKeyName` with "TacAlertKey*", `Reward.items[]`. These ARE the "Gifts of the Lotus" shown in the Events column.
- `Events` — game events (Plague Star, etc.) — parsed by `_parse_events()`, shown in events column
- `SeasonInfo` — nightwave season + active challenges
- `ActiveMissions` + `VoidStorms` — fissures

## Git Notes
- Working branch: `claude/continue-handoff-8bCEE`
- Commits pushed to remote; user merges to main on their Windows machine
- User is on branch `codex` locally on Windows — they merge from the claude branch
