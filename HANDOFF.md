# Handoff — Warframe Damage Calculator

## Current Status
**210 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Web UI fully functional: dark theme, mod card grid, special slots, weapon images, riven mod builder (with IPS stats), enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks input.

Branch: `claude/continue-handoff-FSGRD`

---

## What Was Done This Session

### 1. Banner — iterated and reverted
Attempted two banner approaches:
1. Flanking SVG wings flanking an `<h1>` in the header — broke on mobile (wings stacked vertically at narrow widths)
2. Full-width `.site-hero` hero banner (`viewBox="0 0 900 80"`) with VOID ◈ CODEX composition, corner brackets, trace lines, central Orokin medallion — removed by user request

**Net result:** Both removed. Header is now a minimal compact sticky nav: `<span class="nav-brand">Void Codex</span>` + nav links. No decorative SVG in the header.

**CSS state:** `.banner-lockup` and `.banner-wing` rules removed. `.nav-brand` added. Header padding reduced to `9px 24px`.

---

## Known Gaps / Next Candidates

### Condition Overload (medium effort)
`condition_overload_pct` is parsed from mods and stored in `Mod.condition_overload_bonus`, but the CO multiplier in `calculator.py` uses `unique_statuses` passed in by the caller — and the API/CLI never pass actual unique status counts. Field is plumbed but caller-side wiring is missing. Also: CO's exact interaction with other damage bonuses needs wiki verification.

### Weapon Arcanes
Deadhead, Merciless, Cascadia Flare — stack-based bonuses tied to kill/headshot triggers. Not modelled.

### Header / Branding
User is not happy with the current plain header but no direction was settled on this session. Needs a design that works on both desktop and mobile.

---

## Data Counts
- `data/weapons.json` — 588 weapons
- `data/mods.json` — 1,405 mods (129 Conclave-exclusive removed)
- `data/enemies.json` — 983 enemies

## Scripts (run order after rescrape)
```bash
python scripts/parse_wiki_data.py      # rebuild weapons.json + mods.json from raw
python scripts/fix_secondary_stats.py  # backfill 109 secondary stat fields
python scripts/fix_galv_stats.py       # restore 10 galvanized mod fields
```

## Tests
```bash
pytest   # 210 passing — run before every commit
```
