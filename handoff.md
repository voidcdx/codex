# Handoff — Warframe Damage Calculator

## Current Status
**248 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional: dark theme, mod card grid, special slots (stance/exilus), weapon images, riven mod builder, enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks, inline SVG damage type icons. Live page (`/live`) with fissures, sorties, archon hunt, void trader, nightwave, alerts, invasions, cycles, events.

Branch: `codex`

---

## What Was Done Recently

### Complete `ALL_NODES` + `NODE_FACTION` Rewrite (`scripts/parse_worldstate.py`)
Full planet-by-planet audit against wiki.warframe.com planet pages via Claude in Chrome browser tool. Both dicts completely replaced. Key changes:

**Planets with wholesale ID changes (DE renumbered these):**
- **Earth** — all nodes wrong (76→26=Lith, 149→228=Plains, 87→39=Everest, 63→79=Cambria, etc.)
- **Mars** — all nodes wrong (38→99=War, 64→106=Alator, 67→30=Olympus, 11→65=Gradivus, etc.)
- **Ceres** — all nodes wrong (157–181 range → 131–149 range)
- **Jupiter** — all nodes wrong (55/164/167/177/183/196 etc. → 53/100/125/126/74/87 etc.)
  - SolNode125=Io, SolNode195=Hydron (**was labeled "Io B (Jupiter)" — critical fix**)
- **Saturn** — all nodes wrong (47/90/14/24/91/92/93 etc. → 906/67/70/96/42/20/31 etc.)
- **Uranus** — mostly wrong (120→69=Ophelia, added 64=Umbriel, 33=Ariel, 105=Titania, 723=Brutus)
- **Sedna** — all wrong (115/116/40/8/51/77/70 etc. → 195/184/185/187/188/189/190 etc.)
- **Europa** — old code had 300–314 (those are **Lua**); correct IDs are 203–220
- **Lua** — old code had 132–139 (those are **Ceres**); correct IDs are 300–310
- **Eris** — all wrong (125/126/121/97/95/27/26/33/32/30 → 172/164/153/162/173/171/166/167/175 etc.)
- **Pluto** — all wrong (42/43/102/37/4/35/36/80/81/112/113/48/73 → 38/43/76/72/102/21/56/4/48/51 etc.)
- **Venus** — SolNode145/146 (wrong) → ClanNode0=Romula, SolNode902=Montes

**Railjack Proxima — complete reshuffle:**
- Old code had Earth Proxima as CrewBattleNode500–505 (now those are split differently)
- Correct current IDs: Earth=502/509/518/519/522/556/559, Venus=503/511–515, Saturn=501/530/533–535/557, Neptune=504/516/521/523–525/558, Pluto=526–529/531/536, Veil=538–543/550/553–555

**Nodes confirmed still correct:** Mercury, Phobos (SettlementNodes), Void, Deimos, Duviri

**Zariman:** corrected to SolNode230–235 (old 780–783 kept as fallback with correct names)

### Data Quality Note — Why Node IDs Change
DE re-exports `ExportRegions.json` with new SolNode IDs when they rework the star chart or move missions. The old IDs may remain in the worldstate simultaneously during transitions. The wiki community tracks these in planet pages and is the best available source. NODE_FACTION is only a **fallback** — the worldstate `Faction` field is present on most fissures, so wrong factions in NODE_FACTION only affect edge cases where the field is absent.

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
| `web/static/panels.css` | Shared panel/component styles (border-radius: 8px) |
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

### When Node IDs Are Wrong Again
1. Open `https://api.warframe.com/cdn/worldState.php` in browser
2. Run: `JSON.parse(document.body.innerText).ActiveMissions.map(f => f.Node)` to get active fissure keys
3. Cross-ref against `ALL_NODES` — anything missing shows as raw ID in the fissure list
4. Navigate to `wiki.warframe.com/w/PlanetName` and run this JS in browser console to scrape:
   ```js
   [...document.querySelectorAll('tr')].map(r => r.innerText.trim())
     .filter(t => /\t(SolNode|ClanNode|CrewBattleNode|SettlementNode)\d+\t/.test(t))
     .map(t => { const node = t.match(/(SolNode|ClanNode|CrewBattleNode|SettlementNode)\d+/)[0]; return `"${node}": "${t.split('\t')[0]}"` })
   ```
5. Add missing entries to both `ALL_NODES` and `NODE_FACTION`

---

## Known Gaps / TODO

### Not yet implemented
- **Kill Time (TTK)** — Shots and seconds to kill at given enemy level.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.

### Partially wired
- **Condition Overload** — parsed and stored on Mod. Calculator uses `unique_statuses` parameter but UI doesn't pass actual unique status counts.

### Node data drift
DE periodically re-exports `ExportRegions.json` with new IDs. The complete rewrite this session used wiki.warframe.com as source of truth, which is community-maintained and generally current but may lag. If raw IDs appear in fissures after a major update, run the audit workflow above.

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
