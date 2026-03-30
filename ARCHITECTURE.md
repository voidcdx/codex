# ARCHITECTURE.md
Detailed implementation notes for the Warframe Damage Calculator.
Read this when working on damage math, CSS/layout, live page, or data pipeline.

---

## Web UI — Layout & Theme

### Stalker-Dashboard Layout (calculator page)
- **`.main`** — left flex:1 column; contains `.header` (inner top bar) + `.content` grid
- **`.content`** — `grid-template-columns: 1fr 480px`; `.content-main` (inputs) + `.content-side` (results)
- **`aside.sidebar`** — right 260px; brand text ("VOID CODEX"), `.nav-menu` with `.nav-item` links, `.sidebar-tools`, `.sidebar-footer` (copyright + `Data: wiki.warframe.com`)
- **`.content-left`** — Builds panel, currently `display: none` (hidden). Grid column removed.
- **`.content-main` order** — Weapon+Enemy grid → Mods panel
- **`.content-side` order** — Results → Options (collapsible, **collapsed by default**, contains Warframe Buffs + Armor Strip) → Calculate button → Build Compare
- **`.app`** — `max-width: 1440px; margin: 0 auto`
- **Mobile ≤900px** — sidebar hidden, `.burger-btn` shows (fixed top-right), sidebar slides in from right with `.sidebar-overlay` backdrop
- `toggleDrawer()` in `app.js` toggles `#sidebar` + `#sidebar-overlay` CSS classes

### CSS Variables
Key theme vars in `:root`: `--bg: #050505`, `--surface: rgba(18,10,10,0.50)`, `--surface-solid: #201818`, `--surface2: rgba(12,6,6,0.55)`, `--border: rgba(139,0,0,0.4)`, `--panel-glow: rgba(139,0,0,0.13)`, `--crimson: #8b0000`, `--crimson-bright: #dc143c`, `--font-display: 'Orbitron'`, `--font-body: 'Rajdhani'`, `--radius: 0` (sharp edges everywhere).

### Font Size Scale
`0.67rem` (8–9px) · `0.73rem` (10–11px) · `0.85rem` (12–13px) · `1rem` (14–15px) · `1.1rem` (18px) · `1.5rem` (24px). iOS anti-zoom overrides (`16px !important`) are intentional — do not convert.

### Glassmorphism — local-glow pattern only
`backdrop-filter` on `#050505` blurs nothing. Each `.panel` generates its own crimson atmosphere via `::after` (`inset: -24px; radial-gradient(...var(--panel-glow)...); z-index: -1`). Do NOT attempt page-level glassmorphism.

### `.sc-modded` arrows
CSS `::before { content: '→ ' }` injects the arrow. Never prepend `'→ '` in JS `textContent` — it will double up.

### Key CSS Classes (panels.css)
| Class | Purpose |
|---|---|
| `.panel-sub-h` | Section heading divider within merged panels |
| `.btn-add` | `+ ADD` button (buffs row, arcane row) |
| `.btn-help` | `?` help toggle button — borderless, `var(--crimson)`, no border-radius |
| `.panel-help` / `.panel-help.hidden` | Inline help text block below a panel heading; hidden by default |
| `.panel-toggle-with-help` | Modifier on collapsible h2: transfers `margin-left: auto` from chevron to `.btn-help` |
| `.input-sm` | Compact 44px number input |
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
| `.strip-bar-label-left` / `.strip-bar-label-right` | "Original" / "X% stripped" labels under strip bar — `0.85rem` |
| `.buff-helminth-label` | Helminth checkbox label — crimson, `0.73rem`, flex row |
| `.buff-subsumed` | Helminth checkbox — fully custom styled (`appearance:none`), crimson border + fill, white checkmark |

### Enemy Picker Card Structure
Enemy name and subtitle (faction · health type) sit **outside** `.threat-card`, directly in `#enemy-stats-content`.
```html
#enemy-stats-content
  <div class="weapon-stats-name">Name</div>
  <div class="weapon-stats-sub">Faction · Health Type</div>
  <div class="threat-card">
    <div class="threat-stats-row">…</div>
    <div class="threat-bars">…</div>
  </div>
```

