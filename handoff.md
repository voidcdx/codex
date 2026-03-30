# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional.

**Version:** `0.5.8`
**Branch:** `claude/continue-handoff-8bCEE` — last commit `b575e0c`

---

## What Was Done This Session

### 1. Melee weapon stat display
- For `slot === 'Melee'`, "Fire Rate" label → "Atk Speed"
- Magazine, Reload, Multishot stat rows hidden for melee weapons
- `isMelee` flag added in `showWeaponStats()` in `weapons.js`

### 2. Fix: Base damage column showed quantized values
- Bug: `quantized_base_damage` from API response was being used for the Base column display
- Fix: Base column always uses raw `base_damage` from weapon data
- Modded column still uses quantized+calculated values as before
- `weapons.js` line 738

### 3. Data refresh investigation
- `fetch_wiki_data.py` confirmed blocked by wiki (403) — do not attempt
- Manual browser download flow works: download .lua → `parse_lua.py` → `parse_wiki_data.py`
- Enkaus (new weapon from last Wednesday's update) not yet in `Module:Weapons/data` on wiki
  - It's on the wiki as a page but not in the Lua data module yet
  - Will appear automatically on next data refresh once wiki module is updated
- `mods.json` updated successfully this session; `weapons.json` unchanged (no new data in module)
- Data refresh workflow documented in `CLAUDE.md` under "Data Refresh Notes"

---

## Pending / TODO

- Version bump pending — user deferred, ask at start of next session
- Enkaus weapon: re-run data refresh once wiki module is updated (check `Module:Weapons/data?action=raw`)
- Calculator going public-facing — data accuracy is a known concern; established weapons are stable, newly reworked/released weapons may have stale data

---

## Key Files Changed This Session
- `web/static/js/weapons.js` — melee stat display + base damage column fix
- `CLAUDE.md` — added Data Refresh Notes section
- `data/mods.json` — refreshed from wiki
- `data/mods_data.lua` / `data/mods_raw.json` — updated source files

---

## Git Notes
- Working branch: `claude/continue-handoff-8bCEE`
- Commits pushed to remote; user merges to main on their Windows machine
- User is on branch `codex` locally on Windows — they merge from the claude branch
