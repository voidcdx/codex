# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/continue-handoff-docs-ij1wt`

---

## What Was Done This Session

### Reliquary Page — Search, Mobile, and Image Fixes

#### 1. Search & Tab State Fix
- **Tab state mismatch**: HTML had `active` class on Warframes button but JS started at `activeTab = 'all'` — synced both to `'warframes'`
- **Click-away wipe fix**: `collapseSearch()` no longer clears the search query when clicking away (e.g. clicking a set item). Only the X button or toggling the magnifier explicitly clears it. Added `forceClear` parameter.

#### 2. Mobile Collapsible Toggle Removed
- Removed the "N sets" mobile toggle button (`rq-mob-toggle`), `toggleMobileList()`, `updateMobCount()`
- Set list is now always visible on mobile — no collapse behavior
- Removed all `.mob-open` CSS and related mobile overrides

#### 3. Seg Toggle Kept, Search Styled
- Warframes/Weapons seg pills restored — user wants them
- Seg toggle height matched to search field (22px)
- Search input restyled: Exo 2 font, 0.65rem, uppercase, 600 weight
- Placeholder: 0.6rem, uppercase, dim color
- Mobile: search expand shrinks to 100px, seg pills stay full size

#### 4. Warframe & Sentinel Images
- **Convention-based naming**: `"Saryn Prime"` → `Saryn-Prime.png` (spaces → hyphens)
- Weapon images: still data-driven from `weaponImages` map (weapons.json `image` field)
- Warframe images: `/static/images/warframes/Name-Prime.png`
- Sentinel images: `/static/images/sentinels/Name-Prime.png`
- `onerror` hides image div if file missing (graceful fallback)
- **50 warframe images**, **6 sentinel images** — all unvaulted sets covered
- Removed 2 duplicate space-named files (Banshee Prime.png, Trinity Prime.png)

#### 5. Sentinel Type Classification
- New `'sentinel'` type in `buildPrimeSets()` — detected by Carapace/Cerebrum parts
- Sentinels show under Warframes tab in seg toggle
- Type badge shows "Sentinel" in hero card
- Image lookup uses `/static/images/sentinels/` folder for sentinel type

#### 6. Hero Image Sizing & Fade
- Fixed 512×512 source images: `object-fit: contain` at 256px (180px mobile)
- Removed opacity — full color visibility
- Radial gradient mask for soft edge fade-out (80% ellipse, solid to 50%, fade at 90%)
- Reduced grayscale filter (0.1)

#### 7. Detail Panel Scroll
- `selectSet()` sets `detail.scrollTop = 0` on all screen sizes
- Mobile also scrolls detail into viewport with `scrollIntoView()`

---

## Key Files Changed This Session
```
web/static/reliquary.css           # hero image, search input, seg toggle, mobile, radial fade
web/static/js/reliquary.js         # search fix, sentinel type, image convention, scroll-to-top
web/static/reliquary.html          # removed mobile toggle, restored seg pills
web/static/images/warframes/*.png  # 50 warframe images (convention: Name-Prime.png)
web/static/images/sentinels/*.png  # 6 sentinel images
```

---

## Pending / Known Issues
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **URL state / sharing** — high-value missing feature (no work started).
- **Hero image radial fade** — user said it "cuts off half image", was widened but may need further tuning.

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
allSets         — { "Saryn Prime": { type:'warframe'|'sentinel'|'weapon', baro, parts: { partName: [{ relic, tier, rarity }] } } }
dropsMap        — { "Lith S1": [{ location, mission_type, rotation, rarity, chance }] }
baroRelicNames  — Set of relic names that are baro-exclusive
weaponImages    — { "Braton Prime": "BratonPrime.png" }  (from weapons.json)
weaponStats     — { "Braton Prime": { slot, class, crit_chance, … } }
wishlist        — Set of set names (localStorage 'rq-wishlist')
activeTab       — 'warframes' (default) | 'all' | 'weapons'
searchQuery     — current search string
selectedSet     — currently selected set name
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
web/static/reliquary.css   # .rq-sidebar, .rq-comp-*, .rq-hero, hero image
web/static/live.css        # live page, news/events, nightwave
web/static/js/reliquary.js # prime sets state + rendering + baro + images
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
- Hero images: no opacity, radial fade only, object-fit contain, no stretch
