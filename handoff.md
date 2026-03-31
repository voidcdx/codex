# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional.

**Version:** `0.5.8`
**Branch:** `claude/continue-handoff-docs-Zw93K` — last commit `94aa98a`

---

## What Was Done This Session

### 1. ui-ux-pro-max skill — persisted to repo
- Skill was ephemeral (lived only in sandbox ~/.claude/skills/) — lost between sessions
- Fixed: skill file now lives at `skills/ui-ux-pro-max/SKILL.md` in the repo
- `session-start.sh` updated to loop over `skills/*/` and copy each to `~/.claude/skills/` on startup
- Skill auto-installs every session going forward

### 2. Factions page — complete redesign
- Replaced matrix view + card grid with a single scrollable **faction roster**
- No grids, no rows, no view toggle
- Factions grouped by type: Grineer / Corpus / Infested / Other
- Group labels colored by faction group (gold / blue / green / purple)
- Each faction entry: name on left (180px), damage types on right
- Only relevant damage types shown — neutral types absent entirely
  - Weak (×1.5): element-colored icon + glow, element name, ×1.5 mult
  - Resist (×0.5): crimson icon + glow, element name, ×0.5 mult
  - Separator between weak and resist sections
- Entry left border = faction group color; gradient bg bleed from left
- Hover deepens faction color tint
- Matrix view, cards view, view toggle, attachMatrixHover, renderMatrix,
  renderCards, setView, cycleView all removed
- Search + type filter (all/vulnerable/resistant) + group filter (all/grineer/corpus/infested/other) kept

---

## Pending / TODO

- Version bump deferred — ask at start of next session
- Enkaus weapon: re-run data refresh once wiki module is updated
- Debug endpoints (`/api/worldstate/debug-*`) can be removed once live data is stable

---

## Key Files Changed This Session
- `skills/ui-ux-pro-max/SKILL.md` — new; skill definition for Void Codex design system
- `.claude/hooks/session-start.sh` — added skills copy loop
- `web/static/factions.css` — complete rewrite for roster layout
- `web/static/factions.html` — removed matrix/cards divs + view toggle; added roster div + group filter pills
- `web/static/js/factions.js` — complete rewrite; renderRoster(), FACTION_GROUPS, FACTION_GROUP_COLORS, setGroup(), applyFilter() with group support

---

## Factions Roster CSS Reference

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
.dmg-item-icon           20×20px SVG
.dmg-item-name           0.58rem Orbitron uppercase
.dmg-item-mult           0.65rem Orbitron 700
```

### Faction group colors (game-data, not UI accents — row borders/labels only)
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
- Working branch: `claude/continue-handoff-docs-Zw93K`
- User is on branch `codex` locally on Windows — they merge from the claude branch
