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
  mods.json         # 1405 mods — damage%, elemental%, ips%, cc/cd/sc/multishot, faction bonus; Conclave mods excluded
  enemies.json      # 983 enemies — faction, health_type, armor_type, base_armor, base_level, base_health, base_shield, head_multiplier
  relics.json       # 732 relics — name, tier, vaulted, is_baro, introduced, rewards:[{item,part,rarity}]
scripts/
  parse_lua.py      # parses raw .lua module files downloaded from wiki
  parse_wiki_data.py # normalizes raw JSON → calculator-ready weapons.json/mods.json (multi-attack aware)
  fetch_wiki_data.py # (attempted) automated fetch — wiki blocks it, use browser instead
  fetch_wiki_playwright.py # Playwright-based fetcher — bypasses 403s using real Chromium; must run on Windows
                   #   Fetches weapons_data.lua, mods_data.lua, enemies_data.lua, void_data.lua
                   #   Handles both old stealth_async and new Stealth class playwright-stealth APIs
  parse_relic_data.py # parses data/void_data.lua → data/relics.json (732 relics)
                   #   _extract_block() skips empty RelicData={} declaration (line 51) to find real data
  extract_data.lua  # Lua extraction script / wiki ApiSandbox one-liners
  parse_worldstate.py # worldstate parser: parse(raw); _parse_nightwave(raw); _parse_goals(raw) for anniversary gifts
                   #   _NW_NAMES + _NW_DESCRIPTIONS (~120 entries each); _NW_ELITE_NAMES/_NW_ELITE_DESCRIPTIONS for weekly/elite key collisions
                   #   Gifts of the Lotus: Goals array (Tag: Anniversary*TacAlert) → gift events; Alerts array (Tag: LotusGift) → regular alert rows
web/
  api.py            # FastAPI: GET /api/weapons|mods|enemies|version|relics; POST /api/modded-weapon, /api/calculate, /api/scaled-enemy
                   #   GET /api/mods returns `effect` field (plain-text effect_raw) used by Alchemy Guide stat pills
                   #   GET /api/relics — optional query params: tier, vaulted, reward
                   #   All HTML routes served with Cache-Control: no-store
                   #   GET /favicon.ico → web/static/favicon.png (explicit route, StaticFiles would 404)
                   #   Routes: GET / → index.html (live tracker), GET /live → index.html (alias),
                   #           GET /calculator → calculator.html, GET /factions → factions.html,
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
  static/reliquary.html # Reliquary page — at /reliquary
                   #   Controls: search row (search input 320px + count) + filter row (tier pills + vault segmented)
                   #   Tier pills: All / Lith / Meso / Neo / Axi / Requiem — each tier gets its color when active
                   #   Vault seg: All / Unvaulted / Vaulted
                   #   Grid: .relic-grid auto-fill minmax(280px, 1fr) inside .factions-wrap
                   #   NOTE: large empty space to the right of cards is an unresolved layout bug
  static/reliquary.css  # Reliquary styles — tier color tokens (:root), controls, tier pills, vault seg,
                   #   .relic-card (data-tier attr drives tier bar + badge color), reward rows with rarity dots
                   #   Tier tokens: --tier-lith/meso/neo/axi/requiem/vanguard
  static/live.css  # Live page styles — .live-page-wrap, .live-grid (dot bg), .refresh-info, .ne-* (News & Events layout)
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
  static/js/
    constants.js   # all global state + data constants (ELEM_COLORS, TOOLTIPS, etc.)
    utils.js       # esc(), fmtNum(), dmgIcon(), initTooltips(), getCurrentWeapon/Enemy(), setupSelectDropdown(), togglePanelHelp()
    combobox.js    # setupCombobox(), clearCombobox(); setupPickerModal(), openPickerModal(),
                   #   closePickerModal(), renderPickerResults() — modal-based weapon/enemy picker
    weapons.js     # mod grid, picker, weapon stats, element badges, modded stats, special slots
                   #   selectIncarnonMode(mode) — toggles Normal/Incarnon attack; weapons with *incarnon* attacks
                   #   get a pill toggle instead of raw attack tabs
    reliquary.js   # relic browser — loadRelics(), renderGrid(), matchesSearch(), renderCard()
                   #   setTier(btn), setVault(btn), clearSearch() — filter state: activeTier/activeVault/searchQuery
    enemy.js       # enemy panel, level scaling, Steel Path, Eximus
    modals.js      # Alchemy Guide, Riven Builder, Guide, Buffs
    armorstrip.js  # updateArmorStripDisplay(), getArmorStripPayload(), initArmorStrip()
    calculate.js   # runCalculation(), showResults(), showError()
    app.js         # loadData() bootstrap — uses setupPickerModal for weapon/enemy; DOMContentLoaded, version fetch
    factions.js    # renderRoster() — grouped roster; FACTION_GROUPS, FACTION_GROUP_COLORS
                   #   setFilter(), setGroup(), applyFilter() (composes search+type+group)
    theme.js       # theme switcher — applyTheme(name), initTheme(); localStorage key 'void-theme'
                   #   THEME_NAMES = ['stalker','jade','ash']; default = 'stalker' (no body class)
run_web.py          # python run_web.py → dev server on port 8000
__main__.py         # python -m dc "Weapon" "Mod" vs "Enemy" [--crit avg|guaranteed|max] [--headshot] [--attack "Name"] [--list-attacks "Weapon"] [--version]
handoff.md          # session handoff notes for next Claude instance
web/static/theme-preview.html  # standalone theme/color preview page — open at /static/theme-preview.html
ARCHITECTURE.md     # detailed implementation notes — damage pipeline, CSS, live page, scaling formulas, etc.
skills/
  ui-ux-pro-max/SKILL.md  # design system guidance — auto-installed by session-start.sh
```

## Tests
Run `pytest` before committing. All tests must pass. **304 tests** as of v0.7.0.

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
  3. `python scripts/parse_relic_data.py` → produces `relics.json`
  4. `git diff data/weapons.json` to review changes, then `pytest`
- Fallback (if Playwright fails): open browser → download raw Lua manually from:
  - `https://wiki.warframe.com/w/Module:Weapons/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Mods/data?action=raw`
  - `https://wiki.warframe.com/w/Module:Void/data?action=raw`
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
- **Fonts** — Orbitron for headings/values, Rajdhani for labels/buttons. No Share Tech Mono.
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
