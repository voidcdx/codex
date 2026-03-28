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
web/
  api.py            # FastAPI: GET /api/weapons|mods|enemies|version; POST /api/modded-weapon, /api/calculate, /api/scaled-enemy
                   #   GET /api/mods returns `effect` field (plain-text effect_raw) used by Alchemy Guide stat pills
  static/index.html # SPA HTML — stalker-dashboard layout: inner header + .content grid (1fr 480px) + right .sidebar
                   #   .content-main: Weapon+Enemy (.we-grid), Mods+Arcanes panel
                   #   .content-side: Results → Options (collapsible, merged Hit Options+Buffs) → Calculate → Build Compare (hidden) → Armor Strip → Mods panel
                   #   aside.sidebar (260px): brand text, nav-menu (.nav-item), sidebar-tools, sidebar-footer (copyright + data source)
                   #   .content-left (Builds panel): hidden via CSS, grid column removed from layout
                   #   Mobile: .burger-btn (fixed top-right) + .sidebar-overlay backdrop
  static/style.css  # Stalker/Shadow Acolyte theme: #050505 bg, crimson #8b0000/#dc143c, Orbitron/Rajdhani fonts
                   #   .panel: glass dark surface, sharp edges (radius:0), crimson top glow ::before
                   #   .sidebar: right-side nav 260px with .brand, .nav-menu, .nav-item (.active has right border)
                   #   .eff-badge/.eff-vuln/.eff-res for faction effectiveness badges in results table
                   #   .breakdown-table td/th have overflow-wrap:break-word so long CC/Debuff effect text wraps
  static/js/
    constants.js   # all global state + data constants (ELEM_COLORS, TOOLTIPS, etc.)
    utils.js       # esc(), fmtNum(), dmgIcon(), initTooltips(), getCurrentWeapon/Enemy(), setupSelectDropdown(), togglePanelHelp()
    combobox.js    # setupCombobox(), clearCombobox() — reusable widget
    weapons.js     # mod grid, picker, weapon stats, element badges, modded stats, special slots
    enemy.js       # enemy panel, level scaling, Steel Path, Eximus
    modals.js      # Alchemy Guide, Riven Builder, Guide, Buffs
    armorstrip.js  # updateArmorStripDisplay(), getArmorStripPayload(), initArmorStrip()
    calculate.js   # runCalculation(), showResults(), showError()
    app.js         # loadData() bootstrap, DOMContentLoaded, version fetch
run_web.py          # python run_web.py → dev server on port 8000
__main__.py         # python -m dc "Weapon" "Mod" vs "Enemy" [--crit avg|guaranteed|max] [--headshot] [--attack "Name"] [--list-attacks "Weapon"] [--version]
handoff.md          # session handoff notes for next Claude instance
```

## Tests
Run `pytest` before committing. All tests must pass.

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
- **User Guide:** When adding new features or panels to the Web UI, always update the Guide modal in `web/static/index.html` (`#guide-overlay`) to document the new functionality. The Guide is the user-facing reference for all calculator features.

## Web UI Notes

### Layout — Stalker-Dashboard Theme
The calculator page uses a mirrored stalker-dashboard layout:
- **`.main`** — left flex:1 column; contains `.header` (inner top bar) + `.content` grid
- **`.content`** — `grid-template-columns: 1fr 480px`; `.content-main` (inputs) + `.content-side` (results)
- **`aside.sidebar`** — right 260px; brand text ("VOID CODEX"), `.nav-menu` with `.nav-item` links, `.sidebar-tools`, `.sidebar-footer` (copyright + `Data: wiki.warframe.com`)
- **`.content-left`** — Builds panel, currently `display: none` (hidden). Grid column removed.
- **`.content-main` order** — Weapon+Enemy grid → Mods panel (moved here from content-side)
- **`.content-side` order** — Results → Options (collapsible, **collapsed by default**) → Calculate button → Build Compare → Armor Strip
- **`.app`** — `max-width: 1440px; margin: 0 auto` — full layout centered
- **Mobile ≤900px** — sidebar hidden, `.burger-btn` shows (fixed top-right), sidebar slides in from right with `.sidebar-overlay` backdrop
- `toggleDrawer()` in `app.js` toggles `#sidebar` + `#sidebar-overlay` CSS classes

