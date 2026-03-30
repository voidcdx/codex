# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional. Live page (`/live`) fully rebuilt with live countdown timers, full-width alert ticker, and brand header.

**Version:** `0.5.7`
**Branch:** `codex` — last commit `ac27ea0`

---

## What Was Done This Session

### 1. Live page layout — gap fix
- Added `@media (max-width: 1339px)` breakpoint collapsing grid to 1 column, skipping the 2-column zone where INVASIONS (short) left dead space beside NIGHTWAVE.
- At user's wide screen: 3 columns. At zoom/narrow: 1 column. 2-column layout never occurs.

### 2. Dot grid background
- `.live-grid` gets `radial-gradient` dot pattern as background — dots only show in empty grid areas (beneath panel backgrounds), giving a holographic HUD feel.

### 3. Full-width alert ticker
- Moved `#alert-banner` above `.app` using new `.live-page-wrap` flex-column wrapper in `live.html`.
- Banner spans both content + sidebar area.
- When no active alerts: `display: none`, zero height, `.app` fills 100%.
- Mobile: `mask-image` fade on right so ticker doesn't collide with hamburger button.

### 4. Live page header — brand + refresh
- Removed dead strip (old `.live-controls` row with just the timer).
- Header now: `VOID CODEX` brand left, refresh timer right.
- `WORLD STATUS` glitch subtext under brand — CSS animation with cyan/red offset layers, fires every 6s with long idle gaps.
- Header HTML structure:
  ```html
  <header class="header">
    <div class="live-header-brand">
      VOID <span>CODEX</span>
      <div class="live-subtext" data-text="WORLD STATUS">WORLD STATUS</div>
    </div>
    <div class="refresh-info">
      <span>Refresh in <span id="refresh-countdown">180</span>s</span>
      <button class="refresh-btn" onclick="loadData()">&#8635; Now</button>
    </div>
  </header>
  ```

### 5. Nightwave challenge dedup
- DE's worldstate API returns duplicate `ActiveChallenges` entries during rotation window.
- `_parse_nightwave()` in `scripts/parse_worldstate.py` now tracks `seen_paths` set and skips dupes.

---

## Pending / TODO

- **Subtext wording** — "WORLD STATUS" is a placeholder. User may want something more Warframe-flavored (ORIGIN CLUSTER, TENNO UPLINK, etc.)
- **VOID CODEX title treatment** — user wanted to do something to the title itself (glitch, shimmer, layout) but didn't get to it.
- **Live page review at normal resolution** — confirm dot grid + panel layout looks good at user's actual screen.

---

## Key Files (live page)
- `web/static/live.html` — `.live-page-wrap` wrapper, `#alert-banner` before `.app`, header structure, `.live-subtext` element
- `web/static/live.css` — all live-specific styles including `.live-page-wrap`, `.alert-banner`, `.live-grid`, `.live-header-brand`, `.live-subtext` + glitch keyframes
- `scripts/parse_worldstate.py` — `_parse_nightwave()` dedup fix

---

## Git / Commit Notes
- Cowork desktop app holds `.git/index.lock`, blocking sandbox commits.
- User must commit from Windows PowerShell (run commands separately — `&&` not supported):
  ```
  cd C:\Users\jesse\Desktop\codex
  git add <files>
  git commit -m "message"
  ```
- If lock blocks: `del C:\Users\jesse\Desktop\codex\.git\index.lock` then retry.
