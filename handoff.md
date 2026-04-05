# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** v0.8.1. Full damage pipeline, web UI, live tracker, reliquary, alchemy page (vanilla).

**Branch:** `claude/review-handoff-docs-GK8Zj`

---

## What Was Done This Session

### 1. Recharts Removed from Alchemy React App
- Replaced Recharts bar charts with custom CSS bars + Framer Motion in `MultiplierCard.tsx`
- Each bar: gradient fill, glowing tip edge, staggered entrance animation, hover pulse, floating HUD tooltip
- Removed `recharts` from `package.json` (~45KB gzip savings)

### 2. Full Vanilla Port of Alchemy Page (COMPLETE)
- **Replaced** the React/Vite sub-app with vanilla HTML/CSS/JS — zero build step
- `web/static/alchemy.html` — full site shell (header, sidebar, nav, themes, burger)
- `web/static/alchemy.css` — wheel, combiner, cards, banner, tactic tip, responsive
- `web/static/js/alchemy.js` — element data, wheel builder, combiner logic, bar animations, banner, tactic tips
- `web/api.py` — `/alchemy` route now serves `alchemy.html` directly (was `alchemy-dist/index.html`)
- Bundle: ~8KB total vs ~180KB React build. No npm install, no npm run build, no Vite dev server
- Same visual output: wheel with glow/spin/shine, combiner, animated bars, element banner

### 3. Element Icons (Custom SVGs)
- Designed recognizable stroke-only SVG icons for all 10 elements (24x24 viewBox, 2px stroke)
- Cold: snowflake with barbs, Electricity: bolt with sparks, Heat: double flame
- Toxin: droplet with bubbles, Corrosive: broken ring with acid drips
- Radiation: trefoil sectors, Viral: DNA double helix, Magnetic: horseshoe magnet
- Gas: rising vapor wisps, Blast: 8-ray starburst
- Icons are functional placeholders — user plans to create their own custom graphics later

### 4. Vanilla Preview File
- `web/static/alchemy-preview.html` — standalone proof-of-concept (predates the full port)
- Can be kept for reference or deleted — the main `alchemy.html` supersedes it

---

## Key Files Changed
```
# Vanilla alchemy (NEW — replaces React app)
web/static/alchemy.html              # full page with site shell
web/static/alchemy.css               # all alchemy-specific styles
web/static/js/alchemy.js             # element data, wheel, combiner, cards, banner
web/api.py                           # /alchemy serves alchemy.html (was alchemy-dist)

# React app changes (still exists but no longer served)
web/alchemy/package.json             # removed recharts dependency
web/alchemy/src/components/MultiplierCard.tsx  # custom CSS bars (unused now)

# Preview
web/static/alchemy-preview.html      # standalone PoC (superseded)
```

---

## Pending / Known Issues
- **Element icons** — current SVGs are functional placeholders; user wants to create custom graphics (can swap icon strings in alchemy.js)
- **Missing base element glyphs** — Cold, Electricity, Heat, Toxin PNGs not downloaded (run `fetch_images.py --category damage_types`)
- **React app cleanup** — DONE, deleted `web/alchemy/` + `web/static/alchemy-dist/`
- **Alchemy element data** — multiplier values may need wiki verification for accuracy
- **Alchemy page styling** — could use further refinement to match Void Codex design system
- **URL state / sharing** — not started
- **Sentinel stats** — companions_data.lua has stats but Reliquary sentinel classification doesn't map automatically
- **Mod images not yet wired into UI** — ready for mod picker redesign
- **Baro item names** — some guessed names may be wrong
- **Factions page** — files kept (factions.html, factions.css, factions.js) but route removed; could be deleted

---

## Image Download Workflow
```bash
# On Windows (wiki blocks automated fetch from sandbox):
python scripts/fetch_images.py                        # all categories
python scripts/fetch_images.py --category arcanes     # single category
python scripts/fetch_images.py --resume               # skip existing
python scripts/fetch_mod_images.py --resume            # mods only
```

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
- Alchemy page: fully vanilla (HTML/CSS/JS) — React/Vite sub-app replaced, no build step
- Element icons: custom stroke-only SVGs in alchemy.js, user plans to make their own later
- Recharts removed — custom CSS bars with gradient fill + glowing tips
- Vanilla port identical visual output to React version with ~95% less bundle weight
- Reliquary images on LEFT side, stats/info on RIGHT — no rotation
- Reliquary image inside scroll panel (not on outer container) — fixes landscape float
- Landscape phones: nav sidebar collapses to burger, header scrolls away
- /factions route replaced by /alchemy; factions files kept but unrouted
