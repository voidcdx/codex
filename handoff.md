# Void Codex — Session Handoff

## Session summary
UI polish session focused on the Alchemy Guide modal and general web UX.
No logic changes; all 256 pytest tests still pass.

---

## Changes made

### 1. Alchemy Guide — major overhaul
Complete redesign of the Alchemy Mixer into "Alchemy Guide":
- Glassmorphism modal: `backdrop-filter: blur(22px) saturate(1.3)`, dark glass card rows
- Mod rows rendered by `alchModRow()` → `.alch-mod-row` (flex column):
  - `.alch-mod-row-main`: element icon, mod name, GALV badge, pct (+60, no %), +/− button
  - `.alch-stat-strip`: always-visible pills from `mod.effect` (parsed via API `effect_raw`)
- +/− toggle: equipped mods show red `−` (`alch-remove-btn`), unequipped show `+`
- `addAlchMod()` / `removeAlchMod()` update `modSlots[]`
- Element arcs: per-row-band offset fix so Gas arc lands on correct card row

### 2. Alchemy Guide — UX fixes
- **Mobile centering:** `#alchemy-mixer-overlay` overrides `.mod-picker-overlay`
  `align-items: flex-end` at ≤520px → stays centered via specific rule
- **Scroll bleed:** `overscroll-behavior: contain; -webkit-overflow-scrolling: touch`
  on `.alchemy-suggestions`; `overflow: hidden` on `.mod-picker-overlay.active`
- **Clear Mods button:** `.alchemy-modal-header` flex row (title + button).
  `clearAlchMods()` removes all `primary_element !== null` mods from `modSlots`.
  Button text: "Clear Mods". Hover: red tint.
- **Colored hover:** `color-mix(in srgb, var(--elem-color) 14%, ...)` on
  `.alch-mod-row:hover` for background, border, and `box-shadow` glow. No layout shift
  (stat strip is always-visible, not expand-on-hover).
- **Pct label:** `+60` not `+60%`; `text-align: center` on `.alch-mod-pct`

### 3. API — mods endpoint
`GET /api/mods` now returns `effect` field (plain-text `effect_raw`) so the
front-end can render stat pills without secondary-stat guessing.

### 4. Table overflow fix
`overflow-wrap: break-word; word-break: break-word` added to
`.breakdown-table th, .breakdown-table td` — long CC/Debuff effect text wraps
instead of stretching the table on narrow viewports.

### 5. Gas colour
`ELEM_COLORS.gas` changed from `#c0e040` (yellow-green) to `#00c8a0` (teal).
`PROC_COLORS.gas` auto-updates via reference.

---

## Current state
- Branch: `claude/review-handoff-notes-I3mZt`
- Version: `0.1.0` (no bump this session)
- Game data: Update 41 — The Old Peace
- Tests: 256 passing

---

## Start-of-session checklist for next Claude

> **Ask the user:** "Should I bump the version in `src/version.py` before we start? Current version is `0.1.0`."

- [ ] Run `pytest` — confirm 256 passing before touching anything
- [ ] Check `git log --oneline -5` to orient on recent commits
- [ ] Ask about version bump (see above)
