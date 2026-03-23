# Handoff — Warframe Damage Calculator

## Current Status
**210 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Web UI fully functional: dark theme, mod card grid, special slots, weapon images, riven mod builder (now with IPS stats), enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks input.

Branch: `claude/continue-handoff-RsV91`

---

## What Was Done This Session

### 1. IPS mod buffs implemented end-to-end
Mods like Rupture (+Impact%), Piercing Hit (+Puncture%), Jagged Edge (+Slash%) — 61 mods total — were parsed from `mods.json` but silently ignored by the damage pipeline.

**Changes:**
- `src/models.py` — `ips_bonuses: list[DamageComponent]` field added to `Mod`
- `src/loader.py` — `_IPS_FIELD` map reads `impact_pct`/`puncture_pct`/`slash_pct`; `_RIVEN_IPS_TYPES` added so Rivens can roll IPS stats; stale "not yet supported" comment removed
- `src/calculator.py` — `ips_bonus` lookup pre-computed per-type in both `calculate()` and `calculate_procs()` Step 1; IPS bonus stacks additively with general damage bonus for its type only
- `tests/test_calculator.py` — 2 new `TestIPSModBuffs` cases verify per-type selectivity and stacking
- `web/static/index.html` — Impact/Puncture/Slash added to Riven stat dropdown and `STAT_LABELS`

**Formula:** `Modded X = floor(Base X × (1 + Σdamage_mods + Σx_mods + CO + galv) × combo)`

### 2. Reproducible data pipeline (`scripts/fix_galv_stats.py`)
Galvanized mod fields (`galv_kill_stat`, `galv_kill_pct`, `galv_max_stacks`) were manually added to `mods.json` and would be lost on any rescrape. `fix_galv_stats.py` re-applies all 10 galvanized mod entries in one step.

**Full regeneration sequence (now documented in CLAUDE.md):**
```bash
python scripts/parse_wiki_data.py
python scripts/fix_secondary_stats.py
python scripts/fix_galv_stats.py
```

### 3. Conclave mod filtering automated
`parse_wiki_data.py` now filters `/PvPMods/` entries automatically via `InternalName`. Removes ~129 Conclave-exclusive mods. `mods.json` is down to 1,405 mods (was 1,534).

### 4. Kuva/Tenet bonus element — confirmed already implemented
Feature was fully wired (loader heuristic → calculator injection → API fields → UI selector). Removed stale CLAUDE.md note claiming it was unimplemented.

---

## Known Gaps / Next Candidates

### Condition Overload (medium effort)
`condition_overload_pct` is parsed from mods and stored in `Mod.condition_overload_bonus`, but the CO multiplier in `calculator.py` uses `unique_statuses` passed in by the caller — and the API/CLI never pass actual unique status counts. The field is plumbed but the caller-side wiring is missing. Also: CO's exact interaction with other damage bonuses needs wiki verification.

### IPS mod buffs on Riven — API not wired
The Riven builder UI now sends IPS stat keys (`"impact"`, `"puncture"`, `"slash"`) to the API. `make_riven_mod()` in `loader.py` now builds them into `ips_bonuses`. No additional wiring needed — the API sends `riven: {stats: [...]}` which goes through `make_riven_mod()` already.

### Weapon Arcanes
Deadhead, Merciless, Cascadia Flare — stack-based bonuses tied to kill/headshot triggers. Not modelled.

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
