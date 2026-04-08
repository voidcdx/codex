# CLAUDE.md

# Warframe Damage Calculator

## Project Goal
Python-based damage calculator emulating in-game calculations per the [Warframe Wiki — Damage/Calculation](https://wiki.warframe.com/w/Damage/Calculation), including full quantization to 1/32nd of base damage.

**NEVER use the Fandom wiki (warframe.fandom.com) — always use wiki.warframe.com.**

**DATA SOURCE RULE: wiki.warframe.com is the ONLY permitted source for game data, constants, and formulas. No third-party tools, GitHub repos, or other external sources.**

## Technical Stack
- **Language:** Python 3.11+
- **Testing:** `pytest`
- **Alchemy Page:** Vanilla HTML/CSS/JS — `web/static/alchemy.html` + `alchemy.css` + `js/alchemy.js`

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
  calculator.py     # DamageCalculator — 6-step pipeline + crit + armor + faction + Viral stacks
  loader.py         # load_weapon/mod/enemy from JSON; case-insensitive; headshot + attack selection
  scaling.py        # enemy level scaling: health/shield/armor/overguard formulas
  version.py        # APP_VERSION, GAME_DATA_VERSION — single source of truth
tests/
  test_quantization.py
  test_arcanes.py
  test_combiner.py
  test_co_curve.py
  test_loader.py
  test_calculator.py
  test_scaling.py
data/
  weapons.json      # weapons — multi-attack, per-attack IPS/innate/crit/status/shot_type, image
  mods.json         # mods — damage%, elemental%, cc/cd/sc/multishot, faction bonus, image; Conclave excluded
  enemies.json      # enemies — faction, health_type, armor_type, base stats, head_multiplier
  warframes.json    # Prime warframes + sentinels + archwing — health, shield, armor, energy, sprint
  relics.json       # relics — name, tier, vaulted, is_baro, rewards:[{item,part,rarity}]
  drops.json        # active relic drop locations — auto-refreshed weekly from CDN; manual: POST /api/refresh-drops
  nightwave_acts.json  # REFERENCE ONLY — wiki-scraped NW acts [{name,description,tier}]
                       # Grep to resolve new CamelCase keys → add to _NW_NAMES/_NW_DESCRIPTIONS in parse_worldstate.py
  warframes_data.lua   # raw wiki Lua — Module:Warframes/data
  companions_data.lua  # raw wiki Lua — Module:Companions/data
  arcanes_data.lua     # raw wiki Lua — Module:Arcane/data
  resources_data.lua   # raw wiki Lua — Module:Resources/data
  manifest_*.json      # image download manifests (abilities, arcanes, damage_types, enemies, relics, resources)
scripts/
  parse_lua.py             # raw .lua → weapons_raw.json / mods_raw.json
  parse_wiki_data.py       # weapons_raw/mods_raw → weapons.json / mods.json / enemies.json
  parse_warframe_data.py   # warframes_data.lua + companions_data.lua → warframes.json
  parse_relic_data.py      # void_data.lua → relics.json
  parse_drops.py           # drops HTML → relic drop dict
  parse_worldstate.py      # worldstate parser — _NW_NAMES/_NW_DESCRIPTIONS (169/167 entries), Nightwave, gifts
  fetch_wiki_playwright.py # Playwright fetcher (Windows only) — downloads all .lua files; bypasses wiki 403s
  fetch_wiki_data.py       # BLOCKED by wiki (403) — do not use
  fetch_images.py          # batch image downloader — 6 categories (--category, --resume, --limit)
  fetch_mod_images.py      # mod card PNG downloader (--resume, --limit)
  fix_galv_stats.py        # re-patches Galvanized mod fields after parse_wiki_data.py overwrites them
  extract_data.lua         # Lua extraction script / wiki ApiSandbox one-liners
web/
  api.py            # FastAPI server
                   #   GET /api/weapons|mods|enemies|warframes|version|relics|drops
                   #   POST /api/modded-weapon, /api/calculate, /api/scaled-enemy, /api/refresh-drops
                   #   Routes: / and /live → index.html, /calculator, /alchemy, /reliquary
                   #   Background: _worldstate_bg_loop (60s), _drops_bg_loop (7 days)
                   #   r.encoding = 'utf-8' required for CDN HTML — no charset in Content-Type
  static/index.html      # Live Data SPA — worldstate: alerts, events, gifts, Nightwave, Void Trader, news
  static/calculator.html # Damage Calculator SPA
  static/reliquary.html  # Prime Sets browser — sidebar set list + detail panel with stats + relic components
  static/alchemy.html    # Alchemy page — elemental wheel, combiner, faction effectiveness cards
  static/reliquary.css   # Reliquary styles — glassmorphism, breakout image, stat grid, tier tokens
  static/alchemy.css     # Alchemy styles — wheel, combiner, faction cards; glassmorphism via .panel
  static/live.css        # Live page styles
  static/layout.css      # Shared layout, brand/glitch styles, .page-wrap (dot bg), theme switcher
  static/panels.css      # .panel, .we-panel-row, .picker-open-btn, form input scoping
  static/js/
    constants.js   # global state + data constants
    utils.js       # esc(), fmtNum(), dmgIcon(), initTooltips(), setupSelectDropdown(), togglePanelHelp()
    combobox.js    # setupCombobox(), setupPickerModal(), openPickerModal(), renderPickerResults()
    weapons.js     # mod grid, weapon stats, element badges, Incarnon mode toggle
    reliquary.js   # buildPrimeSets(), selectSet(), renderDetail(), wishlist, renderDropList()
    enemy.js       # enemy panel, level scaling, Steel Path, Eximus
    modals.js      # Alchemy Guide, Riven Builder, Guide, Buffs
    armorstrip.js  # updateArmorStripDisplay(), getArmorStripPayload(), initArmorStrip()
    calculate.js   # runCalculation(), showResults(), showError()
    app.js         # loadData() bootstrap — DOMContentLoaded, version fetch
    alchemy.js     # ELEMENTS data + FACTION_META (13 factions), buildWheel(), renderCards() — 2 faction panels
    theme.js       # applyTheme(), initTheme(); themes: stalker (default), jade, ash
  static/images/
    weapons/       # weapon PNGs — filenames from weapons.json `image` field
    mods/          # mod card PNGs — filenames from mods.json `image` field
    warframes/     # warframe PNGs — convention: Name-Prime.png
    sentinels/     # sentinel PNGs — convention: Name-Prime.png
    enemies/       # enemy portrait PNGs
    abilities/     # warframe ability PNGs — convention: AbilityName130xWhite.png
    arcanes/       # arcane PNGs
    relics/        # relic tier PNGs — convention: XRelicIntact.png
    damage_types/  # damage type glyphs — convention: EssentialXGlyph.png
    resources/     # resource PNGs
run_web.py        # python run_web.py → dev server on port 8000
__main__.py       # python -m dc "Weapon" "Mod" vs "Enemy" [--crit] [--headshot] [--attack] [--version]
HANDOFF.md        # session handoff notes — start each session with git pull
ARCHITECTURE.md   # detailed implementation notes — pipeline, CSS variables, layout, scaling formulas
skills/
  ui-ux-pro-max/SKILL.md  # design system guidance
```

## Tests
Run `pytest` before committing. All tests must pass. **304 tests** as of v0.8.1.

## Data Refresh
```bash
# 1. Fetch (Windows + Playwright):
python scripts/fetch_wiki_playwright.py   # → weapons_data.lua, mods_data.lua, enemies_data.lua, void_data.lua

# 2. Parse (in order):
python scripts/parse_lua.py              # → weapons_raw.json, mods_raw.json
python scripts/parse_wiki_data.py        # → weapons.json, mods.json, enemies.json
python scripts/parse_warframe_data.py    # → warframes.json
python scripts/parse_relic_data.py       # → relics.json
python scripts/fix_galv_stats.py         # restore Galvanized mod fields
pytest

# 3. Bump: src/version.py → GAME_DATA_VERSION = "Update NN — Name"
```

**Fallback** (if Playwright fails) — download raw Lua manually in browser:
- `wiki.warframe.com/w/Module:Weapons/data?action=raw`
- `wiki.warframe.com/w/Module:Mods/data?action=raw`
- `wiki.warframe.com/w/Module:Void/data?action=raw`
- `wiki.warframe.com/w/Module:Warframes/data?action=raw`
- `wiki.warframe.com/w/Module:Companions/data?action=raw`

**Images:** `python scripts/fetch_images.py --resume` or `python scripts/fetch_mod_images.py --resume`

**New weapons** appear in `Module:Weapons/data` a few days after in-game release — check the module in browser before debugging the pipeline.

## Versioning
`src/version.py` is the single source of truth:
```python
APP_VERSION       = "x.y.z"
GAME_DATA_VERSION = "Update NN — …"
```
- `GET /api/version` → `{"app": APP_VERSION, "game_data": GAME_DATA_VERSION}`
- **At the start of each new session, ask the user if the version should be bumped.**
- When adding new UI features, update the Guide modal in `web/static/index.html` (`#guide-overlay`).

## Coding Standards
- **Accuracy first** — correctness over speed or brevity
- **Test before implement** — write the `pytest` case from a wiki example, then write logic until it passes
- **Pure functions** — `quantize()`, `combine()` must have no side effects
- **Type hints** on all function signatures
- **Short answers only** — don't rewrite entire files; only change what's needed

## Critical Implementation Rules
- **Rounding:** NEVER use `round()` — use `warframe_round` (Decimal + ROUND_HALF_UP)
- **Quantization:** Apply 1/32 scale to each damage type individually before summing
- **Precision:** Use `Decimal` or high-precision floats for intermediate steps

## CSS / Web UI Rules (STRICT)
- **Dot background on ALL pages** — use `.page-wrap`, `.live-wrap`, or `.content` wrapper (defined in `layout.css`)
- **New page checklist** — (1) dot bg wrapper, (2) favicon link, (3) sidebar nav markup, (4) `Cache-Control: no-store` in api.py
- **No inline `style=` attributes** — all styles in CSS classes (SVG presentation attributes excepted)
- **No hardcoded `rgba()` for theme colors** — use CSS variables
- **No scan-line/noise overlays, panel radial glow, global button glow, panel hover border changes** — all removed, do not re-add
- **No pure white text** — all themes use tinted off-whites
- **Theme accents** — Stalker = crimson, Jade = teal, Ash = steel blue
- **Panel lines** — use `--panel-line-top` / `--panel-line-bottom` from `base.css`; no top line on `.panel::before`
- **No dashed mod card borders** — `.mod-card.empty` solid border only
- **Dropdowns fully opaque** — `--dropdown-bg` is solid hex; no `backdrop-filter` on `.combobox-dropdown`
- **Mobile theme switcher** — sidebar footer only (`sidebar-theme-switcher`), hidden in header at ≤900px
- **Never use native `<select>`** — use `setupSelectDropdown()` in `utils.js`
- **Fonts** — Exo 2 (headings/values), Rajdhani (labels/buttons). No Orbitron, no Share Tech Mono
- **Theme system** — colors in `base.css` `:root` (Stalker) or `body.theme-jade` / `body.theme-ash` blocks only
- See `ARCHITECTURE.md` for full CSS variable list and layout details

## Git / Commit Notes
- Cowork desktop app may hold `index.lock` — if blocked: `del C:\Users\jesse\Desktop\codex\.git\index.lock`
- **Always `git pull` at the start of each session** to avoid merge conflicts with Cowork pushes
- Commits stay local (no push needed) unless Cowork or user explicitly pushes to GitHub

## Private Notes
`accuracy-notes.md` — accuracy self-assessment, known gaps, confidence levels. Read on user request.

## UI/UX Skill
`skills/ui-ux-pro-max/SKILL.md` — auto-installed to `~/.claude/skills/ui-ux-pro-max/` via `session-start.sh`.
