# Handoff — Warframe Damage Calculator

## Current Status
**248 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional: dark theme, mod card grid, special slots (stance/exilus), weapon images, riven mod builder, enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks, inline SVG damage type icons. Live page (`/live`) with fissures, sorties, archon hunt, void trader, nightwave, alerts, invasions, cycles, events.

Branch: `codex`

---

## What Was Done Recently

### Fissure Node Mapping Audit (`scripts/parse_worldstate.py`)
Pulled live worldstate from `api.warframe.com` via browser and cross-referenced against `ALL_NODES` + `NODE_FACTION`. Added 5 missing nodes that were showing as raw IDs in fissure display:

| Node | Name | Faction |
|---|---|---|
| `SolNode10` | Thebe (Jupiter) | Corpus |
| `SolNode18` | Rhea (Saturn) | Grineer |
| `SolNode166` | Nimus (Eris) | Infested |
| `SolNode175` | Naeglar (Eris) | Infested |
| `SolNode220` | Kokabiel (Europa) | Corpus |

`SettlementNode15` (Sharpless/Phobos) was already correctly mapped. `SolNode714` is not on the Deimos wiki and not currently appearing in live fissures — left as-is.

### Known Data Quality Issue — Jupiter/Eris Node IDs
The wiki now shows different SolNode IDs for Jupiter and Eris than what we have in `ALL_NODES`. Example conflicts:
- Wiki: `SolNode164` = Kala-azar (Eris); our code: `SolNode164` = Elara (Jupiter)
- Wiki: `SolNode167` = Oestrus (Eris); our code: `SolNode167` = Io (Jupiter)
- Wiki: `SolNode166` = Nimus (Eris) — added this session ✓

This suggests Jupiter/Eris nodes were re-numbered in an update. Both old and new IDs appear to be active in the worldstate simultaneously (observed `SolNode195` still active as Io B/Jupiter). A full audit of Jupiter and Eris IDs is needed but deferred.

---

## Architecture Quick Reference

### Damage Pipeline (6 Steps)
```
1. Base Damage × (1 + ΣDamageMods)          → Modded Base   [floor]
2. Modded Base × Body Part × Crit            → Part Damage   [round nearest]
3. Part Damage × Faction Type Effectiveness  → Typed Damage  [floor]
4. Typed Damage × Armor Mitigation           → Mitigated     [floor]
5. Mitigated × (1 + FactionMod + Roar)       → Final         [floor]
5.5. Final × Eclipse multiplier              → Buffed Final  [floor]
6. Buffed Final × Viral stacks               → Viral Damage  [floor]
```

### Key Files
| File | Purpose |
|------|---------|
| `src/calculator.py` | 6-step pipeline + crit + armor + faction + Viral + procs |
| `src/loader.py` | JSON → Weapon/Mod/Enemy; case-insensitive; attack selection |
| `src/buffs.py` | 4 buff presets (Roar, Eclipse, Xata's Whisper, Nourish) |
| `src/models.py` | Weapon, WeaponAttack, Mod, Enemy, Buff, DamageComponent |
| `src/scaling.py` | Enemy level scaling per faction |
| `src/combiner.py` | Elemental combination by mod slot order |
| `src/quantizer.py` | quantize() — Decimal + ROUND_HALF_UP |
| `web/api.py` | FastAPI endpoints |
| `web/static/index.html` | Calculator SPA — all JS inline |
| `web/static/live.html` | Live Data SPA — worldstate, fissures, news, etc. |
| `web/static/live.css` | Live page styles |
| `web/static/panels.css` | Shared panel/component styles (sharp edges, radius:0) |
| `scripts/parse_worldstate.py` | Worldstate parser — `parse(raw)` entry point; `ALL_NODES` + `NODE_FACTION` dicts |
| `__main__.py` | CLI interface |

### Data Files
| File | Records |
|------|---------|
| `data/weapons.json` | 588 weapons |
| `data/mods.json` | 1,405 mods |
| `data/enemies.json` | 983 enemies |

### Combobox Architecture
`setupCombobox(inputId, dropdownId, items, onSelect, getImageUrl)` in `index.html`:
- Dropdown is `position: absolute` inside `.combobox-wrap` — no portal
- `_confirmed` tracks last committed name; restored to input on abandon
- `.panel.combobox-open` lifts parent panel z-index when open
- Selection: `mousedown` (desktop) + `touchend` (mobile), both with `e.preventDefault()`
- Close: `mousedown` outside only (no touchstart)

### Live Page Node Lookup (`parse_worldstate.py`)
- `ALL_NODES` dict: SolNode/SettlementNode/ClanNode/CrewBattleNode → "Name (Planet)"
- `NODE_FACTION` dict: same keys → faction string (fallback when worldstate `Faction` field is missing)
- `_node_display(node_key, solnode_map)` strips Lotus paths, checks ALL_NODES first, then solnode_map fallback, then humanises the raw key
- `solnode_map.json` does not exist — no secondary fallback currently active
- When fissures show raw node IDs: pull `api.warframe.com/cdn/worldState.php` in browser, check `ActiveMissions[].Node`, look up on wiki planet pages to find the name

---

## Known Gaps / TODO

### Not yet implemented
- **Kill Time (TTK)** — Shots and seconds to kill at given enemy level.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.
- **Jupiter/Eris node ID audit** — Old IDs in ALL_NODES conflict with current wiki IDs; needs full planet-by-planet check via browser + wiki.

### Partially wired
- **Condition Overload** — parsed and stored on Mod. Calculator uses `unique_statuses` parameter but UI doesn't pass actual unique status counts.

---

## Scripts (run order after rescrape)
```bash
python scripts/parse_wiki_data.py      # rebuild weapons.json + mods.json from raw
python scripts/fix_secondary_stats.py  # backfill 109 secondary stat fields
python scripts/fix_galv_stats.py       # restore 10 galvanized mod fields
```

## Tests
```bash
pytest   # 248 passing — run before every commit
```
