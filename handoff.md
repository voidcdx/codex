# Handoff — Warframe Damage Calculator

> **Start of session:** always run `git pull` before making any changes to avoid merge conflicts with Cowork pushes.

## Current Status
**304 tests passing.** v0.8.1. `GAME_DATA_VERSION = "Update 42 — The Shadowgrapher"`.

**Branch:** `claude/continue-documentation-JrJt7`

Full damage pipeline, web UI, live tracker, reliquary, alchemy page (vanilla, post-Update 36 faction-based).

---

## What Was Done This Session

### 1. CLAUDE.md trimmed (321 → 198 lines)
- Removed verbose inline comments, condensed Data Refresh section, fixed stale references

### 2. Deleted `web/alchemy/` React app
- Old React/Vite sub-app removed from disk (was untracked)

### 3. Voruna Prime added
- `data/warframes.json` — new entry (455hp / 270sh / 265ar / 130en / 1.2sp)
- `web/static/images/warframes/Voruna-Prime.png` — portrait added

### 4. Perigale Prime + Sarofang Prime images added
- `web/static/images/weapons/Perigale-Prime.png`
- `web/static/images/weapons/Sarofang-Prime.png`

### 5. Update 42 data refresh
- `fetch_wiki_playwright.py` fixed — now fetches weapons subpages (`/primary`, `/secondary`, `/melee`, `/archwing`, `/companion`, `/railjack`, `/modular`, `/misc`) instead of stub module
- `data/weapons*.lua` — all 8 subpages downloaded and parsed
- `data/weapons.json` — refreshed (867 weapons; Perigale Prime + Sarofang Prime now present)
- `data/mods.json` — refreshed + Galvanized fields restored via `fix_galv_stats.py`
- `data/relics.json` — refreshed

### 6. HANDOFF.md merge conflict resolved
- Merged HEAD + remote (a67aa967) — no data lost
- Added `git pull` reminder at top

---

## Image Naming Conventions
- **Weapons:** hyphenated — e.g. `Braton-Prime.png`, `Perigale-Prime.png`
- **Warframes:** hyphenated — e.g. `Ash-Prime.png` (convention: `Name.replace(' ', '-') + '.png'`)
- **Sentinels:** hyphenated — e.g. `Carrier-Prime.png` (same convention as warframes)

## Data Refresh Workflow (Update NN)
```bash
# On Windows (wiki blocks sandbox fetches):
python scripts/fetch_wiki_playwright.py    # downloads all .lua files (weapons as 8 subpages)

# Parse in order:
python scripts/parse_lua.py               # → weapons_raw.json, mods_raw.json
python scripts/parse_wiki_data.py         # → weapons.json, mods.json, enemies.json
python scripts/parse_warframe_data.py     # → warframes.json
python scripts/parse_relic_data.py        # → relics.json
python scripts/fix_galv_stats.py          # restore Galvanized mod fields
pytest                                    # verify 304 pass

# Bump: src/version.py → GAME_DATA_VERSION = "Update NN — Name"
```

## Image Download Workflow
```bash
python scripts/fetch_images.py --resume        # all categories
python scripts/fetch_mod_images.py --resume    # mods only
```

---

## Pending / Known Issues
- **Element icons** — current SVGs are functional placeholders; user wants custom graphics (swap icon strings in `js/alchemy.js`)
- **Missing base element glyphs** — Cold, Electricity, Heat, Toxin PNGs not downloaded (run `fetch_images.py --category damage_types`)
- **Vaulted relic override is temporary** — will auto-correct on next wiki refresh once contributors update `Module:Void/data`
- **URL state / sharing** on alchemy page — not started
- **Mod images** not yet wired into UI — ready for mod picker redesign
- **Baro item names** — some guessed names may be wrong
- **252 weapon images missing** — not yet downloaded (run `fetch_images.py`)

---

## Prior Sessions Summary

### Nightwave act resolution — 11 new mappings
`scripts/parse_worldstate.py` `_NW_NAMES` + `_NW_DESCRIPTIONS` — 169 / 167 entries.
- `TransmuteMods`, `KillEnemiesWithCorrosive`, `FriendsDefense`, `HighGround`, `ZarimanBountyHunter`, `RiseOfTheMachine`, `CompleteMission`, `DeployGlyph`, `CompleteRace`, `KuvaSurvivalNoCapsules`
- Workflow: grep `data/nightwave_acts.json` to resolve new CamelCase keys

### Alchemy page — full vanilla port + faction rewrite
- Replaced React/Vite with vanilla HTML/CSS/JS — ~8KB vs 180KB bundle
- Post-Update 36: FACTION_META (13 factions), 2 cards (Strong Against / Resisted By)
- Glassmorphism via `.panel`, all colors via CSS vars, fonts via `--font-display`/`--font-body`

### Höllvania mojibake fix
- `web/api.py` `_fetch_drops()`: set `r.encoding = "utf-8"` — CDN serves without charset header

### Nightwave Resolution Workflow
1. Grep `data/nightwave_acts.json` for keywords from the CamelCase key
2. Add to `_NW_NAMES` + `_NW_DESCRIPTIONS` in `scripts/parse_worldstate.py`
3. For Elite collisions: use `_NW_ELITE_NAMES` / `_NW_ELITE_DESCRIPTIONS`
4. Run `pytest` (should stay at 304)

---

## Design Decisions Log
- All image folders use hyphenated filenames — e.g. `Braton-Prime.png`, `Ash-Prime.png`
- Alchemy: fully vanilla, faction-based multipliers, glassmorphism via `.panel`
- Nightwave: hardcoded dict in `parse_worldstate.py`, reference in `data/nightwave_acts.json`
- Vaulted override: manual flip in `relics.json` acceptable when wiki lags DE
- `r.text` unsafe for CDN HTML without charset — always set `r.encoding = 'utf-8'`
- Factions page: fully deleted; `.page-wrap` is shared dot-bg wrapper for all pages
