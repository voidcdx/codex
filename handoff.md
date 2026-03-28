# Handoff — Warframe Damage Calculator

## Current Status
**248 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional: dark theme, mod card grid, special slots (stance/exilus), weapon images, riven mod builder, enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks, inline SVG damage type icons. Live page (`/live`) with fissures, sorties, archon hunt, void trader, nightwave, alerts, invasions, cycles, events.

Branch: `codex`

---

## What Was Done This Session

### 1. Teal Railjack label in fissure tier column (`live.html` + `live.css`)
Railjack fissures now show a teal "Railjack" label in the tier column (same position as the red "Requiem" label). Removed the inline Storm tag that was previously in the node name line.

- `--void-teal: #3ddcb8` and `--void-teal-glow` added as CSS variables in `live.css`
- `TIER_COLORS` in `live.html` extended with `Railjack: '#3ddcb8'`
- Tier span logic updated: `f.is_railjack ? 'Railjack' : esc(f.tier)` with matching color
- SP tag retained in node name line; Storm tag removed

### 2. Fixed truncated f-string in `scripts/parse_worldstate.py`
Line 1390 was cut mid-line: `print(f"  Invasions:` — completed to `print(f"  Invasions:  {len(result['invasions'])}")`. This caused a `SyntaxError` on import, taking down the entire live page.

### 3. Git index corruption — diagnosed and fixed
The sandbox git (2.34.1) couldn't read the index written by Windows git (newer format). Root causes found and fixed:

- `.git/HEAD` had null bytes padded after the content — fixed by rewriting the file cleanly
- `.git/refs/heads/codex` had leading whitespace before the hash — stripped
- Added `[index] version = 2` to `.git/config` to force Windows git to always write v2 format (which sandbox git understands). This should prevent recurrence.
- If the index breaks again: use `GIT_INDEX_FILE=/sessions/relaxed-beautiful-fermi/tmp/<dir>/fresh_index git read-tree <sha>` then copy the result to `.git/index`

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
| `web/static/index.html` | Calculator SPA |
| `web/static/live.html` | Live Data SPA — worldstate, fissures, etc. |
| `web/static/live.css` | Live page styles — includes `--void-teal` game color var |
| `web/static/panels.css` | Shared panel/component styles — `--radius: 0` everywhere |
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

### Live Page Fissure Categories
| Key | Condition |
|-----|-----------|
| `railjack` | `f.is_railjack === true` |
| `requiem` | `f.tier === 'Requiem'` |
| `steelpath` | `f.is_steel_path === true` |
| `origin` | everything else |

Tier column shows the label ("Railjack", "Requiem", tier name) with its color from `TIER_COLORS`. SP tag shown inline in node name for steel path rows.

### Sandbox Git Notes
The sandbox runs git 2.34.1. Windows git writes a newer index format by default. We've set `[index] version = 2` in `.git/config` to prevent this. If the index breaks again (error: `unknown index entry format`):
```bash
# In sandbox:
TMPDIR=/sessions/relaxed-beautiful-fermi/tmp/fix
mkdir -p $TMPDIR
GIT_DIR=/sessions/relaxed-beautiful-fermi/mnt/codex/.git \
GIT_INDEX_FILE=$TMPDIR/fresh \
git read-tree <HEAD_SHA>
cp $TMPDIR/fresh /sessions/relaxed-beautiful-fermi/mnt/codex/.git/index
# Also check .git/HEAD for null bytes — rewrite clean if needed
```

---

## Known Gaps / TODO

### Not yet implemented
- **Kill Time (TTK)** — Shots and seconds to kill at given enemy level.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.

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
