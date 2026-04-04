# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** v0.8.0. Full damage pipeline, web UI, live tracker, reliquary.

**Branch:** `claude/continue-handoff-docs-YjbJQ`

---

## What Was Done This Session

### 1. Nightwave Challenge Fixes
- Added 3 missing challenge paths to `_NW_NAMES` + `_NW_DESCRIPTIONS`:
  - `InteractWithPet` → Loyalty
  - `CodexScan` → Researcher
  - `CompleteMissionMelee` → Swordsman

### 2. Mission Type Fix
- Added `MT_RETRIEVAL` → Hijack in both Python and JS parsers (was showing raw in Sortie)

### 3. Vanguard + Eterna Relic Tiers
- `TIER_ICONS` map in `reliquary.js`: Vanguard → `AxiRelicIntact.png`, Eterna → `RequiemRelicIntact.png`
- `tierOrder` extended to include both new tiers
- CSS tier badge + chip styles for Vanguard and Eterna
- `--tier-eterna` CSS variable added

### 4. Baro Ki'Teer Item Names
- Added 40 item path → display name mappings to `ITEM_NAMES` in `parse_worldstate.py`
- Covers: Primed mods, weapons, cosmetics, plushies, glyphs, relics, operator skins
- Then removed Baro inventory list from live page — now shows only timer + location
- `ITEM_NAMES` dict + `_item_name()` kept (still used by alerts/invasions/events)

### 5. Reliquary Layout Overhaul
- **Images moved to LEFT side** (were right) — removed `rq-img-left`/`rq-img-right` class system
- Rotation removed — images sit straight
- Text shadow on `.rq-detail-info` for readability over image
- Stats/info pushed to right side (`margin-left: auto`, `text-align: right`)
- Gradient divider constrained to 60% width under stat grid (full width on mobile)
- COMPONENTS section spacing increased (margin + label size)
- Stat label `0.55→0.65rem`, stat value `0.7→0.8rem`, bar height `3→4px`
- Image/info padding increased (16px each side)
- Grid gap increased for breathing room
- **Sprint undefined fix** — sentinel stats filtered for null values (Nautilus no longer shows "undefined")
- Image fade softened (`transparent 70%→85%`), position lowered (`top -30→-10px`)

---

## Key Files Changed
```
scripts/parse_worldstate.py       # +3 NW challenges, +MT_RETRIEVAL, +40 Baro items, void trader simplified
web/static/js/worldstate-parser.js # +MT_RETRIEVAL
web/static/js/reliquary.js        # TIER_ICONS, tierOrder, images left, sprint filter, no class toggling
web/static/reliquary.css           # images left, stat grid polish, divider alignment, text shadow, spacing
web/static/index.html              # removed Baro inventory table
web/static/live.css                # removed inventory-table/ducat-val/credit-val/live-card-wide CSS
```

---

## Pending / Known Issues
- **URL state / sharing** — not started
- **Sentinel stats** — companions_data.lua has stats but Reliquary sentinel classification doesn't map automatically
- **Mod images not yet wired into UI** — ready for mod picker redesign
- **Baro item names** — some guessed names may be wrong (Ki'Teer Archwing Skin, Primed Rubedo-Lined Barrel, Deimos Plushie, Prisma Shinai armor pieces, Nova Engineer operator set)

---

## Image Download Workflow
```bash
# On Windows (wiki blocks automated fetch from sandbox):
python scripts/fetch_images.py                        # all categories
python scripts/fetch_images.py --category arcanes     # single category
python scripts/fetch_images.py --resume               # skip existing
python scripts/fetch_mod_images.py --resume            # mods only
```

Manifests in `data/manifest_*.json` map names → wiki filenames.
Wiki URL pattern: `https://wiki.warframe.com/w/Special:Redirect/file/{filename}`

## Data Refresh Workflow
```bash
# On Windows (Playwright):
python scripts/fetch_wiki_playwright.py               # downloads .lua files

# Then parse:
python scripts/parse_lua.py                           # → weapons_raw.json, mods_raw.json
python scripts/parse_wiki_data.py                     # → weapons.json, mods.json, enemies.json
python scripts/parse_warframe_data.py                 # → warframes.json
python scripts/parse_relic_data.py                    # → relics.json
pytest                                                # verify
```

## Design Decisions Log
- Reliquary images on LEFT side, stats/info on RIGHT — no rotation
- Text shadow for readability over image
- Gradient divider only spans stat grid width (60%), full width on mobile
- Baro inventory list removed — timer + location only
- Eterna uses RequiemRelicIntact.png, Vanguard uses AxiRelicIntact.png
- Sprint stat hidden for sentinels (filtered null values)
- Real stat bars for warframes, placeholders for sentinels until data mapping solved
- Equal IPS splits are valid wiki data — not placeholders
- Mod images not yet wired into UI — ready for mod picker redesign