### Faction Effectiveness Badges
Results breakdown table shows `+50%` / `−50%` badges driven by `FACTION_EFFECTIVENESS` JS constant in `constants.js` (mirrors `src/calculator.py`). CSS: `.eff-badge`, `.eff-vuln`, `.eff-res`.

### Weapon Picker Filtering
Exalted weapons (`class === 'Exalted Weapon'`) and Garuda Talons are hidden via `visibleWeapons` filter in `loadData()`. `allWeapons` retains full data.

### Combobox / Select Dropdowns
- `setupCombobox()` in `combobox.js` — weapon + enemy search.
- `setupSelectDropdown(selectId, onChange)` in `utils.js` — hit type, body part, bonus element. Never use native `<select>`.
- Call `refreshSelectDropdown(selectId)` after programmatically updating options.

### Mod Slot Compatibility
`onWeaponChange()` clears any mod slots whose `mod.type` is not in `getCompatibleModTypes()` for the new weapon.

### Combo Counter
Melee-only. Range: 1–12 for all weapons, 1–13 for Venka Prime. `oninput` clamp enforces the cap.

### Input / Focus Styling
Focus glow is white/subtle — **not** crimson. Riven inputs keep purple focus intentionally. Do NOT add crimson glow to combobox dropdowns or modal borders.

### Galvanized Stacks
`#galv-stacks` input (range 0–5, default 0). Shown when any equipped mod has `galv_kill_stat` set. Sent as `galvanized_stacks: int` in POST bodies.

### Warframe Buffs — Strength Input
Strength input sends `parseFloat(val) / 100` to the API. Label says **percentage** (e.g. enter `150` for 150%). Do not change — the `/100` division is in JS, not the API.

### Helminth Checkbox
`.buff-subsumed` — fully custom-styled (`appearance: none`), crimson border + fill + white checkmark on `:checked`. Defined in `panels.css`. `.buff-helminth-label` is the label. **No inline `style=`**.

---

## Riven Mod Builder
Purple card in mod grid → two-column modal with up to 4 stat rows. `rivenDraft[]` state in `modals.js`. `buildRivenFromDraft()` converts to Mod-compatible object. Mobile: centered modal with scroll containment.

## Alchemy Mixer
Gold seal button in mod panel header → modal for exploring elemental combinations.
- **Key state:** `alchSelected[]` (0–2), `_alchMergeTimer`. `clearAlchMods()` removes only elemental mods from slots.
- **Naming:** Uses `ALCH_PRIMARY` (array) — do not confuse with `PRIMARY_ELEMENTS` (Set, used by combiner).
- **Mobile:** Stays centered. Scroll containment on `.alchemy-suggestions`.

---

## Multi-Attack System
Weapons can have multiple attack modes. Each attack has `name`, `base_damage`, `innate_elements`, `crit_chance`, `crit_multiplier`, `status_chance`, `fire_rate`, `shot_type` in `weapons.json` under `attacks[]`.

- **Selection:** `load_weapon(name, attack_name=None)` — defaults to first attack.
- **CLI:** `--attack "Rocket Explosion"`
- **API:** POST endpoints accept optional `"attack"` field. `GET /api/weapons` returns per-weapon `attacks[]`.

---

## Galvanized Mods

| Field | Type | Values |
|---|---|---|
| `galv_kill_stat` | `str` | `"multishot_bonus"` \| `"cc_bonus"` \| `"cd_bonus"` \| `"sc_bonus"` \| `"aptitude_damage_bonus"` \| `""` |
| `galv_kill_pct` | `float` | Per-stack bonus (e.g. `0.20` = +20% per stack) |
| `galv_max_stacks` | `int` | Mod-specific cap (typically 4 or 5) |

**Aptitude-style:** bonus = `galv_kill_pct × stacks × unique_statuses`, added to `damage_bonus` in Step 1.
**CC/CD/multishot/SC styles:** bonuses pre-computed in `api.py`, augment `Weapon` fields directly.

---

