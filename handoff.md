# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional.

**Version:** `0.5.8`
**Branch:** `claude/read-handoff-22llh` — last commit `aae97f5`

---

## What Was Done This Session

### 1. Nightwave challenge — KillEnemiesWithPrimary
- Added `"KillEnemiesWithPrimary": "Mow Them Down"` to `_NW_NAMES` in `parse_worldstate.py`
- Added `"KillEnemiesWithPrimary": "Kill 150 Enemies with a Primary Weapon"` to `_NW_DESCRIPTIONS`
- Confirmed in-game: 1000 standing, challenge name "Mow Them Down"

### 2. News & Events panel — text/formatting tweaks (`index.html` + `live.css`)
- **News capped at 7 items** (was 10, briefly 5)
- **Relative timestamps** added inline before each article title: `relativeTime(iso)` helper → "Xd ago / Xh ago / Xm ago"; `0.85rem` dim text
- **News font size** bumped to `1rem` (matches event titles)
- **Event rows restructured**: `.event-row-header` wraps title (left) + timer (right) on same line
- **Reward text** (`.event-desc`) color changed from dim grey to crimson (`var(--crimson-bright)`)
- **Event row padding** reduced from `8px` to `6px` top/bottom

### 3. Nightwave panel layout (`index.html` + `live.css`)
- **Tag + title on same line**: `.nw-title-row` flex row wraps `<nw-tag>` + `<nw-title>`
- **Description below** title (was previously inside a monolithic `.nw-challenge-info` block alongside the timer)
- **Timer moved under standing number**: `.nw-right` is a flex column — rep on top, eta below
- **Tag alignment fixed**: removed `align-self: flex-start` (was pushing tag up); removed left padding (no background to justify it)

---

## Pending / TODO

- Version bump pending — user deferred, ask at start of next session
- Enkaus weapon: re-run data refresh once wiki module is updated
- Debug endpoints (`/api/worldstate/debug-*`) can be removed once live data is stable

---

## Key Files Changed This Session
- `scripts/parse_worldstate.py` — `KillEnemiesWithPrimary` added to `_NW_NAMES` + `_NW_DESCRIPTIONS`
- `web/static/index.html` — `relativeTime()` helper; `buildNewsEventsPanel()` news slice/timestamps/event-row-header; `buildNightwaveCard()` nw-left/nw-right/nw-title-row restructure
- `web/static/live.css` — `.ne-news-list li`, `.ne-news-time`, `.ne-news-link` (1rem, inline-flex); `.event-row-header`, `.event-desc` crimson, event padding 6px; `.nw-left`, `.nw-right`, `.nw-title-row`, `.nw-tag` left-padding removed

---

## CSS Class Reference (live.css — News & Events + Nightwave)

### News items
```
.ne-news-list li     flex row: timestamp + link on same line
.ne-news-time        0.85rem dim, inline before title, flex-shrink:0
.ne-news-link        inline-flex, 1rem, crimson chevron ::before
```

### Event rows
```
.event-row           padding: 6px 0; border-bottom
.event-row--gift     gradient bg, padding: 6px 8px, margin: 0 -8px
.event-row-header    flex row: justify-content: space-between (title left, eta right)
.event-title         1rem, text-primary
.event-desc          0.85rem, crimson-bright (reward text)
.live-eta            0.8rem, text-dim, white-space: nowrap
```

### Nightwave rows
```
.nw-row              flex, align-items: flex-start
.nw-left             flex column: .nw-title-row → desc
.nw-title-row        flex row, align-items: baseline — tag + title inline
.nw-right            flex column, align-items: flex-end — rep then eta
.nw-tag              0.67rem Orbitron; padding: 1px 5px 1px 0 (no left padding)
```

---

## Worldstate Structure Notes
- `Alerts` — regular alerts; LotusGift alerts have `Tag: "LotusGift"`
- `Goals` — anniversary TacAlert gifts (shown in Active Events as Gifts of the Lotus)
- `Events` — game events (Plague Star, etc.)
- `SeasonInfo` — nightwave season + active challenges
- `ActiveMissions` + `VoidStorms` — fissures

## Git Notes
- Working branch: `claude/read-handoff-22llh`
- User is on branch `codex` locally on Windows — they merge from the claude branch
