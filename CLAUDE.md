# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Warframe Damage Calculator

## Project Goal
Create a Python-based damage calculator that accurately emulates in-game damage calculations per the official [Warframe Wiki — Damage/Calculation](https://wiki.warframe.com/w/Damage/Calculation), including full quantization to 1/32nd of base damage.

**Reference wiki:** https://wiki.warframe.com/w/Damage/Calculation

**NEVER use the Fandom wiki (warframe.fandom.com) — it is no longer updated. Always use the official wiki at wiki.warframe.com.**

**DATA SOURCE RULE: wiki.warframe.com is the ONLY permitted source for all Warframe game data, constants, formulas, and scraping. Never use third-party community tools, GitHub repos, or any other external source for game data — not even as a reference or fallback.**

## Technical Stack
- **Language:** Python 3.11+
- **Testing:** `pytest`
- **Data Source:** Warframe Wiki (official: wiki.warframe.com)
- **Alchemy Page:** React 18 + Vite + TypeScript + Tailwind + Framer Motion + Recharts + Lucide React
  - Build: `cd web/alchemy && npm install && npm run build` (outputs to `web/static/alchemy-dist/`)
  - All dependencies MIT/ISC licensed, no tracking/telemetry

## Commands
```bash
pip install pytest
pytest                              # run all tests
pytest tests/test_quantization.py  # run single file
pytest -k "test_viral_combo"        # run single test by name
```

## Project Structure
```
src/
  enums.py          # DamageType, FactionType, HealthType, ArmorType
  models.py         # Weapon, WeaponAttack, Mod, Enemy, DamageComponent dataclasses
  quantizer.py      # quantize(), quantize_cdm() — pure functions, no side effects
  arcanes.py        # weapon arcane presets — Merciless, Deadhead, Cascadia, Dexterity
  combiner.py       # elemental combination by mod slot order; innate primary/secondary split
  calculator.py     # DamageCalculator — 6-step pipeline + crit + armor + faction + Viral stacks + calculate_procs()
  loader.py         # load_weapon/mod/enemy from JSON; case-insensitive; headshot + attack selection
  scaling.py        # enemy level scaling: health/shield/armor/overguard formulas
  version.py        # APP_VERSION, GAME_DATA_VERSION — single source of truth
tests/
  test_quantization.py
  test_arcanes.py
  test_combiner.py
  test_co_curve.py    # Condition Overload curve: presence, monotonic increase, consistency
  test_loader.py
  test_calculator.py  # M7–M13 + TestCCProcs: modded damage, body part, faction, armor, crit, Viral stacks, secondary elemental mods, status procs
  test_scaling.py     # enemy level scaling: health/shield/armor/overguard per faction
data/
  weapons.json      # 588 weapons — multi-attack (attacks[]), per-attack IPS/innate/crit/status/shot_type, image
  mods.json         # 1405 mods — damage%, elemental%, ips%, cc/cd/sc/multishot, faction bonus, image field; Conclave excluded
  enemies.json      # 983 enemies — faction, health_type, armor_type, base_armor, base_level, base_health, base_shield, head_multiplier
  warframes.json    # 59 Prime entries — health, shield, armor, energy, sprint (warframes + archwing + companions)
  relics.json       # 732 relics — name, tier, vaulted, is_baro, introduced, rewards:[{item,part,rarity}]
  drops.json        # 34 active relics — keyed by relic name → [{location, mission_type, rotation, rarity, chance}]
                   #   Only unvaulted relics appear (vaulted ones don't drop from missions)
                   #   Auto-refreshed: server fetches CDN weekly via _drops_bg_loop() in api.py
                   #   Manual refresh: POST /api/refresh-drops (or re-save drops.html + run parse_drops.py)
                   #   CDN URL: warframe-web-assets.nyc3.cdn.digitaloceanspaces.com/uploads/cms/hnfvc0o3jnfvc873njb03enrf56.html
  warframes_data.lua   # raw wiki Lua — Module:Warframes/data
  companions_data.lua  # raw wiki Lua — Module:Companions/data
  arcanes_data.lua     # raw wiki Lua — Module:Arcane/data
  resources_data.lua   # raw wiki Lua — Module:Resources/data
  manifest_*.json      # 6 image download manifests (abilities, arcanes, damage_types, enemies, relics, resources)
scripts/
  parse_lua.py      # parses raw .lua module files downloaded from wiki
  parse_wiki_data.py # normalizes raw JSON → calculator-ready weapons.json/mods.json (multi-attack aware)
  parse_warframe_data.py # parses warframes_data.lua + companions_data.lua → warframes.json (59 Primes)
  fetch_wiki_data.py # (attempted) automated fetch — wiki blocks it, use browser instead
  fetch_wiki_playwright.py # Playwright-based fetcher — bypasses 403s using real Chromium; must run on Windows
                   #   Fetches weapons_data.lua, mods_data.lua, enemies_data.lua, void_data.lua
                   #   Handles both old stealth_async and new Stealth class playwright-stealth APIs
  fetch_mod_images.py # downloads mod card PNGs from wiki via Playwright (--resume, --limit)
  fetch_images.py   # universal batch image downloader — 6 categories (--category, --resume, --limit)
                   #   Categories: abilities, arcanes, enemies, damage_types, relics, resources
                   #   Reads manifest_*.json files; downloads to web/static/images/<category>/
  parse_relic_data.py # parses data/void_data.lua → data/relics.json (732 relics)
                   #   _extract_block() skips empty RelicData={} declaration (line 51) to find real data
  parse_drops.py    # parses drops HTML → relic drop dict; accepts Path or str (for server in-memory parsing)
                   #   BeautifulSoup4 state machine: mission header → rotation → item rows → blank-row
                   #   normalize_relic_name(): "Lith D7 Relic" → "Lith D7"; dedupes by (loc,type,rot,rarity,chance)
                   #   Raises ValueError (not sys.exit) on parse errors — server catches cleanly
  extract_data.lua  # Lua extraction script / wiki ApiSandbox one-liners
  parse_worldstate.py # worldstate parser: parse(raw); _parse_nightwave(raw); _parse_goals(raw) for anniversary gifts
                   #   _NW_NAMES + _NW_DESCRIPTIONS (~120 entries each); _NW_ELITE_NAMES/_NW_ELITE_DESCRIPTIONS for weekly/elite key collisions
                   #   Gifts of the Lotus: Goals array (Tag: Anniversary*TacAlert) → gift events; Alerts array (Tag: LotusGift) → regular alert rows
web/
  api.py            # FastAPI: GET /api/weapons|mods|enemies|warframes|version|relics|drops; POST /api/modded-weapon, /api/calculate, /api/scaled-enemy
                   #   GET /api/mods returns `effect` field (plain-text effect_raw) used by Alchemy Guide stat pills
                   #   GET /api/relics — optional query params: tier, vaulted, reward
                   #   GET /api/drops — relic drop locations (served from in-memory cache, disk fallback)
                   #   POST /api/refresh-drops — manual trigger to re-fetch drop tables from CDN
                   #   Background loops: _worldstate_bg_loop (60s), _drops_bg_loop (7 days)
                   #   All HTML routes served with Cache-Control: no-store
                   #   GET /favicon.ico → web/static/favicon.png (explicit route, StaticFiles would 404)
                   #   Routes: GET / → index.html (live tracker), GET /live → index.html (alias),
                   #           GET /calculator → calculator.html, GET /alchemy → alchemy-dist/index.html,
                   #           GET /reliquary → reliquary.html
  static/index.html # Live Data SPA — default page at /
                   #   .live-page-wrap: centering wrapper (no banner — removed)
                   #   header: .live-header-brand ("VOID CODEX" + .live-subtext "WORLD STATUS" glitch) left, .refresh-info right
                   #   .live-wrap → #live-news (News & Events panel) + #live-content (grid filled by renderAll())
                   #   renderAll(): gifts from Goals (is_gift:true) go to Active Events column; alerts + plain events also in Events column; no separate Alerts card
                   #   buildNewsEventsPanel(news, events, gifts): auto two-column when events/gifts present, single-column otherwise
                   #   relativeTime(iso): helper → "Xd/Xh/Xm ago"; news capped at 7 items; timestamp inline before title
                   #   Event rows: .event-row-header (title + timer same line); reward in crimson (.event-desc)
                   #   Nightwave rows: .nw-title-row (tag + title inline), desc below; .nw-right (rep + eta stacked)
                   #   Void Trader: timer + location only (inventory list removed); no live-card-wide class
  static/calculator.html # Damage Calculator SPA — at /calculator
                   #   stalker-dashboard layout: inner header + .content grid (1fr 480px) + right .sidebar
                   #   header: .live-header-brand "VOID CODEX" / "DAMAGE CALCULATOR" glitch subtext
                   #   .content-main: .we-panel-row (weapon panel + enemy panel side-by-side), Mods+Arcanes panel
                   #     Weapon/Enemy panels each have magnifier icon (picker-open-btn) in h2, hidden #weapon-search/#enemy-search inputs
                   #     #item-picker-overlay modal for weapon/enemy selection
                   #   .content-side: Results → Options → Calculate → Armor Strip
                   #   Mobile ≤600px: .we-panel-row stacks to 1-col (weapon first, enemy second)
  static/factions.html # Faction Weakness page — at /factions
                   #   Faction roster: single scrollable view, no matrix/no card grid
                   #   Groups: Grineer / Corpus / Infested / Other (each with group-color label)
                   #   Each .roster-entry: .roster-info (name, 180px) + .roster-dmg (weak/resist items only)
                   #   .dmg-item.dmg-weak: elem-color icon+glow+label+×1.5; .dmg-item.dmg-resist: crimson
                   #   Controls: search + type filter (all/vulnerable/resistant) + group filter
  static/factions.css  # Faction Weakness styles — .faction-roster, .roster-group, .roster-group-label
                   #   .roster-entry (flex row, faction-color left border + gradient bleed)
                   #   .roster-info, .roster-name, .roster-dmg, .dmg-sep
                   #   .dmg-item / .dmg-item.dmg-weak / .dmg-item.dmg-resist
  static/reliquary.html # Reliquary page — Prime Sets browser at /reliquary
                   #   Two-panel layout: .reliquary-wrap (grid: 260px sidebar + 1fr detail-outer)
                   #   Left .rq-sidebar: search + seg toggle (Warframes/Weapons) + set list
                   #   Right .rq-detail-outer (overflow:visible, padding-top:50px) → .rq-detail (scrollable)
                   #   Image breaks out of panel via .rq-detail-img on outer container (z-index:0, absolute)
                   #   All images on RIGHT side (.rq-img-right), tilted -8deg
                   #   EVERGREEN_SETS: 14 permanently unvaulted items — shown as green "Permanent" badge in type row
                   #   Stats: 2-column grid (.rq-stat-grid) with label+value+bar; real warframe stats from /api/warframes
                   #   Data derived client-side from /api/relics + /api/drops + /api/weapons + /api/warframes
                   #   Baro-only sets sorted to bottom with gold BARO tag badge
                   #   Set types: 'warframe' (Neuroptics/Chassis/Systems), 'sentinel' (Carapace/Cerebrum), 'weapon' (default)
                   #   Mobile ≤900px: set list always visible (no collapse), search shrinks to 100px
                   #   Mobile: scrollIntoView targets outer container so breakout image is visible
  static/reliquary.css  # Reliquary styles — glassmorphism panels, breakout image, stat grid
                   #   .rq-sidebar, .rq-detail: glass surface + top/bottom gradient lines
                   #   .rq-detail-outer: overflow:visible wrapper for breakout image
                   #   .rq-detail-img: absolute positioned LEFT, 240px, radial edge fade, no rotation
                   #   .rq-detail-info: max-width 60%, margin-left auto (right-aligned), text-shadow for readability
                   #   .rq-stat-grid: 2-col grid; .rq-stat-item: label+value+bar; .rq-badge-permanent: green pill
                   #   .rq-hero-divider: max-width 60%, margin-left auto (under stat grid only); full width on mobile
                   #   .rq-comp-*: inline expanded components with rounded pill headers + relic rows (14px radius)
                   #   Vertical gradient left border, horizontal gradient separators between components
                   #   .rq-baro-tag: gold badge; .rq-seg: 22px height matched to search field
                   #   Tier tokens: --tier-lith/meso/neo/axi/requiem/vanguard/eterna
                   #   Drop rows: grid (1fr auto auto auto); baro note: italic dim text
  static/live.css  # Live page styles — invasion .reward-chip colored by data-faction attr (Grineer/Corpus/Infested/other)
                   #   .live-page-wrap, .live-grid (dot bg), .refresh-info, .ne-* (News & Events layout)
                   #   .ne-body / .ne-body--split (1-col / 2-col grid), .ne-col, .ne-news, .ne-events
                   #   .ne-news-list li (flex row), .ne-news-link (inline-flex, 1rem), .ne-news-time (0.85rem dim, inline before title)
                   #   .event-row / .event-row--gift, .event-row-header (flex row: title left, eta right)
                   #   .event-desc now crimson; .event-row padding 6px 0
                   #   .nw-row: .nw-left (.nw-title-row tag+title inline, desc below) + .nw-right (rep above eta)
                   #   Brand/glitch styles now in layout.css (shared)
                   #   NOTE: alert banner (.alert-banner, .ab-*) was removed — do not re-add
  static/layout.css # Shared layout + .live-header-brand, .live-subtext, glitch keyframes (used on all pages)
                   #   .theme-switcher (flex row of dots in header) + .theme-dot[data-theme=*] styles
  static/panels.css # .we-panel-row replaces old .we-grid/.we-col; .picker-open-btn; .item-picker-item
                   #   .panel::before — top/bottom gradient lines (all themes via --panel-line-color)
                   #   body.theme-ash .panel::before — warm gold override
                   #   input[type=text] form styles are scoped to .panel — no global bleed
  static/js/
    constants.js   # all global state + data constants (ELEM_COLORS, TOOLTIPS, etc.)
    utils.js       # esc(), fmtNum(), dmgIcon(), initTooltips(), getCurrentWeapon/Enemy(), setupSelectDropdown(), togglePanelHelp()
    combobox.js    # setupCombobox(), clearCombobox(); setupPickerModal(), openPickerModal(),
                   #   closePickerModal(), renderPickerResults() — modal-based weapon/enemy picker
    weapons.js     # mod grid, picker, weapon stats, element badges, modded stats, special slots
                   #   selectIncarnonMode(mode) — toggles Normal/Incarnon attack; weapons with *incarnon* attacks
                   #   get a pill toggle instead of raw attack tabs
    reliquary.js   # Prime Sets browser — buildPrimeSets(), selectSet(), renderDetail()
                   #   State: allSets, dropsMap, baroRelicNames, weaponImages, weaponStats, warframeStats, wishlist, activeTab, searchQuery, selectedSet
                   #   TIER_ICONS: maps tier name → relic PNG (Vanguard→Axi, Eterna→Requiem)
                   #   EVERGREEN_SETS: const Set of 14 permanently unvaulted Prime items (2 frames + 12 weapons)
                   #   buildPrimeSets(relics): groups unvaulted relic rewards by item→parts→relics; flags baro-only sets
                   #     Type classification: sentinel (Carapace/Cerebrum), warframe (Neuroptics/Chassis/Systems), weapon (default)
                   #   renderSidebar(): filtered/searched set list; baro sets sorted to bottom with BARO tag
                   #   renderDetail(): breakout image on outer container + stat grid + inline components
                   #     Image placed on .rq-detail-outer (not inside scrollable panel) so it breaks out of card
                   #     All images LEFT side (no rotation), stats/info on RIGHT
                   #     Stats: 2-col grid with colored bars (weapons + warframes); sentinels filter null stats (no sprint)
                   #     Images: weapons from weaponImages map, warframes/sentinels by convention (Name-Prime.png)
                   #   renderDropList(relicName): top 5 drop locations; baro relics get Void Trader note
                   #   Wishlist: toggleWishlist(), removeGoal(), getGoalRelics(), calcBestMissions(), renderGoals()
                   #   Search: collapseSearch(forceClear) — click-away preserves query, X button clears
    enemy.js       # enemy panel, level scaling, Steel Path, Eximus
    modals.js      # Alchemy Guide, Riven Builder, Guide, Buffs
    armorstrip.js  # updateArmorStripDisplay(), getArmorStripPayload(), initArmorStrip()
    calculate.js   # runCalculation(), showResults(), showError()
    app.js         # loadData() bootstrap — uses setupPickerModal for weapon/enemy; DOMContentLoaded, version fetch
    factions.js    # renderRoster() — grouped roster; FACTION_GROUPS, FACTION_GROUP_COLORS
                   #   setFilter(), setGroup(), applyFilter() (composes search+type+group)
    theme.js       # theme switcher — applyTheme(name), initTheme(); localStorage key 'void-theme'
                   #   THEME_NAMES = ['stalker','jade','ash']; default = 'stalker' (no body class)
                   #   positionBackToTop(btn): reads sidebar.getBoundingClientRect().left, sets btn.style.right dynamically
                   #     handles .app max-width:1440px centering at any viewport width; also fires on resize
  static/images/
    weapons/       # 619 weapon PNGs — filenames from weapons.json `image` field
    mods/          # 1196 mod card PNGs — filenames from mods.json `image` field
    enemies/       # 899 enemy portrait PNGs — from manifest_enemies.json
    resources/     # 871 resource PNGs — from manifest_resources.json
    abilities/     # 216 warframe ability PNGs — convention: AbilityName130xWhite.png
    arcanes/       # 162 arcane PNGs — from manifest_arcanes.json
    warframes/     # 50 warframe PNGs — convention: Name-Prime.png (spaces→hyphens)
    damage_types/  # 12 damage type glyphs — convention: EssentialXGlyph.png
    sentinels/     # 6 sentinel PNGs — convention: Name-Prime.png (spaces→hyphens)
    relics/        # 5 relic tier PNGs — convention: XRelicIntact.png (missing: Eterna, Vanguard)
web/alchemy/              # Vite+React sub-app for Alchemy page
  package.json            # dependencies: react, framer-motion, recharts, lucide-react, tailwind
  vite.config.ts          # builds to web/static/alchemy-dist/; base: /static/alchemy-dist/
  tsconfig.json           # TypeScript config
  tailwind.config.js      # warframe theme colors (gold, accent, card, bg)
  postcss.config.js       # Tailwind + autoprefixer
  index.html              # Vite entry — full site shell (header, sidebar, burger, themes)
  src/
    main.tsx              # React entry point → #alchemy-root
    AlchemyPage.tsx       # page wrapper — 2-col grid (wheel+combiner left, analysis right)
    index.css             # Tailwind directives + hardware-card class
    data/elements.ts      # 10 elements (4 base + 6 combined), multiplier data per health type
    components/
      ElementalWheel.tsx        # circular element selector (inner: base, outer: combined)
      ElementalCombiner.tsx     # slot-based combiner (pick 2 base → result)
      MultiplierCard.tsx        # bar chart cards per category (Recharts)
      SelectedElementHeader.tsx # selected element display + component breakdown
run_web.py          # python run_web.py → dev server on port 8000
__main__.py         # python -m dc "Weapon" "Mod" vs "Enemy" [--crit avg|guaranteed|max] [--headshot] [--attack "Name"] [--list-attacks "Weapon"] [--version]
handoff.md          # session handoff notes for next Claude instance
web/static/theme-preview.html  # standalone theme/color preview page — open at /static/theme-preview.html
ARCHITECTURE.md     # detailed implementation notes — damage pipeline, CSS, live page, scaling formulas, etc.
skills/
  ui-ux-pro-max/SKILL.md  # design system guidance — auto-installed by session-start.sh
```

## Tests
Run `pytest` before committing. All tests must pass. **304 tests** as of v0.8.1.

## Data Refresh Notes
- `fetch_wiki_data.py` is blocked by the wiki (403). **Do not attempt automated fetch.**
- To refresh data: use `scripts/fetch_wiki_playwright.py` on Windows (sandbox has no internet):
  ```
  python scripts/fetch_wiki_playwright.py
  ```
  Downloads: `weapons_data.lua`, `mods_data.lua`, `enemies_data.lua`, `void_data.lua` into `data/`
- Then run parse scripts:
  1. `python scripts/parse_lua.py` → produces `weapons_raw.json` / `mods_raw.json`
  2. `python scripts/parse_wiki_data.py` → produces `weapons.json` / `mods.json`
  3. `python scripts/parse_warframe_data.py` → produces `warframes.json`
  4. `python scripts/parse_relic_data.py` → produces `relics.json`
  5. `git diff data/weapons.json` to review changes, then `pytest`
- **Note:** `parse_wiki_data.py` re-parse will overwrite hand-patched Galvanized mod fields in mods.json.
  After re-parse, run `python scripts/fix_galv_stats.py` to restore them.
- Fallback (if Playwright fails): open browser → download raw Lua manually from:
  - `https://wiki.warframe.com/w/Module:Weapons/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Mods/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Void/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Warframes/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Companions/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Arcane/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Resources/data?action=raw`
- Image refresh: `python scripts/fetch_images.py --resume` (all categories)
  or `python scripts/fetch_mod_images.py --resume` (mods only)
- New weapons appear in `Module:Weapons/data` a few days after in-game release. If a weapon is missing, check the module directly in browser first before debugging the parse pipeline.

## Versioning
`src/version.py` is the single source of truth:
```python
APP_VERSION       = "x.y.z"          # semver — bump before shipping features
GAME_DATA_VERSION = "Update NN — …"  # update when data files are refreshed
```
- `GET /api/version` returns `{"app": APP_VERSION, "game_data": GAME_DATA_VERSION}`
- CLI `--version` prints `Void Codex v{APP_VERSION} · {GAME_DATA_VERSION}`
- Guide modal footer shows both strings (fetched on DOMContentLoaded)
- **At the start of each new session, ask the user if the version should be bumped.**
- **User Guide:** When adding new features or panels to the Web UI, always update the Guide modal in `web/static/index.html` (`#guide-overlay`) to document the new functionality.

## Coding Standards
- **Accuracy first:** Mathematical correctness over speed or brevity.
- **Test before implement:** Write the `pytest` case from a wiki example, then write logic until it passes.
- **Pure functions:** `quantize()`, `combine()` must have no side effects.
- **Type hints** on all function signatures.
- **Short answers only.** Don't rewrite entire files — only the parts that need changing. Ask questions when uncertain.

## Critical Implementation Rules
- **Rounding:** NEVER use the built-in `round()` function. All rounding must use the `warframe_round` utility (Decimal + ROUND_HALF_UP) to prevent Banker's Rounding errors.
- **Quantization:** Apply quantization (scale of 1/32) to each damage type (Impact, Puncture, Slash, Elementals) individually before summing.
- **Precision:** Use `Decimal` or high-precision floats for intermediate steps to avoid floating-point drift.

## CSS / Web UI Rules (STRICT)
- **Dot background on ALL pages** — the dot grid (`radial-gradient(circle, var(--accent-a18) 1px, transparent 1px) / 20px 20px`) is defined once in `layout.css` on `.content, .live-wrap, .factions-wrap`. Every new page must use one of these wrappers — never add a new page without it.
- **New page checklist** — any new HTML page must: (1) use `.factions-wrap` or equivalent wrapper that gets the dot bg, (2) include `favicon.ico` link, (3) match sidebar nav markup from other pages, (4) have `Cache-Control: no-store` in api.py route.
- **No inline `style=` attributes** on HTML elements — all styles go to CSS classes. SVG presentation attributes excepted.
- **No hardcoded `rgba()` for theme colors** — use CSS variables.
- **No scan-line or noise overlays** — both removed. Do not re-add.
- **No panel radial glow** (`::after` removed) — do not re-add.
- **No global button box-shadow glow** — removed. Do not re-add.
- **No panel hover border-color change** — removed. Do not re-add.
- **No pure white text** — all themes use tinted off-whites for `--text` and `--text-primary`. See base.css per-theme values.
- **Theme accents** — Stalker = crimson (`#8b0000`→`#e53e3e`), Jade = teal (`#00897b`→`#00e5c8`), Ash = steel blue (`#466482`→`#7393b3`). Game-data colors stay as-is.
- **Panel lines** — use `--panel-line-top` (bright) and `--panel-line-bottom` (dim) — NOT the old `--panel-line-color`. Each theme defines both variables in `base.css`.
- **No panel top gradient line** — only the bottom line is active. Do not re-add the top line to `.panel::before`.
- **No dashed mod card borders** — `.mod-card.empty` uses solid border only.
- **Dropdowns must be fully opaque** — `--dropdown-bg` is a solid hex color; no `backdrop-filter` on `.combobox-dropdown`.
- **Mobile theme switcher** — lives in the sidebar footer (`sidebar-theme-switcher`), hidden in header at ≤900px. Do not put it back in the header on mobile.
- **Never use native `<select>` elements** — use `setupSelectDropdown()` in `utils.js` instead (iOS picker issue).
- **Fonts** — Exo 2 for headings/values, Rajdhani for labels/buttons. No Orbitron, no Share Tech Mono.
- **Theme system** — all color changes go in `base.css` `:root` (Stalker default) or `body.theme-jade` / `body.theme-ash` override blocks. Never hardcode colors outside these blocks.
- See `ARCHITECTURE.md` for full CSS variable list, class tables, and layout details.

## Git / Commit Notes
- The Cowork desktop app holds `index.lock` in the background, blocking sandbox git commits.
- If blocked: `del C:\Users\jesse\Desktop\codex\.git\index.lock` then retry.
- Commit from Windows PowerShell (run commands separately — `&&` not supported in PS):
  ```
  cd C:\Users\jesse\Desktop\codex
  git add <files>
  git commit -m "message"
  ```

## Private Notes
`accuracy-notes.md` — accuracy self-assessment covering what the calculator gets right, known gaps, and where confidence is lowest. Read on user request.

## UI/UX Skill
`ui-ux-pro-max` skill lives at `skills/ui-ux-pro-max/SKILL.md` in the repo.
Auto-installed to `~/.claude/skills/ui-ux-pro-max/` on every session via `session-start.sh`.
No manual transfer needed.