## Confirmed Order of Operations
```
1. Base Damage × (1 + ΣDamageMods)           → Modded Base Damage  [round DOWN]
2. Modded Base Damage × Body Part Multiplier  → Part Damage         [round to nearest]
3. Part Damage × DamageType Multiplier        → Typed Damage        [round DOWN]
4. Typed Damage × Armor Mitigation            → Mitigated Damage    [round DOWN]
5. Mitigated Damage × (1 + FactionMod)        → Final Damage        [round DOWN]
6. Final Damage × Viral stack multiplier      → Viral Damage        [round DOWN]
```

**Viral stack multipliers** (0=×1.0, max 10=×4.25):
`{1:1.75, 2:2.0, 3:2.25, 4:2.5, 5:2.75, 6:3.0, 7:3.25, 8:3.5, 9:3.75, 10:4.25}`

**Armor Mitigation** = `300 / (300 + min(armor, 2700))` — flat DR, no per-type modifiers (Update 36+).
**Faction mods apply LAST** — multiplicative `(1 + bonus)` after armor mitigation.

---

## Critical Hit Rules
- **Tier Scaling:** `M_crit = 1 + T × (CD − 1)` where T = `floor(total_crit_chance)`
- **Average Multiplier:** `1 + CC × (CD − 1)` for DPS calculations.
- **Crit on Headshot:** `M_crit_headshot = 1 + T × (CD − 1) × 2`. Apply after Step 2, before Step 3.

---

## Faction Mod Rules
- Faction mods (Bane of X) apply at Step 5, after armor mitigation: `Final Damage × (1 + faction_bonus)`
- **Double-Dipping (Status Procs):** Slash bleed, Gas cloud, Heat burn apply faction bonus twice: `proc_damage × (1 + faction_bonus)²`

---

## Quantization Rules (Damage 3.0)
Scale = `base_damage / 32`

```python
from decimal import Decimal, ROUND_HALF_UP

def warframe_round(x: Decimal) -> Decimal:
    return x.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

quantized = warframe_round(Decimal(str(raw_amount)) / Decimal(str(scale))) * Decimal(str(scale))
```
- Applied **independently per damage type** before faction/damage multipliers.
- Combined elements quantize their **combined total** at 1/32 of base.

### CDM Quantization
```python
quantized_cdm = Round(CDM × 4095/32) × 32/4095
```
Grid step ≈ 0.00781. Applied after all CD bonuses summed, before `calculate_crit_multiplier()`. `quantize_cdm()` in `src/quantizer.py`.

---

## Elemental Combination
**Primary elements:** Heat, Cold, Electricity, Toxin
**Combination priority:** mod placement order, top-left first. Innate weapon elements come last.
Exception: Kuva/Tenet innate elements follow HCET priority.

| Combined Element | Recipe |
|---|---|
| Blast | Heat + Cold |
| Corrosive | Electricity + Toxin |
| Gas | Heat + Toxin |
| Magnetic | Cold + Electricity |
| Radiation | Heat + Electricity |
| Viral | Cold + Toxin |

### Innate Element Placement Rules
- **Primary innate** (e.g. Heat on Ignis) occupy "Slot 9" — after all mod slots — unless a mod of the same element is equipped.
- **Secondary (combined) innate** (e.g. Magnetic on Kuva Nukor) are fixed — cannot be uncombined or combined further.
- **Quantization order:** Combine raw bonus percentages first → calculate raw damage → then quantize. Never quantize individual primaries before combining.

---

## Enemy Armor (Post-Update 36: Jade Shadows, June 18 2024)
- **Hard Cap:** 2,700 (90% DR).
- **Formula:** `DR = Armor / (Armor + 300)` — flat, no per-type modifiers.
- `armor_type` field in `enemies.json` and `ArmorType` enum are retained as inert metadata.

---

## Enemy Level Scaling

**ΔLevel** = `max(0, level - base_level)`. Steel Path: ×2.5 on health and shields only (does NOT add +100 to level).

### Health Multiplier (per-faction)
Smoothstep blend 70–80. `f1(δ) = 1 + A1×δ^e1`, `f2(δ) = 1 + A2×δ^e2`.