### CSS Variables
Key theme vars in `:root`: `--bg: #050505`, `--surface: rgba(18,10,10,0.50)`, `--surface-solid: #201818`, `--surface2: rgba(12,6,6,0.55)`, `--border: rgba(139,0,0,0.4)`, `--panel-glow: rgba(139,0,0,0.13)`, `--crimson: #8b0000`, `--crimson-bright: #dc143c`, `--font-display: 'Orbitron'`, `--font-body: 'Rajdhani'`, `--radius: 0` (sharp edges everywhere).
**No green UI accents** — `--accent-green` maps to crimson. Only game-data colors (element types, mod rarities, riven olive `--riven: #5a8a3a`) stay green.
**No purple UI accents** — no `#c49aff`, no `rgba(155,109,208,...)`. Crimson theme only.

### CSS Design Rules (STRICT)
- **No inline `style=` attributes** on HTML elements — all styles go to CSS classes. SVG presentation attributes excepted.
- **No hardcoded `rgba()` for theme colors** — use CSS variables (see variable list above).
- **No rounded corners** — `--radius: 0`, `--radius-sm: 0` everywhere.
- **No scan-line or noise overlays** — both removed. Do not re-add.
- **Glassmorphism — local-glow pattern only.** `backdrop-filter` on `#050505` blurs nothing. Each `.panel` generates its own crimson atmosphere via `::after` (`inset: -24px; radial-gradient(...var(--panel-glow)...); z-index: -1`) so blur works without a page-wide background. Do NOT attempt page-level glassmorphism.
- **Font sizes** — use `rem` for text content. `px` only for structural/icon sizes. Body: `clamp(13px, 1.1vw, 16px)`. 7-step rem scale: `0.67rem` (8–9px) · `0.73rem` (10–11px) · `0.85rem` (12–13px) · `1rem` (14–15px) · `1.1rem` (18px) · `1.5rem` (24px). iOS anti-zoom overrides (`16px !important`) are intentional — do not convert.
- **Fonts** — Orbitron (`var(--font-display)`) for headings, names, and stat values. Rajdhani (`var(--font-body)`) for labels, descriptions, and button text. **No Share Tech Mono** — removed entirely.
- **`.sc-modded` arrows** — CSS `::before { content: '→ ' }` injects the arrow. Never prepend `'→ '` in JS `textContent` — it will double up.

### Key CSS Classes (panels.css)
| Class | Purpose |
|---|---|
| `.panel-sub-h` | Section heading divider within merged panels |
| `.btn-add` | `+ ADD` button (buffs row, arcane row) |
| `.btn-help` | `?` help toggle button — borderless, `var(--crimson)`, no border-radius |
| `.panel-help` / `.panel-help.hidden` | Inline help text block below a panel heading; hidden by default |
| `.panel-toggle-with-help` | Modifier on collapsible h2: transfers `margin-left: auto` from chevron to `.btn-help` |
| `.input-sm` | Compact 44px number input (stacks inputs) |
| `.input-sm-wide` | Compact 52px number input |
| `.input-level` | 72px enemy level input |
| `.bonus-element-label/row/unit` | Bonus element form row layout |
| `.enemy-level-col` | Column flex wrapper for level/SP/Eximus stack |
| `.panel-toggle` | Clickable `h2` header that collapses/expands panel |
| `.chevron` | Rotating arrow SVG inside `.panel-toggle` |
| `.collapsible-body` | Collapses with `.hidden` class |
| `.strip-row` / `.strip-label-row` | Armor strip panel row layout |
| `.strip-slider` | Range input — crimson thumb, no border-radius, `margin-bottom: 0` |
| `.strip-pct-badge` | Live % readout next to slider |
| `.strip-result-block` / `.strip-result-row` | Armor/DR summary section |
| `.strip-bar-wrap` / `.strip-bar-fill` | Strip progress bar (crimson fill, `transition: width 0.2s`) |

### Faction Effectiveness Badges
Results breakdown table shows `+50%` (green) or `−50%` (red) badges next to damage types based on the selected enemy's faction. Driven by `FACTION_EFFECTIVENESS` JS constant in `web/static/js/constants.js` (mirrors `src/calculator.py`). CSS: `.eff-badge`, `.eff-vuln`, `.eff-res` in `style.css`.

