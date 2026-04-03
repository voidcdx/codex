# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/review-handoff-notes-fhPol`

---

## What Was Done This Session

### Reliquary Page — Major UI Overhaul

Continued from previous session's Prime Sets browser. This session focused entirely on visual polish and UX improvements.

#### 1. Font Size Overhaul
All component section fonts were too small (0.5–0.65rem). Bumped across the board:
- Component name: 0.65→0.8rem, relic count: 0.5→0.7rem
- Relic name: 0.8→0.88rem, tier badge: 0.55→0.67rem
- Inline location: 0.72→0.82rem, inline chance: 0.55→0.72rem
- Drop rows, missions, rotations, chances all bumped proportionally

#### 2. Hero Card Redesign
- Removed solid black `--bg` background → transparent (blends with content area)
- Removed border, removed top crimson accent line (violates CLAUDE.md rules)
- Removed box-shadow glow (user rejected it)
- No panel gradient lines on hero — it's seamless with content area
- Divider above "Components" label uses centered gradient line (`--panel-line-top`)

#### 3. Panel Gradient Lines
- Added **top** gradient line to sidebar and detail panels (was bottom-only)
- All separators use brighter `--panel-line-top` instead of dim `--panel-line-bottom`

#### 4. Components Section — Inline Expanded Design
- **Old design**: clickable part cards that expand a separate relic section below hero
- **New design**: each component shows as a labeled section (`.rq-comp`) with all relics inline
- All relic drop locations are **always expanded** — no click needed
- Removed `toggleRelic()` function entirely
- Relic rows are `<div>` not `<button>` (non-interactive header)
- Component titles are rounded pills (`border-radius: 14px`, accent bg)
- Relic name rows are rounded pills (`border-radius: 14px`)
- Vertical left line: centered gradient (`transparent → --panel-line-top → transparent`)
- Horizontal separators between components: centered gradient via `::before` on `.rq-comp + .rq-comp`

#### 5. Baro Ki'Teer Sorting
- `buildPrimeSets()` tracks `is_baro` flag from relic data
- Sets where ALL relics are baro-exclusive get `set.baro = true`
- Baro sets sort to bottom of sidebar list
- Gold "BARO" tag badge next to set name, slightly dimmed (`opacity: 0.7`)
- Baro relics with no mission drops show italic dim note: "Available from Baro Ki'Teer's Void Trader rotation — inventory changes each visit and this relic is not guaranteed to appear."
- Module-level `baroRelicNames` Set for use in `renderDropList()`

#### 6. Mobile Collapsible Sidebar
- On ≤900px, set list and goals are **collapsed by default**
- Controls bar shows "N sets" toggle button with chevron
- Tap to expand (max-height 40vh with slide transition)
- Selecting a set auto-collapses sidebar and scrolls to detail
- `toggleMobileList()`, `updateMobCount()` functions added
- Toggle button is a rounded pill matching other controls

---

## Key Files Changed This Session
```
web/static/reliquary.css         # hero, components, gradients, mobile collapse, baro styles
web/static/js/reliquary.js       # inline expanded components, baro sorting, mobile toggle
web/static/reliquary.html        # mobile toggle button in controls bar
```

---

## Pending / Known Issues
- **Controls bar styling** — user wanted it rounded but reverted the attempt. Needs careful re-approach — don't wrap in a pill, find subtler treatment.
- **Warframe images** — weapons wired into hero card, warframes still pending.
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **URL state / sharing** — high-value missing feature (no work started).

---

## Reliquary Component Architecture
```
.rq-comp-grid (flex column, gap 0)
  .rq-comp + .rq-comp::before (gradient separator)
  .rq-comp (vertical gradient left border)
    .rq-comp-header (rounded pill: name + count)
    .rq-comp-relics (flex column)
      .rq-comp-relic.open (always open)
        .rq-comp-relic-row (rounded pill: tier badge + name + rarity)
        .rq-drop-list (top 5 locations) OR .rq-baro-note (Void Trader message)
```

## Reliquary State (reliquary.js)
```
allSets         — { "Saryn Prime": { type, baro, parts: { partName: [{ relic, tier, rarity }] } } }
dropsMap        — { "Lith S1": [{ location, mission_type, rotation, rarity, chance }] }
baroRelicNames  — Set of relic names that are baro-exclusive
weaponImages    — { "Braton Prime": "BratonPrime.png" }
weaponStats     — { "Braton Prime": { slot, class, crit_chance, … } }
wishlist        — Set of set names (localStorage 'rq-wishlist')
activeTab       — 'all' | 'warframes' | 'weapons'
searchQuery     — current search string
selectedSet     — currently selected set name
selectedPart    — unused (was for toggle, kept for compat)
```

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables, theme overrides
web/static/layout.css      # shared layout, header, sidebar, burger, back-to-top
web/static/panels.css      # .panel, .panel::before gradient lines
web/static/factions.css    # .roster-entry pattern (reference for list components)
web/static/reliquary.css   # .rq-sidebar, .rq-comp-*, .rq-hero, mobile collapse
web/static/live.css        # live page, news/events, nightwave
web/static/js/reliquary.js # prime sets state + rendering + baro + mobile
web/static/js/theme.js     # theme switcher + positionBackToTop()
```

---

## Current State — Themes
```
stalker  (default, no class)   bg: #0a0a0a   surface: #121212   accent: #8b0000 → #e53e3e
jade     body.theme-jade        bg: #080808   surface: rgba(10,18,16,0.85)   accent: #00897b → #00e5c8
ash      body.theme-ash         bg: #080808   surface: rgba(16,16,16,0.85)   accent: #466482 → #7393b3
```

## Design Decisions Log
- User prefers rounded pills (14px border-radius) for component headers and relic rows
- User rejected: box-shadow glow on hero, yellow/gold text for baro notes, pill-shaped controls bar wrapper
- All data should be visible by default — no click-to-expand patterns
- Baro sets are second-class citizens (dimmed, sorted to bottom)
- Font: Exo 2 for display (replaced Orbitron across all pages)
