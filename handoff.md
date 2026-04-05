# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** v0.8.1. Full damage pipeline, web UI, live tracker, reliquary, alchemy page.

**Branch:** `claude/review-handoff-docs-GK8Zj`

---

## What Was Done This Session

### 1. Recharts Removed from Alchemy
- Replaced Recharts bar charts with custom CSS bars + Framer Motion animations in `MultiplierCard.tsx`
- Each bar: gradient fill, glowing tip edge, staggered entrance animation, hover pulse, floating HUD tooltip
- Removed `recharts` from `package.json` (~45KB gzip savings)

### 2. Vanilla Alchemy Preview (Proof of Concept)
- Built `web/static/alchemy-preview.html` — full interactive preview with zero dependencies
- Elemental wheel (inner base + outer combined rings), decorative rings, rotating animation, glow pulses, shine sweeps
- Clicking an element updates banner + all 4 multiplier cards with animated bars
- Proves the entire Alchemy page can be ported from React to vanilla HTML/CSS/JS with identical output
- Custom element sigils attempted (geometric SVGs) — need redesign to better match Warframe aesthetic

### 3. Vanilla Port Decision
- Confirmed React/Vite sub-app is unnecessary — page data is tiny, interactions are simple
- Vanilla port would: eliminate build step, drop ~180KB bundle, remove npm dependency chain, match every other page
- Same pixels, same animations, same interactivity — just no build step
- **Decision: proceed with full vanilla port in next session**

---

## Key Files Changed
```
web/alchemy/package.json                    # removed recharts dependency
web/alchemy/src/components/MultiplierCard.tsx # custom CSS bars replacing Recharts
web/static/alchemy-preview.html             # vanilla proof-of-concept (wheel + cards)
```

---

## Pending / Known Issues
- **Alchemy vanilla port** — full port from React to vanilla HTML/CSS/JS (preview proves feasibility)
- **Element icons** — custom sigils need redesign; current geometric SVGs don't match Warframe feel. Options: use official wiki glyphs, or design better originals
- **Missing base element glyphs** — Cold, Electricity, Heat, Toxin PNGs not downloaded yet (run `fetch_images.py --category damage_types`)
- **Alchemy element data** — multiplier values may need wiki verification for accuracy
- **Alchemy page styling** — needs refinement to match Void Codex design system (fonts, panels, themes)
- **URL state / sharing** — not started
- **Sentinel stats** — companions_data.lua has stats but Reliquary sentinel classification doesn't map automatically
- **Mod images not yet wired into UI** — ready for mod picker redesign
- **Baro item names** — some guessed names may be wrong
- **Factions page** — files kept (factions.html, factions.css, factions.js) but route removed; could be deleted or kept as reference

---

## Alchemy Build Workflow (current — React)
```powershell
# On Windows (still needed until vanilla port is done):
cd C:\Users\jesse\Desktop\codex\web\alchemy
npm install          # first time only
npm run build        # outputs to web/static/alchemy-dist/
npm run dev          # dev server on port 3000 (proxies API to 8000)

# After build, commit the dist:
cd C:\Users\jesse\Desktop\codex
git add web/static/alchemy-dist/
git commit -m "Rebuild alchemy"
git push
```

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
- Reliquary images on LEFT side, stats/info on RIGHT — no rotation
- Reliquary image inside scroll panel (not on outer container) — fixes landscape float
- Landscape phones: nav sidebar collapses to burger, header scrolls away
- Alchemy page: currently React sub-app, planned vanilla port (preview at alchemy-preview.html)
- Recharts removed — custom CSS bars with Framer Motion (lighter, more thematic)
- Vanilla preview proves identical output with zero build step and ~95% less bundle weight
- /factions route replaced by /alchemy; factions files kept but unrouted
- Element icons: custom sigils attempted but need redesign; may use official wiki glyphs instead