### Weapon Picker Filtering
Exalted weapons (`class === 'Exalted Weapon'`) and Garuda Talons are hidden from the weapon search combobox via `visibleWeapons` filter in `loadData()`. `allWeapons` retains full data.

### Combobox (Weapon + Enemy Search)
`setupCombobox()` in `combobox.js` — intentionally simple. Read the source for closure internals (`_confirmed`, z-index lift, touch/mouse event handling).

### Select Dropdowns (Hit Type, Body Part, Bonus Element)
**Never use native `<select>` elements** — they render as iOS pickers on mobile and can't be CSS-styled cross-platform. Use `setupSelectDropdown(selectId, onChange)` in `utils.js` instead. This hides the native select, builds a `.sel-btn` trigger + `.combobox-dropdown` div using `.combobox-item` rows — identical look to the search comboboxes. Call `refreshSelectDropdown(selectId)` after programmatically updating options.

### Mod Slot Compatibility
`onWeaponChange()` clears any mod slots whose `mod.type` is not in `getCompatibleModTypes()` for the new weapon. Mod picker always enforces type compatibility — no fallback to showing all mods.

### Combo Counter
Melee-only mechanic. `onWeaponChange()` hides `#combo-div` and resets to tier 1 for non-melee weapons (uses existing `isMeleeWeapon()`). Range: 1–12 for all weapons, 1–13 for Venka Prime. `oninput` clamp enforces the cap against manual keyboard entry.

### Input / Focus Styling
- Focus glow is white/subtle — **not** crimson (`var(--accent)`). Riven inputs keep purple focus intentionally.
- Do NOT add crimson glow to combobox dropdowns or modal borders. Crimson border stays on `.panel:hover` and `.nav-item.active` only.

### Galvanized Stacks
`#galv-stacks` input (range 0–5, default 0). Shown in the mod panel whenever any equipped mod has `galv_kill_stat` set. Sent as `galvanized_stacks: int` in POST bodies to `/api/calculate` and `/api/modded-weapon`. The server caps effective stacks per-mod via `galv_max_stacks`.

## Riven Mod Builder (Web UI)
Purple card in mod grid → two-column modal with up to 4 stat rows. `rivenDraft[]` state in `modals.js`. `buildRivenFromDraft()` converts to Mod-compatible object. Mobile: centered modal with scroll containment.

## Alchemy Mixer (Web UI)
Gold seal button in mod panel header → modal for exploring elemental combinations. Pick two primary elements → animated merge → filtered mod suggestions with +/− equip buttons.
- **Key state:** `alchSelected[]` (0–2), `_alchMergeTimer`. `clearAlchMods()` removes only elemental mods from slots.
- **Naming:** Uses `ALCH_PRIMARY` (array) — do not confuse with `PRIMARY_ELEMENTS` (Set, used by combiner).
- **Mobile:** Stays centered (overrides bottom-sheet pattern). Scroll containment on `.alchemy-suggestions`.

## Multi-Attack System
Weapons can have multiple attack modes (e.g. Acceltra Prime: Rocket Impact + Rocket Explosion; Torid: Grenade Impact + Poison Cloud + Incarnon Form). Each attack has its own damage, crit, status, fire rate, and shot type.

**Data schema:** `weapons.json` stores `attacks[]` per weapon. Each attack has `name`, `base_damage`, `innate_elements`, `crit_chance`, `crit_multiplier`, `status_chance`, `fire_rate`, `shot_type`.

**Selection:** `load_weapon(name, attack_name=None)` — defaults to first attack. The selected attack's stats populate `Weapon.base_damage`, `innate_elements`, `crit_chance`, `crit_multiplier`, `status_chance`. All attacks are also available via `Weapon.attacks` for enumeration.

**CLI:** `--attack "Rocket Explosion"` flag (must come before or after all positional args due to argparse).

**API:** POST endpoints (`/api/calculate`, `/api/modded-weapon`) accept optional `"attack"` field. `GET /api/weapons` returns per-weapon `attacks[]` with per-attack stats.

## Galvanized Mods

Three extra fields on the `Mod` dataclass (default to empty/0 for non-galvanized mods):

| Field | Type | Values |
|---|---|---|
| `galv_kill_stat` | `str` | `"multishot_bonus"` \| `"cc_bonus"` \| `"cd_bonus"` \| `"sc_bonus"` \| `"aptitude_damage_bonus"` \| `""` |
| `galv_kill_pct` | `float` | Per-stack bonus (e.g. `0.20` = +20% per stack) |
| `galv_max_stacks` | `int` | Mod-specific cap (typically 4 or 5) |

