# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional.

**Version:** `0.5.9`
**Branch:** `claude/continue-handoff-docs-POh8b`

---

## What Was Done This Session

*(session in progress)*

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
- Working branch: `claude/continue-handoff-docs-POh8b`
- User is on branch `codex` locally on Windows — they merge from the claude branch
