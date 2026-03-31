# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.5.9` (no bump — CSS-only session)
**Branch:** `claude/review-handoff-docs-AhX7d`

---

## What Was Done This Session

### CSS Variable Refactor (completed prior session, carried over)
- All hardcoded colors extracted to CSS variables in `base.css` `:root`
- Full variable system: semantic, alpha-step, game-data, atmosphere layers

### Theme System
- Built a **3-theme switcher** — Stalker Classic (default), Jade, Void Ash
- Theme dots in header on all 3 pages; localStorage persistence
- Each theme is a `body.theme-*` CSS block overriding ~35 variables
- `web/static/js/theme.js` — standalone switcher, no deps
- `web/static/layout.css` — `.theme-switcher` + `.theme-dot` styles

### Visual Cleanup
- Removed panel hover border (`panels.css`)
- Removed `.atmo` background glow overlay (`base.css` — `display: none`)
- Removed panel `::after` radial glow behind panels
- Removed global `button { box-shadow: var(--void-glow) }`
- Removed panel border (`border: 1px solid var(--border-metal)`)
- Removed attack tab glow (was from global button rule)

### Panel Gradient Lines
- Re-added `::before` top/bottom gradient lines for **all themes** using `--panel-line-color`
- Void Ash gets a warm gold override (brighter top, dimmer bottom)
- Stalker = crimson lines, Jade = teal lines, Ash = warm gold

### Text Color Softening
- All 3 themes: `--text-primary` and `--text` changed from pure white to tinted off-whites
  - Stalker: `#ede0dc` / `#c8c0bc` (warm rosy tint)
  - Jade: `#cce8e0` / `#a8c8c0` (teal tint)
  - Ash: `#d8d0c8` / `#a8a49e` (warm parchment)

### Theme Preview Page
- `web/static/theme-preview.html` — standalone file, open directly in browser
- Shows all 3 themes side by side with mock UI
- Has Void Ash accent color comparison section (pale gold, steel blue, dusty rose, sage)
- Has Void Ash parchment variant section (ivory, linen, vellum, aged, burnt)

---

## Pending / In Progress

### Void Ash accent color — NOT YET DECIDED
User was comparing accent color options for Void Ash. Current accent is `#888888` / `#ffffff` (silver/white) — the white is confirmed too harsh. User was browsing:
- Parchment variants: Ivory `#e8dcc8`, Linen `#d4b896`, Vellum `#c4a882`, Aged `#b8956a`, Burnt `#a07850`
- Other options: Pale Gold `#c8a878`, Steel Blue-Gray `#7a9ab0`, Dusty Rose `#c09090`, Sage `#8aaa88`

**Next session: pick the Void Ash accent and apply it** (`--accent`, `--accent2`, `--crimson`, `--crimson-bright`, all alpha steps in `base.css`).

### Other pending
- Version bump deferred — ask at start of next session
- Enkaus weapon: re-run data refresh once wiki module is updated
- Debug endpoints (`/api/worldstate/debug-*`) can be removed once live data is stable

---

## Theme System Reference

### Files
```
web/static/base.css          # :root defaults (Stalker Classic) + body.theme-jade + body.theme-ash blocks
web/static/layout.css        # .theme-switcher, .theme-dot styles
web/static/js/theme.js       # applyTheme(), initTheme(), localStorage key: 'void-theme'
web/static/theme-preview.html # standalone preview page — open in browser at /static/theme-preview.html
```

### Themes
```
stalker  (default, no class)  bg: #0a0a0a  accent: #8b0000 → #e53e3e  crimson
jade     body.theme-jade       bg: #070d0c  accent: #00897b → #00e5c8  teal
ash      body.theme-ash        bg: #080808  accent: #888888 → TBD      parchment/TBD
```

### Panel gradient lines
```css
/* All themes */
.panel::before { top + bottom gradient using var(--panel-line-color) }

/* Ash override */
body.theme-ash .panel::before {
  top:    rgba(210, 185, 155, 0.65)  warm gold bright
  bottom: rgba(180, 155, 120, 0.35)  warm gold dim
}
```

### Key CSS variables per theme (what differs)
`--bg`, `--surface`, `--surface2`, `--surface-solid`, `--border`, `--border-highlight`, `--border-red`,
`--accent`, `--accent2`, `--crimson`, `--crimson-bright`, `--crimson-glow`, `--blood-red`, `--deep-red`,
`--text`, `--text-primary`, `--text-dim`, `--text-field`, `--text-muted`,
`--header-bg`, `--sidebar-bg-top`, `--dropdown-bg`, `--tooltip-bg`,
all `--accent-a*`, `--accent-mid-a*`, `--accent-hi-a*`,
`--panel-line-color`, `--atmo-*`, `--border-metal`, `--void-glow`

---

## Factions Roster CSS Reference (unchanged)

### Groups
```
.faction-roster          flex column, gap 28px
.roster-group            flex column, gap 6px — per group section
.roster-group-label      0.65rem Orbitron, colored by --faction-color, bottom border
```

### Entries
```
.roster-entry            flex row; border-left: 3px solid --faction-color; gradient bg bleed
.roster-info             180px flex-shrink:0; padding 16px 20px; border-right
.roster-name             0.78rem Orbitron 700, uppercase, letter-spacing 0.1em
.roster-dmg              flex 1; flex wrap; padding 12px 16px; gap 6px
.dmg-sep                 1px × 36px vertical separator between weak/resist
```

### Damage items
```
.dmg-item                flex column center; padding 8px 12px; min-width 56px; border 1px
.dmg-item.dmg-weak       elem-color border/bg; icon glow; label+mult in elem-color
.dmg-item.dmg-resist     crimson border/bg; icon glow; label+mult crimson
```

### Faction group colors (game-data only — row borders/labels)
```
grineer   #c07828
corpus    #4090c0
infested  #60a030
other     #9060c0
```

---

## Worldstate Structure Notes
- `Alerts` — regular alerts; LotusGift alerts have `Tag: "LotusGift"`
- `Goals` — anniversary TacAlert gifts (shown in Active Events as Gifts of the Lotus)
- `Events` — game events (Plague Star, etc.)
- `SeasonInfo` — nightwave season + active challenges
- `ActiveMissions` + `VoidStorms` — fissures

## Git Notes
- Working branch: `claude/review-handoff-docs-AhX7d`
- User is on branch `codex` locally on Windows — they merge from the claude branch
