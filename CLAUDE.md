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
scripts/
  parse_lua.py      # parses raw .lua module files downloaded from wiki
  parse_wiki_data.py # normalizes raw JSON → calculator-ready weapons.json/mods.json (multi-attack aware)
  fetch_wiki_data.py # (attempted) automated fetch — wiki blocks it, use browser instead
  extract_data.lua  # Lua extraction script / wiki ApiSandbox one-liners
  parse_worldstate.py # worldstate parser: parse(raw); _parse_nightwave(raw); _parse_goals(raw) for anniversary gifts
                   #   _NW_NAMES + _NW_DESCRIPTIONS (~120 entries each); _NW_ELITE_NAMES/_NW_ELITE_DESCRIPTIONS for weekly/elite key collisions
                   #   Gifts of the Lotus: Goals array (Tag: Anniversary*TacAlert) → gift events; Alerts array (Tag: LotusGift) → regular alert rows
web/
  api.py            # FastAPI: GET /api/weapons|mods|enemies|version; POST /api/modded-weapon, /api/calculate, /api/scaled-enemy
                   #   GET /api/mods returns `effect` field (plain-text effect_raw) used by Alchemy Guide stat pills
                   #   All HTML routes served with Cache-Control: no-store
                   #   GET /favicon.ico → web/static/favicon.png (explicit route, StaticFiles would 404)
                   #   Routes: GET / → index.html (live tracker), GET /live → index.html (alias),
                   #           GET /calculator → calculator.html, GET /factions → factions.html
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
                   #   header: .live-header-brand "VOID CODEX" / "FACTION WEAKNESS" glitch subtext
  static/live.css  # Live page styles — .live-page-wrap, .live-grid (dot bg), .refresh-info, .ne-* (News & Events layout)
                   #   .ne-body / .ne-body--split (1-col / 2-col grid), .ne-col, .ne-news, .ne-events
                   #   .ne-news-list li (flex row), .ne-news-link (inline-flex, 1rem), .ne-news-time (0.85rem dim, inline before title)
                   #   .event-row / .event-row--gift, .event-row-header (flex row: title left, eta right)
                   #   .event-desc now crimson; .event-row padding 6px 0
                   #   .nw-row: .nw-left (.nw-title-row tag+title inline, desc below) + .nw-right (rep above eta)
                   #   Brand/glitch styles now in layout.css (shared)
                   #   NOTE: alert banner (.alert-banner, .ab-*) was removed — do not re-add
  static/layout.css # Shared layout + .live-header-brand, .live-subtext, glitch keyframes (used on all pages)
  static/panels.css # .we-panel-row replaces old .we-grid/.we-col; .picker-open-btn; .item-picker-item
  static/js/
    constants.js   # all global state + data constants (ELEM_COLORS, TOOLTIPS, etc.)
    utils.js       # esc(), fmtNum(), dmgIcon(), initTooltips(), getCurrentWeapon/Enemy(), setupSelectDropdown(), togglePanelHelp()
    combobox.js    # setupCombobox(), clearCombobox(); setupPickerModal(), openPickerModal(),
                   #   closePickerModal(), renderPickerResults() — modal-based weapon/enemy picker
    weapons.js     # mod grid, picker, weapon stats, element badges, modded stats, special slots
    enemy.js       # enemy panel, level scaling, Steel Path, Eximus
    modals.js      # Alchemy Guide, Riven Builder, Guide, Buffs
    armorstrip.js  # updateArmorStripDisplay(), getArmorStripPayload(), initArmorStrip()
    calculate.js   # runCalculation(), showResults(), showError()
    app.js         # loadData() bootstrap — uses setupPickerModal for weapon/enemy; DOMContentLoaded, version fetch
run_web.py          # python run_web.py → dev server on port 8000
__main__.py         # python -m dc "Weapon" "Mod" vs "Enemy" [--crit avg|guaranteed|max] [--headshot] [--attack "Name"] [--list-attacks "Weapon"] [--version]
handoff.md          # session handoff notes for next Claude instance
ARCHITECTURE.md     # detailed implementation notes — damage pipeline, CSS, live page, scaling formulas, etc.
```

## Tests
Run `pytest` before committing. All tests must pass. **304 tests** as of v0.5.8.

## Data Refresh Notes
- `fetch_wiki_data.py` is blocked by the wiki (403). **Do not attempt automated fetch.**
- To refresh data: open browser → download raw Lua modules manually → run parse scripts.
  1. `https://wiki.warframe.com/w/Module:Weapons/data?action=raw` → save as `data/weapons_data.lua`
  2. `https://wiki.warframe.com/w/Module:Mods/data?action=raw` → save as `data/mods_data.lua`
  3. `python scripts/parse_lua.py` → produces `weapons_raw.json` / `mods_raw.json`
  4. `python scripts/parse_wiki_data.py` → produces `weapons.json` / `mods.json`
  5. `git diff data/weapons.json` to review changes, then `pytest`
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
- **No inline `style=` attributes** on HTML elements — all styles go to CSS classes. SVG presentation attributes excepted.
- **No hardcoded `rgba()` for theme colors** — use CSS variables.
- **No scan-line or noise overlays** — both removed. Do not re-add.
- **No green or purple UI accents** — crimson theme only. Game-data colors (element types, mod rarities, riven olive) stay as-is.
- **Never use native `<select>` elements** — use `setupSelectDropdown()` in `utils.js` instead (iOS picker issue).
- **Fonts** — Orbitron for headings/values, Rajdhani for labels/buttons. No Share Tech Mono.
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