| Faction | A1 | e1 | A2 | e2 |
|---|---|---|---|---|
| Grineer / Scaldra | 0.015 | 2.12 | 10.7332 | 0.72 |
| Corpus | 0.015 | 2.12 | 13.4165 | 0.55 |
| Infested | 0.0225 | 2.12 | 16.1 | 0.72 |
| Corrupted | 0.015 | 2.10 | 10.7332 | 0.685 |
| Murmur / Sentient / Unaffiliated | 0.015 | 2.0 | 10.7332 | 0.5 |
| Techrot | 0.02 | 2.12 | 15.1 | 0.7 |

### Shield Multiplier (per-faction)
| Faction | A1 | e1 | A2 | e2 |
|---|---|---|---|---|
| Corpus | 0.02 | 1.76 | 2.0 | 0.76 |
| Corrupted | 0.02 | 1.75 | 2.0 | 0.75 |
| Grineer / Sentient | 0.02 | 1.75 | 1.6 | 0.75 |
| Techrot | 0.02 | 1.76 | 3.5 | 0.76 |

### Overguard (Eximus Only)
```
f1(δ) = 1 + 0.0015 × δ^4   (δ < 45)
f2(δ) = 1 + 260 × δ^0.9    (δ > 50)
T = (δ - 45) / 5;  S2 = 3T² − 2T³  (45 ≤ δ ≤ 50)
Overguard = 12 × [f1(δ)·(1 − S2) + f2(δ)·S2]
```
Reference: δ=0→12.0 | δ=10→192.0 | δ=45→73,823.25 | δ=50→~105,592.8

### Armor Scaling
```
f1(δ) = 1 + 0.005 × δ^1.75
f2(δ) = 1 + 0.4   × δ^0.75
```
Hard-capped at 2700. **Do not truncate coefficients** — causes ~9 HP / ~2 OG drift vs wiki.

---

## Status Procs (`calculate_procs()`)

### DoT Procs
| Key | Damage | Notes |
|---|---|---|
| `slash` | 35% of step-2 total | Faction double-dips |
| `heat` | 50% of step-2 total | Faction double-dips; type eff. applied |
| `gas` | 50% of base × damage bonus × gas mod bonus | Faction double-dips; crit + body part applied |
| `toxin` | 50% of step-2 total | Faction double-dips; type eff. applied |
| `electricity` | 50% of step-2 total | Faction double-dips; type eff. applied |

### CC / Debuff Procs
| Key | Effect |
|---|---|
| `viral` | Health Vulnr. ×1.75–×4.25 |
| `magnetic` | +100% shield/OG dmg; forced Elec proc on shield break |
| `radiation` | Confuses enemy to attack allies for 12s |
| `blast` | −30% accuracy (up to −75%); detonates at 10 stacks |
| `cold` | −50% speed (up to −90%); +0.1 flat crit damage |

---

## Damage Type Effectiveness (Update 36.0+)
- **Vulnerable (+):** ×1.5
- **Resistant (−):** ×0.5

---

## Data Quality Notes

### mods.json — secondary stat fields
After regenerating `mods.json`, run patch scripts in order:
```bash
python scripts/fix_secondary_stats.py
python scripts/fix_galv_stats.py
```
Fields read by `loader.py`: `damage_bonus_pct`, `impact_pct`, `puncture_pct`, `slash_pct`, `crit_chance_pct`, `crit_damage_pct`, `status_chance_pct`, `multishot_pct`, `status_damage_pct`, `fire_rate_pct`, `magazine_pct`, `ammo_max_pct`, `reload_speed_pct`, `condition_overload_pct`

### mods.json — Conclave mods
Filtered via `/PvPMods/` substring in `InternalName`. Removes ~129 mods. Dual-use mods (diamond icon, `Conclave=True`) such as Eagle Eye are retained.

---

## Weapon Arcanes

### Pipeline Placement
- **damage_bonus** → additive with Serration in Step 1
- **headshot_bonus** (Deadhead) → additive to `body_part_multiplier` in Step 2, headshot only
- **cc_bonus / cd_bonus** (Cascadia Flare/Empowered) → pre-computed in `api.py`
- **reload_bonus** (Merciless) → applied to modded reload time for sustained DPS
- **flat_damage** (Cascadia Overcharge) → distributed proportionally among IPS types before Step 1

