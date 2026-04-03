# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** v0.8.0. Full damage pipeline, web UI, live tracker, reliquary.

**Branch:** `claude/continue-handoff-docs-YjbJQ`

---

## What Was Done This Session

### 1. Warframe Stats Pipeline
- Downloaded `warframes_data.lua` + `companions_data.lua` from wiki
- `scripts/parse_warframe_data.py` → `data/warframes.json` (59 Prime entries)
  - 51 warframes, 1 archwing (Odonata Prime), 7 companions
  - Stats: health, shield, armor, energy, sprint
- `GET /api/warframes` endpoint + `_raw_warframes()` loader
- Reliquary shows real stat bars for warframes (replaces placeholder dashes)
- Sentinel stats still placeholder (companion data doesn't map to Reliquary sentinel type cleanly)

### 2. Mod Images
- Downloaded 1,186 mod card PNGs → `web/static/images/mods/`
- `image` field injected into `mods.json` (1,404 of 1,405 mods)
- `scripts/fetch_mod_images.py` — Playwright batch downloader
- 4 failed (exalted weapon stances — 404s, not needed)

### 3. Game Image Library (4,036 total)
Downloaded 6 additional image categories via `scripts/fetch_images.py`:

| Category | Count | Folder |
|---|---|---|
| Mods | 1,196 | `images/mods/` |
| Enemies | 899 | `images/enemies/` |
| Resources | 871 | `images/resources/` |
| Weapons | 619 | `images/weapons/` |
| Abilities | 216 | `images/abilities/` |
| Arcanes | 162 | `images/arcanes/` |
| Warframes | 50 | `images/warframes/` |
| Damage types | 12 | `images/damage_types/` |
| Sentinels | 6 | `images/sentinels/` |
| Relics | 5 | `images/relics/` |

Missing: Eterna + Vanguard relic icons (404 on wiki — too new)

### 4. Misc
- Warframe images moved to right side in Reliquary (matching weapons)
- Verified "27 placeholder weapons" — actually correct wiki data (equal IPS splits confirmed)
- Version bumped to 0.8.0

---

## Key Files Changed
```
src/version.py                    # 0.7.0 → 0.8.0
src/loader.py                     # + _raw_warframes()
web/api.py                        # + GET /api/warframes
web/static/js/reliquary.js        # real warframe stats, images right side
data/warframes.json               # 59 Prime entries (new)
data/mods.json                    # + image field on 1404 mods
data/warframes_data.lua           # raw wiki source (new)
data/companions_data.lua          # raw wiki source (new)
data/arcanes_data.lua             # raw wiki source (new)
data/resources_data.lua           # raw wiki source (new)
data/manifest_*.json              # 6 download manifests (new)
scripts/parse_warframe_data.py    # warframes + archwings + companions parser (new)
scripts/fetch_mod_images.py       # mod image downloader (new)
scripts/fetch_images.py           # universal batch image downloader (new)
scripts/parse_wiki_data.py        # + image field in _parse_mod()
```

---

## Pending / Known Issues
- **URL state / sharing** — not started
- **Eterna + Vanguard relic icons** — wiki 404s, check back later
- **Sentinel stats** — companions_data.lua has stats but Reliquary sentinel classification (Carapace/Cerebrum parts) doesn't map to companion names automatically

---

## Image Download Workflow
```bash
# On Windows (wiki blocks automated fetch from sandbox):
python scripts/fetch_images.py                        # all categories
python scripts/fetch_images.py --category arcanes     # single category
python scripts/fetch_images.py --resume               # skip existing
python scripts/fetch_mod_images.py --resume            # mods only
```

Manifests in `data/manifest_*.json` map names → wiki filenames.
Wiki URL pattern: `https://wiki.warframe.com/w/Special:Redirect/file/{filename}`

## Data Refresh Workflow
```bash
# On Windows (Playwright):
python scripts/fetch_wiki_playwright.py               # downloads .lua files

# Then parse:
python scripts/parse_lua.py                           # → weapons_raw.json, mods_raw.json
python scripts/parse_wiki_data.py                     # → weapons.json, mods.json, enemies.json
python scripts/parse_warframe_data.py                 # → warframes.json
python scripts/parse_relic_data.py                    # → relics.json
pytest                                                # verify
```

## Design Decisions Log
- Warframe/sentinel images on RIGHT side (same as weapons, tilted -8deg)
- Real stat bars for warframes, placeholders for sentinels until data mapping solved
- Equal IPS splits are valid wiki data — not placeholders
- Mod images not yet wired into UI — ready for mod picker redesign
- All other downloaded images (enemies, arcanes, abilities, resources, damage types, relics) stored for future use
