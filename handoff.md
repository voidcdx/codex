# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/continue-documentation-tN0o0`

---

## What Was Done This Session

### Reliquary Page — Detail Panel Redesign + Evergreen Sets

#### 1. Breakout Image System
- **Image breaks out of panel** — placed on `.rq-detail-outer` (overflow:visible) wrapper so it physically extends above the `.rq-detail` panel border
- `.rq-detail-outer`: padding-top:50px, overflow:visible, z-index:2 (above header)
- `.rq-detail`: scrollable inner panel (overflow-y:auto)
- **Warframes/sentinels**: image on LEFT side (`.rq-img-left`), text RIGHT-aligned
- **Weapons**: image on RIGHT side (`.rq-img-right`), tilted -8deg for dynamic look
- Image: 240px desktop, 150px mobile; radial edge fade on all edges; brightness(1.2); drop-shadow
- Fade-in animation (0.4s, scale 0.95→1)
- Mobile: scrollIntoView targets outer container so breakout image is visible

#### 2. Stat Grid (replaces old hero card)
- Removed old `.rq-hero` wrapper — content lives directly in `.rq-detail`
- **2-column grid** (`.rq-stat-grid`) with colored bars: label left, value right, bar underneath
- **Weapon stats**: Damage, Crit, Crit DMG, Status, Fire Rate, Riven (with colored values/bars)
- **Warframe/Sentinel placeholders**: Health, Shields, Armor, Energy, Sprint (em-dash values, empty bars) — ready for data
- Stats sit inside `.rq-detail-info` beside image, tight under title — no dead space
- Mobile: stays 2-column (3 rows × 2)

#### 3. Evergreen / Permanently Unvaulted Sets
- `EVERGREEN_SETS` constant: 14 items that are never vaulted
  - Warframes: Nyx Prime, Valkyr Prime
  - Weapons: Braton, Burston, Cernos, Paris, Akbronco, Bronco, Hikou, Lex, Fang, Orthos, Scindo, Venka Prime
- **Green "Permanent" badge** in the type row next to Weapon/Warframe badge (`.rq-badge-permanent`)
- Uses tier-meso green color

#### 4. Layout Tightening
- Removed all dead space: detail panel padding 12px 20px, tight title margins (4px), divider 8px/6px
- `.rq-detail-header`: position:static, no min-height — content dictates height
- `.rq-detail-info`: max-width:60% desktop (100% mobile)
- Mobile: padding 10px 14px

---

## Key Files Changed This Session
```
web/static/reliquary.html          # added .rq-detail-outer wrapper around .rq-detail
web/static/reliquary.css           # breakout image, stat grid, permanent badge, layout tightening
web/static/js/reliquary.js         # EVERGREEN_SETS, breakout image on outer, stat grid, permanent tag
```

---

## Pending / Known Issues
- **Warframe stats data** — placeholder values (—) for Health/Shields/Armor/Energy/Sprint. Need warframe data source.
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **URL state / sharing** — high-value missing feature (no work started).
- **Hero image radial fade tuning** — current values: `ellipse 75% 65% at center 40%, black 35%, transparent 70%`

---

## Reliquary Detail Panel Architecture (Current)
```
.rq-detail-outer (overflow:visible, padding-top:50px, z-index:2)
  .rq-detail-img (absolute, placed by JS on outer — breaks out of panel)
    img (240px, fade-in animation, radial mask, brightness 1.2)
  .rq-detail (scrollable panel, overflow-y:auto)
    .rq-detail-header
      .rq-detail-info (max-width:60%)
        .rq-hero-type-row (Weapon/Warframe badge + Permanent badge)
        h2.rq-hero-title
        .rq-hero-sub (slot · class · trigger)
        .rq-stat-grid (2-col)
          .rq-stat-item (label + value + bar) × 6
    .rq-hero-divider
    .rq-hero-section-label "COMPONENTS"
    .rq-comp-grid → .rq-comp → .rq-comp-relic (relic rows + drop lists)
```

## Image Positioning
```
Weapons:    .rq-img-right  → right:10px, top:-30px, rotate(-8deg)
Warframes:  .rq-img-left   → left:10px, top:-20px, no rotation
                              text-align:right, margin-left:auto
Mobile:     150px, top:-15px, same left/right logic
```

## Reliquary State (reliquary.js)
```
allSets         — { "Saryn Prime": { type:'warframe'|'sentinel'|'weapon', baro, parts: { partName: [{ relic, tier, rarity }] } } }
dropsMap        — { "Lith S1": [{ location, mission_type, rotation, rarity, chance }] }
baroRelicNames  — Set of relic names that are baro-exclusive
weaponImages    — { "Braton Prime": "BratonPrime.png" }  (from weapons.json)
weaponStats     — { "Braton Prime": { slot, class, crit_chance, … } }
wishlist        — Set of set names (localStorage 'rq-wishlist')
activeTab       — 'warframes' (default) | 'all' | 'weapons'
searchQuery     — current search string
selectedSet     — currently selected set name
EVERGREEN_SETS  — const Set of 14 permanently unvaulted Prime names
```

## Image Conventions
```
weapons:    /static/images/weapons/{weapons.json image field}   (data-driven)
warframes:  /static/images/warframes/{Name-Prime}.png           (convention: spaces→hyphens)
sentinels:  /static/images/sentinels/{Name-Prime}.png           (convention: spaces→hyphens)
```

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables, theme overrides
web/static/layout.css      # shared layout, header, sidebar, burger, back-to-top
web/static/panels.css      # .panel, .panel::before gradient lines
web/static/factions.css    # .roster-entry pattern (reference for list components)
web/static/reliquary.css   # .rq-detail-outer, breakout image, stat grid, badges
web/static/live.css        # live page, news/events, nightwave
web/static/js/reliquary.js # prime sets state + rendering + baro + images + evergreen
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
- Don't remove seg toggle pills (Warframes/Weapons) — user wants them
- Don't add mobile collapsible sidebar — user wanted it removed
- Don't make seg pills smaller on mobile — keep same size everywhere
- Breakout images: warframes left, weapons right (tilted -8deg)
- No mask fading on images — user rejected multiple fade attempts; use radial edge fade only
- "Permanent" shown as green badge pill next to type badge (not standalone text)
- Stat bars preferred over stat cards — 2-column grid with colored bars
- Dead space is enemy #1 — content dictates height, no min-height, tight padding
