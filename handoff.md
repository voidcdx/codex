# Handoff — Warframe Damage Calculator

## Current Status
**248 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional. Live page (`/live`) fully rebuilt: cycles standalone panel, fissures, invasions (reformatted), sortie, archon hunt, nightwave (fully populated), baro, alert banner, events.

**Version:** `0.5.6`
**Branch:** `claude/review-handoff-notes-ciJK9` — last commit `869b28d`

---

## What Was Done This Session

### 1. Version bump
`0.5.5` → `0.5.6`

### 2. Invasions panel — full reformat
- New 3-column layout: `[Attacker + reward] | VS | [Defender + reward]`
- ETA chip hidden when no expiry (was showing `?`)
- Empty reward chips hidden (Infested side has no reward)
- Reward chip borders removed
- `.invasion-header`, `.invasion-sides`, `.invasion-side`, `.invasion-attacker`, `.invasion-defender`, `.invasion-faction` CSS classes

### 3. Live page panel order (final)
```
Cycles (standalone) → Void Fissures → Invasions → Sortie+Archon Hunt (stacked) → Nightwave+Baro (stacked) → Events
```
- `.panel-stack` wrapper: `display: flex; flex-direction: column; gap: 12px` — keeps paired panels in same grid column at any width
- Mobile: collapses naturally to single column

### 4. Nightwave panel — fully populated
**Root cause:** challenges were in top-level `SeasonInfo`, not `SyndicateMissions`.

**Parser fixes (`scripts/parse_worldstate.py`):**
- `_parse_nightwave(raw: dict)` now reads `raw.get("SeasonInfo")`
- Call site changed: `_parse_nightwave(raw)` instead of `_parse_nightwave(raw.get("SyndicateMissions", []))`
- Field names corrected: `Daily` (not `isDaily`), elite detected via `SeasonWeeklyHard` in segment
- `_NW_PREFIX` regex: `^Season(EliteWeekly|Daily|Weekly)(Permanent|Hard)?` — strips both primary and secondary prefixes
- `_NW_TRAIL_NUM`: strips trailing variant numbers (e.g. `22`)
- `_nw_title(path)` helper: extracts segment, strips prefix+number, looks up `_NW_NAMES`, falls back to CamelCase split

**Known challenge name mappings (`_NW_NAMES`):**
| Path key | Display name |
|---|---|
| `VisitFeaturedDojo` | Just Visiting |
| `DeployAirSupport` | Air It Out |
| `DonateLeverian` | Donate to the Leverian |
| `CompleteMissions` | Mission Complete |
| `KillEximus` | Eximus Eliminator |
| `KillEnemies` | Not a Warning Shot |
| `UnlockDragonVaults` | Vault Looter |
| `CompleteTreasures` | Animator |
| `KillOrCaptureRainalyst` | Hydrolyst Hunter |
| + many more | see `_NW_NAMES` dict |

**UI:** Nightwave tag borders removed. Daily=blue, Weekly=orange, Elite=crimson.

### 5. Open World Cycles — standalone panel
- Decoupled from Void Fissures panel
- `buildCyclesCard()` returns `<div class="cycles-standalone live-card-full">` (no `.panel` class)
- `.cycles-standalone` styled manually: `background: var(--surface)`, `border: 1px solid var(--border)`, `border-radius: 8px`, `margin-top: 4px`, `padding: 10px 16px`
- `::before`: top + bottom crimson gradient matching `.panel::before` (`rgba(220,20,60,0.55)`)
- `::before` suppresses the top panel glow to avoid double border with news ticker

### 6. Void Fissures heading moved
`<h2>Void Fissures</h2>` now renders **after** the cycles strip (which is now standalone), above tier tabs. `buildFissureCard(fissures)` — cycles param removed.

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
| `web/static/live.html` | Live Data SPA |
| `web/static/base.css` | CSS variables |
| `web/static/live.css` | Live page styles |
| `web/static/panels.css` | Shared panel styles — top+bottom gradient via `::before` |
| `scripts/parse_worldstate.py` | Worldstate parser — `parse(raw)`; `_parse_nightwave(raw)`; `ALL_NODES`; `_NW_NAMES` |
| `__main__.py` | CLI interface |

### Data Files
| File | Records |
|------|---------|
| `data/weapons.json` | 588 weapons |
| `data/mods.json` | 1,405 mods |
| `data/enemies.json` | 983 enemies |

### Live Page — Key JS Functions (`live.html`)
| Function | Purpose |
|----------|---------|
| `buildCyclesCard(cycles)` | Standalone full-width cycles block (no `.panel`) |
| `buildFissureCard(fissures)` | Fissures panel — tier tabs + two-col list (no cycles) |
| `buildInvasionsCard(invasions)` | 3-col attacker/VS/defender layout |
| `buildNightwaveCard(nw)` | Nightwave challenges — Daily/Weekly/Elite tags + rep |
| `buildAlertBanner(alerts)` | Populates `#alert-banner` ticker; hides when empty |
| `renderAll(data)` | Panel order: cycles, fissures, invasions, sortie+archon stack, nightwave+baro stack, events |
| `loadData()` | Fetch + render; spinner on first load only |

### Live Page Fissure Categories
| Key | Condition |
|-----|-----------|
| `railjack` | `f.is_railjack === true` |
| `requiem` | `f.tier === 'Requiem'` |
| `steelpath` | `f.is_steel_path === true` |
| `origin` | everything else |

### Sandbox Git — Commit Workaround
Cowork's background git sync holds `index.lock`, blocking sandbox commits. Commit from Windows terminal instead:
```
cd C:\Users\jesse\Desktop\codex
git add -A && git commit -m "..."
```
`.git/config` has `[index] version = 2` to keep index format compatible between Windows git and sandbox git 2.34.1.

---

## Known Gaps / TODO

- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.
- **Nightwave challenge names** — Some path keys still fall back to CamelCase split. Add to `_NW_NAMES` as they're identified in-game.
- **Deployment** — Railway blocks `api.warframe.com`. Use VPS (DigitalOcean, Hetzner) or Fly.io for hosting.

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
