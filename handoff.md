# Void Codex — Session Handoff

## Session summary
Bug-fix + UI polish session on top of v0.5.1. Fixed crit/damage math bugs, weapon data issues, dropdown styling, and added Cold proc CDM support.

---

## Changes made this session

### Damage math fixes
- **CC formula** corrected to multiplicative: `base_cc × (1 + sum_mods)` — was additive
- **Blood Rush / Weeping Wounds** now scale with combo tiers (were applying flat at ×1 combo)
- **Multishot** result floored to integer: `math.floor(v * multishot)` in `src/calculator.py`
- **Cold proc CDM**: `+0.1` flat per stack (max 10), applied after relative bonuses in both `/api/calculate` and `/api/modded-weapon`. New `cold_stacks: int` field on both request models.

### Weapon data fixes
- Torid all 3 attacks corrected (Grenade Impact, Poison Cloud, Incarnon Form)
- Mutalist Quanta `crit_multiplier` fixed: `0.0 → 1.5`
- Synoid Simulor `crit_multiplier` fixed: `0.0 → 1.0`

### Mod system fixes
- **Mod family exclusivity**: Primed/Umbral/Archon variants block base version in mod picker and Alchemy Mixer
  - `_mod_family()` in `src/loader.py` strips prefixes; `family` field on `Mod` dataclass
  - Picker filters by `inUseFamilies`; Alchemy Mixer guards `addAlchMod()`
- **mods.json**: Blood Rush `crit_chance_pct → cc_per_combo_tier: 0.4`; Weeping Wounds `sc_per_combo_tier: 0.4`

### New features
- **Cold Stacks input** in Hit Options (0–10, same row as Viral/Corrosive)
- **`scripts/validate_weapons.py`**: flags zero damage, CC/SC out of range, impossible CM, fire_rate=0, single-element 100.0 placeholder. Supports `--slot`, `--severity`, `--weapon`.

### UI fixes
- Stack inputs (Viral, Corrosive, Cold) clamped 0–10 via `oninput`
- **Select dropdowns** (Hit Type, Body Part, Bonus Element): replaced native `<select>` (iOS picker) and broken custom-select widget with new `setupSelectDropdown()` — hides native select, builds button + `.combobox-dropdown` div reusing `.combobox-item` CSS so all dropdowns look identical

### JS/CSS cleanup
- Removed entire custom-select system (`_buildCustomSelectUI`, `setupCustomSelect`, `refreshCustomSelect`, `setCustomSelectValue`, all `.custom-select-*` CSS)
- New functions in `web/static/js/utils.js`: `setupSelectDropdown(selectId, onChange)`, `refreshSelectDropdown(selectId)`
- New CSS in `panels.css`: `.sel-wrap`, `.sel-btn`, `.sel-dropdown`, `.combobox-item.sel-selected`

---

## Design system rules (ENFORCE THESE)

| Rule | Detail |
|---|---|
| No hardcoded `rgba()` | Always use CSS variables |
| No `style=` inline attrs | Extract to CSS classes (SVG attrs excepted) |
| No rounded corners | `--radius: 0`, `--radius-sm: 0` everywhere |
| No glassmorphism | `backdrop-filter` on `#050505` is invisible. Rejected 5+ times. Do not retry. |
| No `▶` in CSS `content:` | Renders as emoji on iOS. Use `→` (U+2192) |
| No native `<select>` | Use `setupSelectDropdown()` — native renders as iOS picker |

**CSS variable reference:**
`--bg` `--surface` `--surface-solid` `--surface2` `--border` `--border-highlight` `--border-red` `--accent` `--accent2` `--accent-glow` `--text` `--text-field` `--text-dim` `--crimson` `--crimson-bright` `--riven`

---

## CSS class inventory

| Class | File | Purpose |
|---|---|---|
| `.panel-sub-h` | panels.css | Section heading divider |
| `.btn-add` | panels.css | `+ ADD` button |
| `.input-sm` | panels.css | Compact 44px number input |
| `.input-sm-wide` | panels.css | Compact 52px number input |
| `.input-level` | panels.css | 72px enemy level input |
| `.sel-wrap` | panels.css | Wrapper for themed select dropdown |
| `.sel-btn` | panels.css | Trigger button for themed select |
| `.sel-dropdown` | panels.css | Dropdown container (extends `.combobox-dropdown`) |
| `.combobox-item.sel-selected` | panels.css | Highlighted selected option |
| `.sc-wrap` | results.css | Two-column weapon stat split |
| `.sc-div` | results.css | Crimson vertical divider |
| `.sc-val-lg` / `.sc-val-sm` | results.css | Large/small stat values |
| `.sc-modded` | results.css | Modded value row (`→` prefix) |

---

## Known issues / pending

- **Friday night task**: Refresh `weapons.json` + `mods.json` via wiki ApiSandbox, then re-run `scripts/validate_weapons.py` (27 MEDIUM 100.0 placeholder issues remain)
- **Low priority**: CDM quantization `Round(Base CDM × 4095/32) × 32/4095`
- **Low priority**: Arcane Crepuscular, Tenacious Bond, Shroud of Dynar absolute CD bonuses
- Cycles + Events not yet rendered in `live.html` (data parsed, cards not built)
- Riven modal — not touched recently. Get screenshot before changing.

---

## Feature backlog

1. Side-by-side Build Compare (panel hidden, placeholder exists)
2. Mod Optimizer — brute-force best mod per slot
3. Armor Strip modeling
4. Damage Falloff
5. EHP Calculator (needs Warframe DB)
6. Status Simulator
7. Build Cards (export image)
8. Build Sharing (URL-encoded state)
9. Live Data — Cycles + Events cards

---

## Current state
- Branch: `claude/review-handoff-oooHw`
- Version: `0.5.2`
- Game data: Update 41 — The Old Peace
- Tests: 283 passing
- Railway deploy branch: `codex`

---

## Start-of-session checklist

> **Ask before touching code:**
> 1. "Should I bump the version? Current: `0.5.2`"
> 2. "Should this session be tracked in the changelog?"
> Do NOT auto-bump or add entries without confirmation.
> Update BOTH `CHANGELOG.md` AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 283 passing
- [ ] `git log --oneline -5` to orient
- [ ] Ask version + changelog questions
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism / `▶` in CSS
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