**Stack injection:** `calculate()` and `calculate_procs()` accept `galvanized_stacks: int = 0`. For each equipped galvanized mod, effective stacks = `min(galvanized_stacks, mod.galv_max_stacks)`.

**Aptitude-style** (`galv_kill_stat == "aptitude_damage_bonus"`): bonus = `galv_kill_pct × stacks × unique_statuses`, added to `damage_bonus` in Step 1.

**CC/CD/multishot/SC styles**: bonuses are pre-computed in `api.py` before calling `calculate()` — they augment the relevant `Weapon` fields directly.

## Confirmed Order of Operations (from wiki research)
Per [Mad5cout's community research](https://wiki.warframe.com/w/User_blog:Mad5cout/Warframe_Damage_Calculation_Research):

```
1. Base Damage × (1 + ΣDamageMods)           → Modded Base Damage  [round DOWN]
2. Modded Base Damage × Body Part Multiplier  → Part Damage         [round to nearest]
3. Part Damage × DamageType Multiplier        → Typed Damage        [round DOWN]
4. Typed Damage × Armor Mitigation            → Mitigated Damage    [round DOWN]
5. Mitigated Damage × (1 + FactionMod)        → Final Damage        [round DOWN]
6. Final Damage × Viral stack multiplier      → Viral Damage        [round DOWN]
```

**Viral stack multipliers** (0 stacks = ×1.0, max 10 stacks = ×4.25):
`{1:1.75, 2:2.0, 3:2.25, 4:2.5, 5:2.75, 6:3.0, 7:3.25, 8:3.5, 9:3.75, 10:4.25}`

**Armor Mitigation** = `300 / (300 + min(armor, 2700))` — flat DR, no per-type modifiers (Update 36+).
**Faction mods apply LAST** — multiplicative `(1 + bonus)` after armor mitigation.
**Faction/Damage mods** do NOT affect quantization scale — they are simple multipliers on already-quantized values.

## Critical Hit Rules
- **Tier Scaling:** `M_crit = 1 + T × (CD − 1)` where T = `floor(total_crit_chance)`
- **Average Multiplier:** Use `1 + CC × (CD − 1)` for DPS calculations (exact for all tiers).
- **Headshot:** Normal headshot = ×2 body part multiplier (Step 2).
- **Crit on Headshot:** If the hit is also a critical, the crit multiplier is **doubled**: `M_crit_headshot = 1 + T × (CD − 1) × 2`. Apply after Step 2, before Step 3.

## Faction Mod Rules
- **Placement:** Faction mods (Bane of X) apply **at the very end** — Step 5, after armor mitigation.
- **Formula:** `Final Damage × (1 + faction_bonus)`
- **Double-Dipping (Status Procs):** For damage-over-time procs triggered by the hit (Slash bleed, Gas cloud, Heat burn), the faction bonus applies **twice**: `proc_damage × (1 + faction_bonus)²`. This is because the proc inherits the faction bonus from the hit that triggered it, then applies it again when the proc ticks.

## Quantization Rules (Damage 3.0)
Scale = `base_damage / 32`

For each damage type:
```python
from decimal import Decimal, ROUND_HALF_UP

def warframe_round(x: Decimal) -> Decimal:
    """NEVER use Python's built-in round() — it uses Banker's Rounding (round-half-to-even),
    which produces wrong results on exact .5 boundaries. Always use this instead."""
    return x.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

quantized = warframe_round(Decimal(str(raw_amount)) / Decimal(str(scale))) * Decimal(str(scale))
```
- **NEVER use Python's `round()` built-in** — use `warframe_round` (Decimal + ROUND_HALF_UP) everywhere
- **Use `Decimal` for all intermediate steps** to prevent floating-point drift
- Applied **independently per damage type** (Impact, Puncture, Slash, each elemental)
- Applied **before** faction/damage multipliers
- Combined elements (e.g. Viral from Cold+Toxin) quantize their **combined total** at 1/32 of base

### CDM Quantization
Critical damage multiplier is quantized to the game's internal precision grid:
```python
quantized_cdm = Round(CDM × 4095/32) × 32/4095
```
- Grid step ≈ 0.00781 (32/4095)
- Applied **after** all CD bonuses (mods, arcanes, cold stacks) are summed
- Applied **before** `calculate_crit_multiplier()` uses the value
- `quantize_cdm()` in `src/quantizer.py` — Decimal precision, ROUND_HALF_UP
- Both `/api/modded-weapon` and `/api/calculate` call `quantize_cdm()` on the final modded CDM

## Elemental Combination
**Primary elements:** Heat, Cold, Electricity, Toxin
**Combination priority:** mod placement order, top-left first. Innate weapon elements come last.
Exception: Kuva/Tenet innate elements follow HCET priority (Heat > Cold > Electricity > Toxin).

| Combined Element | Recipe              |
|-----------------|---------------------|
| Blast           | Heat + Cold         |
| Corrosive       | Electricity + Toxin |
| Gas             | Heat + Toxin        |
| Magnetic        | Cold + Electricity  |
| Radiation       | Heat + Electricity  |
| Viral           | Cold + Toxin        |

### Innate Element Placement Rules
- **Primary innate elements** (e.g. Heat on Ignis) occupy **"Slot 9"** — after all mod slots — unless a mod of the same element is equipped. If a mod of the same element is present, the innate amount merges into that mod's slot position (first occurrence wins queue order).
- **Secondary (combined) innate elements** (e.g. Magnetic on Kuva Nukor) are a fixed bucket — they cannot be uncombined or combined further with anything else. They are passed through directly to the damage output.
- **Quantization order:** Combine raw bonus percentages first → calculate raw damage → then apply `quantize_damage()` to the final combined total. Never quantize individual primaries before combining.

## Enemy Armor (Post-Update 36: Jade Shadows, June 18 2024)
- **Hard Cap:** Enemy armor is hard-capped at 2,700 (90% DR).
- **Armor Scaling:** `DR = Armor / (Armor + 300)` — flat, no per-type modifiers.
- **No armor-type modifiers:** Update 36 removed Ferrite/Alloy armor types. Armor provides flat DR only. All damage type bonuses/penalties are faction-based (see Faction Effectiveness table).
- `armor_type` field in `enemies.json` and `ArmorType` enum are retained as inert metadata.

## Enemy Level Scaling

Formula source: [wiki.warframe.com/w/Enemy_Level_Scaling](https://wiki.warframe.com/w/Enemy_Level_Scaling) (community-derived).

**ΔLevel** = `max(0, level - base_level)`. Steel Path applies a ×2.5 multiplier to health and shields only — it does **not** add +100 to the level used in the formula.

### Health Multiplier (per-faction)
Smoothstep blend 70–80. `f1(δ) = 1 + A1×δ^e1`, `f2(δ) = 1 + A2×δ^e2`.

| Faction | A1 | e1 | A2 | e2 |
|---|---|---|---|---|
| Grineer / Scaldra | 0.015 | 2.12 | 10.7332 | 0.72   |
| Corpus | 0.015 | 2.12 | 13.4165 | 0.55 |
| Infested | 0.0225 | 2.12 | 16.1 | 0.72 |
| Corrupted | 0.015 | 2.10 | 10.7332 | 0.685 |
| Murmur / Sentient / Unaffiliated | 0.015 | 2.0 | 10.7332 | 0.5 |
| Techrot | 0.02 | 2.12 | 15.1 | 0.7 |

### Shield Multiplier (per-faction)
Same smoothstep structure. Factions not listed use Grineer coefficients.

| Faction | A1 | e1 | A2 | e2 |
|---|---|---|---|---|
| Corpus | 0.02 | 1.76 | 2.0 | 0.76 |
| Corrupted | 0.02 | 1.75 | 2.0 | 0.75 |
| Grineer / Sentient | 0.02 | 1.75 | 1.6 | 0.75 |
| Techrot | 0.02 | 1.76 | 3.5 | 0.76 |

- **Steel Path:** ×2.5 multiplier applied to health and shields

### Overguard (Eximus Only)
Two-regime smoothstep formula (source: wiki.warframe.com/w/Enemy_Level_Scaling):
```
δ_OG  = target_level − enemy_base_level  (same delta as health; SP +100 NOT added for OG)
f1(δ) = 1 + 0.0015 × δ^4            (δ < 45)
f2(δ) = 1 + 260 × δ^0.9             (δ > 50)
T     = (δ - 45) / 5
S2    = 3T² − 2T³                   (45 ≤ δ ≤ 50), else 0 or 1
Overguard = 12 × [f1(δ)·(1 − S2) + f2(δ)·S2]
```
Reference values: δ=0 → 12.0 | δ=10 → 192.0 | δ=45 → 73,823.25 | δ=50 → ~105,592.8 | δ=199 → ~365,676 | δ=599 → ~985,000

### Armor Scaling
Two-regime smoothstep (70–80 transition), hard-capped at 2700 (90% DR):
```
f1(δ) = 1 + 0.005 × δ^1.75
f2(δ) = 1 + 0.4   × δ^0.75
```

### Implementation
- `src/scaling.py` — all formulas; `scale_enemy_stats()` is the main entry point
- `web/api.py` — `POST /api/scaled-enemy` → `{level, health, shield, armor, overguard}`
- UI: enemy panel shows faction, health type (armor type hidden — inert post-Update 36), Level input (1–9999), Steel Path toggle, Eximus toggle
- Display uses `toFixed(2)` → `toLocaleString` to show decimals (e.g. `4,502,520.4`)
- **Do not truncate coefficients** — 6-decimal rounding causes ~9 HP / ~2 OG drift vs wiki

## Status Procs (`calculate_procs()`)

Two proc categories, both returned in `procs` dict from `/api/calculate`:

### DoT Procs (damage_per_tick > 0, ticks = 6)
| Key | Damage | Notes |
|---|---|---|
| `slash` | 35% of step-2 total | Faction double-dips |
| `heat` | 50% of step-2 total | Faction double-dips; type eff. applied |
| `gas` | 50% of base × damage bonus × gas mod bonus | Faction double-dips; crit + body part applied |
| `toxin` | 50% of step-2 total | Faction double-dips; type eff. applied |
| `electricity` | 50% of step-2 total | Faction double-dips; type eff. applied |

### CC / Debuff Procs (damage_per_tick = 0, ticks = 0)
These are crowd-control or debuff effects — no tick damage. Return `{active, effect, damage_per_tick:0, ticks:0, total_damage:0}`.

| Key | Effect |
|---|---|
| `viral` | Health Vulnr. ×1.75–×4.25 |
| `magnetic` | +100% shield/OG dmg; forced Elec proc on shield break |
| `radiation` | Confuses enemy to attack allies for 12s |
| `blast` | −30% accuracy (up to −75%); detonates at 10 stacks |
| `cold` | −50% speed (up to −90%); +0.1 flat crit damage |

DoT procs show per-tick / total columns. CC procs show effect text only (no damage contribution).

## Damage Type Effectiveness (Update 36.0+)
- **Vulnerable (+):** ×1.5
- **Resistant (−):** ×0.5

## Data Quality Notes

### mods.json — secondary stat fields
Many mods have a primary stat (e.g. an elemental%) and secondary weapon stats (e.g. reload speed, magazine, status chance) that are **only** in `effect_raw` unless explicitly parsed. `scripts/fix_secondary_stats.py` was used to backfill 109 such fields across 9 stat types. After regenerating `mods.json`, run both patch scripts in order:
```bash
python scripts/fix_secondary_stats.py
python scripts/fix_galv_stats.py
```

Fields read by `loader.py` from each mod entry:
`damage_bonus_pct`, `impact_pct`, `puncture_pct`, `slash_pct`, `crit_chance_pct`, `crit_damage_pct`, `status_chance_pct`, `multishot_pct`, `status_damage_pct`, `fire_rate_pct`, `magazine_pct`, `ammo_max_pct`, `reload_speed_pct`, `condition_overload_pct`

### mods.json — Conclave (PVP) mods
Conclave-exclusive mods (wings icon) are filtered automatically during `parse_mods()` via the `/PvPMods/` substring in `InternalName`. This removes ~129 mods. Dual-use mods (diamond icon, `Conclave=True` but no `/PvPMods/`) such as Eagle Eye are retained.

## Weapon Arcanes

`src/arcanes.py` — preset factory functions. `src/models.py` — `WeaponArcane` dataclass.

### Pipeline Placement
- **damage_bonus** → additive with Serration in Step 1 (`total_damage_bonus`)
- **headshot_bonus** (Deadhead) → additive to `body_part_multiplier` in Step 2, headshot only
- **cc_bonus / cd_bonus** (Cascadia Flare/Empowered) → pre-computed in `api.py`, added to weapon stats
- **reload_bonus** (Merciless) → applied to modded reload time for sustained DPS
- **flat_damage** (Cascadia Overcharge) → distributed proportionally among IPS types before Step 1

### Presets
11 presets in `src/arcanes.py` — Merciless (×3 slots), Deadhead (×3), Dexterity (×2), Cascadia Flare/Empowered/Overcharge. See source or User Guide for full table.

### Usage
- **CLI:** `--arcane primary_merciless:12` (name:stacks, max 2).
- **API:** `arcanes: [{name, stacks}]` on `/api/calculate` and `/api/modded-weapon`. `GET /api/arcanes` returns preset list.
- **Web UI:** Arcane panel with dropdown filtered by weapon slot, stacks input, max 2 rows.

## Warframe Ability Buffs

`src/buffs.py` — preset factory functions for ability buffs. `src/models.py` — `Buff` dataclass.

### Pipeline Placement
- **Roar** → Step 5, additive with Bane mods. Double-dips on DoT procs.
- **Eclipse** → Step 5.5, separate multiplicative after faction. No double-dip.
- **Xata's Whisper** → Independent Void hit, double-dips faction + headshot.
- **Nourish** → Step 1, adds Viral elemental damage.

### Usage
- **CLI:** `--buff roar:1.5` (name:strength). **API:** `buffs: [{name, strength}]`. **Web UI:** Buffs panel with dropdown + strength input.
- Presets: `roar`, `eclipse`, `xatas_whisper`, `nourish` in `src/buffs.py`.

## Damage Falloff

Distance-based damage reduction for hitscan/projectile weapons. ~410/590 weapons have falloff data.

### Data Schema
Per-attack fields in `weapons.json`: `falloff_start` (full damage up to this range in meters), `falloff_end` (minimum damage beyond this range), `falloff_reduction` (max reduction fraction, e.g. 0.8 = 80% reduction at end range).

### Formula
```
multiplier = 1 - reduction × clamp((distance - start) / (end - start), 0, 1)
```
- `distance ≤ start` → ×1.0 (full damage)
- `start < distance < end` → linear ramp down
- `distance ≥ end` → ×(1 − reduction) (floor)

### Pipeline Placement
- Applied **after** all 6 quantized pipeline steps + multishot, as `math.floor(v * multiplier)`
- **DoT procs are NOT affected** by falloff — they tick at full damage regardless of distance
- `calculate_falloff_multiplier()` helper in `src/calculator.py`
- `distance: float = 0.0` param on `calculate()` — default 0 = point blank = no reduction

### Usage
- **API:** `distance` field on POST `/api/calculate`. Response includes `falloff_multiplier`.
- **Web UI:** Distance input in Options panel, hidden for weapons without falloff. Weapon card shows `Falloff: 10–20m (20% min)`.
- **CLI:** Not yet exposed as a flag.

## Live Data / Worldstate (`/live`)

`GET /live` serves `web/static/live.html` — a separate SPA from the main calculator.

### Data source
DE's official endpoint: `https://api.warframe.com/cdn/worldState.php` (and platform variants for ps4/xb1/swi). No third-party API. **Do not use `content.warframe.com`** — it returns `403 host_not_allowed` for non-game-client requests.

### Server-side (`web/api.py`)
- `GET /api/worldstate?platform=pc` — only endpoint the client calls; returns cached parsed JSON.
- **Cache:** In-memory `_ws_cache` dict, TTL = 60 seconds (`_WS_TTL = 60`).
- **Retry:** `_fetch_worldstate()` retries 3× with 2-second backoff before raising.
- **Stale fallback:** On fetch failure the background loop leaves `_ws_cache` intact. The endpoint raises 503 only on a cold cache (first fetch not yet complete). Once warm, always returns last good data.
- **HTTP timeout:** 15 seconds per attempt.
- **Parsing:** `scripts/parse_worldstate.py` — imported dynamically by `_fetch_worldstate()` via `_load_parse_worldstate_mod()`. `parse(raw)` is the entry point.
- **No client-side fetch:** `live.html` never contacts DE directly — all data flows through `/api/worldstate`.

### Parsed sections
| Key | Source function | Rendered in live.html |
|---|---|---|
| `fissures` | `_parse_fissures()` | Yes |
| `sortie` | `_parse_sortie()` | Yes |
| `archon_hunt` | `_parse_archon_hunt()` | Yes |
| `void_trader` | `_parse_void_trader()` | Yes |
| `nightwave` | `_parse_nightwave()` | Yes |
| `alerts` | `_parse_alerts()` | Yes |
| `invasions` | `_parse_invasions()` | Yes |
| `cycles` | `_parse_cycles()` | Yes |
| `events` | `_parse_events()` | Yes |

### UI auto-refresh
- Countdown timer in `live.html`: refreshes every **180 seconds**.
- Actual upstream fetches happen at most every 60 seconds (TTL).
- Manual refresh button always triggers a fresh `/api/worldstate` call.

### Node Name Lookup (`ALL_NODES` / `NODE_FACTION` in `parse_worldstate.py`)
`ALL_NODES` maps SolNode/SettlementNode/ClanNode/CrewBattleNode keys → `"Name (Planet)"`. `NODE_FACTION` maps same keys → faction string (used as fallback when the worldstate `Faction` field is absent).

**When fissures show raw node IDs (e.g. `SolNode10` instead of a name):**
1. Open `https://api.warframe.com/cdn/worldState.php` in the browser
2. Run JS: `JSON.parse(document.body.innerText).ActiveMissions.map(f => f.Node)` to get active node keys
3. Cross-reference against `ALL_NODES` keys to find what's missing
4. Look up the node name on the relevant planet wiki page at `wiki.warframe.com/w/PlanetName`
5. Add to both `ALL_NODES` (display name) and `NODE_FACTION` (faction) in the correct section

**Known data quality issue:** Jupiter and Eris node IDs in `ALL_NODES` are partially stale. The wiki now lists different SolNode IDs for several nodes on those planets (e.g. wiki shows `SolNode164`=Kala-azar/Eris but our code has `SolNode164`=Elara/Jupiter). Both old and new IDs appear active in the worldstate. A full Jupiter + Eris audit is pending.

`solnode_map.json` (secondary fallback) does not exist — do not rely on it.

### Live page typography scale (do not regress)
| Tier | Size | Examples |
|---|---|---|
| Panel headings | `1rem` Orbitron | `.panel h2` (global via `panels.css`) |
| Primary row data | `1rem` | `.fissure-node`, `.mission-node`, `.trader-location`, `.nw-title`, `.alert-reward`, `.invasion-node`, `.event-title`, `.cycle-state`, `.sortie-boss` |
| Secondary text / ETAs | `0.85rem` | `.fissure-sub`, `.mission-sub`, `.trader-eta`, `.nw-eta`, `.alert-sub`, `.invasion-factions`, `.cycle-eta`, `.event-desc`, `.live-eta`, `.eta-chip` |
| Tags / badges / buttons | `0.73rem` | `.fissure-tier`, `.fissure-tag`, `.nw-tag`, `.modifier-badge`, `.reward-chip`, `.invasion-vs`, `.live-count`, `.refresh-btn` |

When adding new live page sections, follow this tier assignment. Do not drop primary row data below `1rem` or secondary text below `0.85rem`.

## Coding Standards
- **Accuracy first:** Mathematical correctness over speed or brevity.
- **Test before implement:** Write the `pytest` case from a wiki example, then write logic until it passes.
- **Pure functions:** `quantize()`, `combine()` must have no side effects.
- **Type hints** on all function signatures.

## Private Notes
`accuracy-notes.md` — accuracy self-assessment covering what the calculator gets right, known gaps, and where confidence is lowest. Read on user request.

## Rules
- Short answers only. Don't rewrite entire files — only the parts that need changing. Ask questions when uncertain.

## Critical Implementation Rules
- **Rounding:** NEVER use the built-in `round()` function. All rounding must use the `warframe_round` utility (Decimal + ROUND_HALF_UP) to prevent Banker's Rounding errors.
- **Quantization:** Apply quantization (scale of 1/32) to each damage type (Impact, Puncture, Slash, Elementals) individually before summing.
- **Precision:** Use `Decimal` or high-precision floats for intermediate steps to avoid floating-point drift.
