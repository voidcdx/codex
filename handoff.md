# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** v0.8.1. Full damage pipeline, web UI, live tracker, reliquary, alchemy page.

**Branch:** `claude/continue-handoff-docs-jT3f0`

---

## What Was Done This Session

### 1. Reliquary Mobile Landscape Fix
- Image was on `.rq-detail-outer` (outside scroll container) — floated over content on landscape phones
- Moved image inside `.rq-detail` via JS (`detail.innerHTML`) so it scrolls with content
- `.rq-detail-outer`: `overflow: hidden`, `padding-top: 0` (image no longer breaks out)
- Landscape phones (max-height 600px): image scaled to 130px
- Image lowered from `top: -10px` → `top: 12px` for breathing room

### 2. Landscape Phone Responsive Fixes (all pages)
- Nav sidebar collapses to burger on landscape phones (`orientation: landscape` + `max-height: 600px`)
- Added to `layout.css`: burger shows, sidebar slides from right, header theme switcher hidden
- iOS Safari address bar collapse: extended `html`/`body` overflow rules in `base.css` to landscape
- `.app`/`.main` set to `height: auto`/`overflow: visible` on landscape (same as portrait mobile)
- Reliquary wrap gets explicit `height: calc(100dvh - 40px)` to keep panel scrolling

### 3. Alchemy Page (NEW — replaces /factions)
- **Vite + React build pipeline** added at `web/alchemy/`
- Dependencies: React, Framer Motion, Recharts, Lucide React, Tailwind CSS (all MIT/ISC, no tracking)
- Components: ElementalWheel (circular selector), ElementalCombiner (slot-based), MultiplierCard (bar charts), SelectedElementHeader
- Data: `elements.ts` — 10 elements (4 base + 6 combined) with multipliers per health type
- Full Void Codex site shell: header, sidebar nav, burger, themes, dot background
- Nav links updated on all pages: Factions → Alchemy (flask icon)
- Route: `/factions` → `/alchemy` in `api.py`, serves `alchemy-dist/index.html`
- Responsive: wheel scales to `80vw` on small screens, 2-col → 1-col grid
- Copyright headers added to all source files
- Build: user runs `cd web\alchemy && npm install && npm run build` on Windows

### 4. Version Bump
- `0.8.0` → `0.8.1`

---

## Key Files Changed
```
# Landscape / mobile fixes
web/static/reliquary.css           # image inside panel, landscape sizing, overflow hidden
web/static/js/reliquary.js         # image moved into detail.innerHTML
web/static/layout.css              # landscape burger, sidebar collapse, header scroll
web/static/base.css                # landscape html/body overflow for iOS Safari

# Alchemy page (new)
web/alchemy/                       # Vite project root
  package.json                     # dependencies + build scripts
  vite.config.ts                   # builds to web/static/alchemy-dist/
  tsconfig.json                    # TypeScript config
  tailwind.config.js               # warframe theme colors
  postcss.config.js                # Tailwind + autoprefixer
  index.html                       # full site shell (header, sidebar, burger)
  src/
    main.tsx                       # React entry point
    AlchemyPage.tsx                # page wrapper component
    index.css                      # Tailwind directives + hardware-card
    data/elements.ts               # element data + types
    components/
      ElementalWheel.tsx           # circular element selector
      ElementalCombiner.tsx        # slot-based combiner
      MultiplierCard.tsx           # bar chart cards (Recharts)
      SelectedElementHeader.tsx    # selected element display

web/static/alchemy-dist/          # built output (committed)
web/api.py                        # /factions → /alchemy route
web/static/calculator.html        # nav: Factions → Alchemy
web/static/reliquary.html         # nav: Factions → Alchemy
web/static/index.html             # nav: Factions → Alchemy
web/static/factions.html          # nav: Factions → Alchemy (kept but unrouted)
src/version.py                    # 0.8.0 → 0.8.1
.gitignore                        # +web/alchemy/node_modules/
```

---

## Pending / Known Issues
- **Alchemy page styling** — needs further refinement to fully match Void Codex design system (colors, fonts, panel styles)
- **Alchemy element data** — multiplier values may need wiki verification for accuracy
- **URL state / sharing** — not started
- **Sentinel stats** — companions_data.lua has stats but Reliquary sentinel classification doesn't map automatically
- **Mod images not yet wired into UI** — ready for mod picker redesign
- **Baro item names** — some guessed names may be wrong
- **Factions page** — files kept (factions.html, factions.css, factions.js) but route removed; could be deleted or kept as reference

---

## Alchemy Build Workflow
```powershell
# On Windows:
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
- Alchemy page: React sub-app with Vite build, mounted inside vanilla site shell
- Alchemy dependencies: React, Framer Motion, Recharts, Lucide, Tailwind — all MIT/ISC, no tracking
- /factions route replaced by /alchemy; factions files kept but unrouted
- Copyright headers on all alchemy source files