11 presets in `src/arcanes.py` — Merciless (×3), Deadhead (×3), Dexterity (×2), Cascadia Flare/Empowered/Overcharge.

**CLI:** `--arcane primary_merciless:12`. **API:** `arcanes: [{name, stacks}]`. `GET /api/arcanes` returns preset list.

---

## Warframe Ability Buffs

### Pipeline Placement
- **Roar** → Step 5, additive with Bane mods. Double-dips on DoT procs.
- **Eclipse** → Step 5.5, separate multiplicative after faction. No double-dip.
- **Xata's Whisper** → Independent Void hit, double-dips faction + headshot.
- **Nourish** → Step 1, adds Viral elemental damage.

Presets: `roar`, `eclipse`, `xatas_whisper`, `nourish` in `src/buffs.py`.

---

## Damage Falloff

### Formula
```
multiplier = 1 - reduction × clamp((distance - start) / (end - start), 0, 1)
```
Applied **after** all 6 quantized pipeline steps + multishot, as `math.floor(v * multiplier)`. DoT procs are NOT affected.

**API:** `distance` field on POST `/api/calculate`. Response includes `falloff_multiplier`.
**Web UI:** Distance input in Options panel, hidden for weapons without falloff.

---

## Live Data / Worldstate (`/live`)

### Data Source
DE's official endpoint: `https://api.warframe.com/cdn/worldState.php`. **Do not use `content.warframe.com`** — returns `403 host_not_allowed`.

### Server-side (`web/api.py`)
- `GET /api/worldstate?platform=pc` — in-memory `_ws_cache`, TTL = 60 seconds.
- Retries 3× with 2-second backoff. Stale fallback: returns last good data on failure. 503 only on cold cache.
- Parsing: `scripts/parse_worldstate.py`, imported dynamically. `parse(raw)` is the entry point.

### Nightwave Parser (`_parse_nightwave`)
- **Data source:** `raw.get("SeasonInfo")` — challenges in `SeasonInfo.ActiveChallenges`.
- **Prefix stripping:** `_NW_PREFIX = re.compile(r"^Season(EliteWeekly|Daily|Weekly)(Permanent|Hard)?")`
- **Trail number stripping:** `_NW_TRAIL_NUM = re.compile(r"\d+$")`
- **Elite detection:** `bool(re.search(r"Season(Weekly|EliteWeekly)?Hard|EliteWeekly", segment))`
- **Name lookup:** `_NW_NAMES` dict maps 50+ path keys → display names.
- **Dedup:** `seen_paths` set skips duplicate entries — DE returns dupes during rotation window.
- **Unknown keys:** Extract via `JSON.parse(document.body.innerText).SeasonInfo.ActiveChallenges.map(c => c.Challenge)` and add to `_NW_NAMES`.

### UI auto-refresh
Countdown timer: refreshes every **180 seconds**. Upstream TTL: 60 seconds. Manual refresh always fetches fresh.

### Node Name Lookup
`ALL_NODES` maps SolNode/SettlementNode/ClanNode/CrewBattleNode keys → `"Name (Planet)"`. `NODE_FACTION` maps same keys → faction string (fallback only).

**When fissures show raw node IDs:**
1. Open `https://api.warframe.com/cdn/worldState.php` in browser
2. Run: `JSON.parse(document.body.innerText).ActiveMissions.map(f => f.Node)`
3. Navigate to `wiki.warframe.com/w/PlanetName` and run:
   ```js
   [...document.querySelectorAll('tr')].map(r => r.innerText.trim())
     .filter(t => /\t(SolNode|ClanNode|CrewBattleNode|SettlementNode)\d+\t/.test(t))
     .map(t => { const node = t.match(/(SolNode|ClanNode|CrewBattleNode|SettlementNode)\d+/)[0]; return `"${node}": "${t.split('\t')[0]}"` })
   ```
4. Add missing entries to both `ALL_NODES` and `NODE_FACTION`.

### Live Page Panel Order
```
Cycles (standalone) → Void Fissures → Invasions → [Sortie + Archon Hunt] → [Nightwave + Baro] → Events
```
Paired panels use `.panel-stack` flex wrapper (column, 12px gap).

