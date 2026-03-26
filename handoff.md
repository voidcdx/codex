# Void Codex — Session Handoff

## Session summary
Added CDM (critical damage multiplier) quantization — `Round(CDM × 4095/32) × 32/4095` — snapping modded CDM to the game's internal precision grid before feeding into the crit formula.

---

## Changes made this session

### CDM quantization
- `src/quantizer.py`: new `quantize_cdm(cdm)` — `Round(CDM × 4095/32) × 32/4095`, Decimal precision, ROUND_HALF_UP
- `web/api.py`: applied `quantize_cdm()` at both CDM computation sites — `/api/modded-weapon` (display) and `/api/calculate` (damage calc)
- `tests/test_quantization.py`: 7 new tests — grid values (1x/2x/3x), typical modded CM, half-boundary rounding, idempotency
- `CHANGELOG.md` + `CHANGELOG_ENTRIES` in `constants.js`: entry added under 0.5.3

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
| `.btn-help` | panels.css | `?` help toggle (crimson, no border) |
| `.panel-help` / `.panel-help.hidden` | panels.css | Inline help block; hidden by default |
| `.panel-toggle-with-help` | panels.css | Transfers auto-margin from chevron to btn-help |
| `.input-sm` | panels.css | Compact 44px number input |
| `.input-sm-wide` | panels.css | Compact 52px number input |
| `.input-level` | panels.css | 72px enemy level input |
| `.sel-wrap` | panels.css | Wrapper for themed select dropdown |
| `.sel-btn` | panels.css | Trigger button for themed select |
| `.sel-dropdown` | panels.css | Dropdown container (extends `.combobox-dropdown`) |
| `.combobox-item.sel-selected` | panels.css | Highlighted selected option |
| `.strip-row` / `.strip-label-row` | panels.css | Armor strip panel row layout |
| `.strip-slider` | panels.css | Range input (crimson thumb, no border-radius) |
| `.strip-result-block` / `.strip-bar-fill` | panels.css | Armor/DR summary + progress bar |
| `.sc-wrap` | results.css | Two-column weapon stat split |
| `.sc-div` | results.css | Crimson vertical divider |
| `.sc-val-lg` / `.sc-val-sm` | results.css | Large/small stat values |
| `.sc-modded` | results.css | Modded value row (`→` prefix) |

---

## Known issues / pending

- Refresh `weapons.json` + `mods.json` via wiki ApiSandbox (27 MEDIUM 100.0 placeholder issues remain)
- Arcane Crepuscular, Tenacious Bond, Shroud of Dynar absolute CD bonuses (low priority)
- Cycles + Events not yet rendered in `live.html` (data parsed, cards not built)
- Riven modal — not touched recently. Get screenshot before changing.

---

## Feature backlog

1. Side-by-side Build Compare (panel hidden, placeholder exists)
2. Mod Optimizer — brute-force best mod per slot
3. Damage Falloff
4. EHP Calculator (needs Warframe DB)
5. Status Simulator
6. Build Cards (export image)
7. Build Sharing (URL-encoded state)
8. Live Data — Cycles + Events cards

---

## Current state
- Branch: `claude/review-handoff-WKaVA`
- Version: `0.5.3`
- Game data: Update 41 — The Old Peace
- Tests: 297 passing
- Railway deploy branch: `codex`

## Private notes
`~/.claude/codex-accuracy.md` — accuracy self-assessment (what the calculator gets right, where the gaps are). Outside the repo, never pushed. Read on request.

---

## Start-of-session checklist

> **Ask at HANDOFF, not session start:**
> 1. "Should I bump the version? Current: `0.5.3`"
> 2. "Should this session be tracked in the changelog?"
> Do NOT auto-bump or add entries without confirmation.
> Update BOTH `CHANGELOG.md` AND `CHANGELOG_ENTRIES` in `web/static/js/constants.js`.

- [ ] Run `pytest` — confirm 297 passing
- [ ] `git log --oneline -5` to orient
- [ ] No hardcoded rgba / inline styles / rounded corners / native selects / glassmorphism / `▶` in CSS
- [ ] Update Guide modal when adding UI features
- [ ] Railway deploys from `codex` — push feature branch AND merge to `codex`