### Live Page — Key JS Functions
| Function | Purpose |
|---|---|
| `buildCyclesCard(cycles)` | Standalone full-width cycles block — `.cycles-standalone` |
| `buildFissureCard(fissures)` | Fissures panel — tier tabs + two-col list |
| `buildInvasionsCard(invasions)` | 3-col attacker/VS/defender layout |
| `buildNightwaveCard(nw)` | Nightwave challenges — Daily/Weekly/Elite tags + rep |
| `buildAlertBanner(alerts)` | Populates `#alert-banner` ticker; hides when empty |
| `renderAll(data)` | Panel order: cycles, fissures, invasions, sortie+archon stack, nightwave+baro stack, events |
| `loadData()` | Fetch + render; spinner on first load only |

### Fissure Categories
| Key | Condition |
|---|---|
| `railjack` | `f.is_railjack === true` |
| `requiem` | `f.tier === 'Requiem'` |
| `steelpath` | `f.is_steel_path === true` |
| `origin` | everything else |

### Live Page Typography Scale (do not regress)
| Tier | Size | Examples |
|---|---|---|
| Panel headings | `1rem` Orbitron | `.panel h2` |
| Primary row data | `1rem` | `.fissure-node`, `.nw-title`, `.alert-reward`, `.cycle-state`, `.sortie-boss` |
| Secondary text / ETAs | `0.85rem` | `.fissure-sub`, `.nw-eta`, `.alert-sub`, `.cycle-eta`, `.live-eta`, `.eta-chip` |
| Tags / badges / buttons | `0.73rem` | `.fissure-tier`, `.nw-tag`, `.invasion-vs`, `.refresh-btn` |
| Rewards / modifiers | `0.85rem` | `.reward-chip`, `.modifier-badge` |

### Live Page Layout Notes
- **`.live-page-wrap`** — flex-column wrapper: `#alert-banner` above `.app` for full-width ticker. `height: 100%; max-width: 1440px; margin: 0 auto`.
- **`#alert-banner`** — `display: none` when no alerts. Mobile: `mask-image` fades right edge for hamburger clearance.
- **`.live-grid` gap fix** — `@media (max-width: 1339px)` collapses to 1 column; skips 2-column zone where INVASIONS left dead space.
- **`.live-grid` dot background** — `radial-gradient` dots show only in empty grid areas.
- **Live page header** — `VOID CODEX` brand left, refresh timer right. No `<h1>`. HTML:
  ```html
  <header class="header">
    <div class="live-header-brand">
      VOID <span>CODEX</span>
      <div class="live-subtext" data-text="WORLD STATUS">WORLD STATUS</div>
    </div>
    <div class="refresh-info">
      <span>Refresh in <span id="refresh-countdown">180</span>s</span>
      <button class="refresh-btn" onclick="loadData()">&#8635; Now</button>
    </div>
  </header>
  ```

### Live Page — Countdown Timers
All expiring sections carry `expiry_ts` (Unix float). Global `setInterval` every second scans `[data-expiry]` elements and rewrites text to live countdown (e.g. `"1h 23m"`). Classes: `.eta-chip`, `.live-eta`.

### New CSS Classes (live.css)
| Class | Purpose |
|---|---|
| `.live-page-wrap` | Flex-column wrapper: `#alert-banner` above `.app` |
| `.live-header-brand` | Brand block in header — `display: block`, Orbitron `0.85rem`, letter-spacing `3px` |
| `.live-subtext` | Glitch subtext under brand — `0.55rem`, crimson, `::before`/`::after` cyan/red offset layers, `glitch-idle` 6s animation |
| `.cycles-standalone` | Standalone cycles panel |
| `.panel-stack` | `display: flex; flex-direction: column; gap: 12px` |
| `.invasion-sides` | `display: grid; grid-template-columns: 1fr auto 1fr` |
| `.invasion-attacker` | Left-aligned invasion side |
| `.invasion-defender` | Right-aligned invasion side |
| `.invasion-vs` | Center "VS" badge |

### News Thumbnails
Render as `<div>` with `background-image` (not `<img>`). Needs `background-size: cover; background-position: center`. Do not switch to `<img>`.
