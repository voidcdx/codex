# Handoff — Warframe Damage Calculator

## Current Status
**205 tests passing.** Full pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Web UI fully functional: dark theme, mod card grid, special slots, weapon images, riven mod builder, enemy level scaler, alchemy mixer.

Branch: `claude/review-documentation-DmcrV`

---

## What Was Done This Session

### 1. Missing secondary stat fields patched in `data/mods.json`
`scripts/fix_secondary_stats.py` — 109 field assignments across 9 stat types:

| Field | Count | Examples |
|---|---|---|
| `status_chance_pct` | 62 | Voltaic Strike, Malignant Force, Rifle Aptitude |
| `reload_speed_pct` | 15 | Chilling Reload (+40%), Burdened Magazine (−18%) |
| `magazine_pct` | 10 | Ice Storm (+40%), Depleted Reload (−60%) |
| `damage_bonus_pct` | 7 | Blaze (+60%), Vile Acceleration (−15%), Hollow Point |
| `status_damage_pct` | 6 | Boreal's Contempt, Elementalist series |
| `crit_damage_pct` | 4 | Bite (+220%), Magnetic Might (+40%) |
| `crit_chance_pct` | 2 | Critical Meltdown (+60%), Sacrificial Steel (+220%) |
| `multishot_pct` | 2 | Lethal Torrent (+60%), Containment Breach (+30%) |
| `ammo_max_pct` | 1 | Draining Gloom (−60%) |

Root cause: mods whose primary stat was already set were silently missing secondary/penalty stats because the parser only wrote the primary. The loader defaulted missing fields to 0, so live stats never updated for those mods.

Script logic: skips conditional effects ("while aiming", "on kill", "per combo", "for Xs", "for each"), companion mod types (Kavat/Kubrow/Hound/Predasite/Vulpaphyla/MOA), and ability augments.

### 2. Conclave (PVP-only) mods removed from `data/mods.json`
22 mods removed total:
- **21 fighting form mods** — shared `"Fighting form devised for Conclave."` in `effect_raw`.
- **Prize Kill** — no Conclave marker in data; identified manually. PVP survival mod with zero weapon stat fields.

`data/mods.json` now contains **1,512 mods** (was 1,534).

---

## Known Gaps / Next Candidates

### Kuva/Tenet bonus element %
Each Kuva/Tenet weapon has a bonus elemental damage % (e.g. 25–60% Heat on Kuva Bramma). The % is in `weapons.json` but **not applied in the damage pipeline**. Requires `bonus_element_pct` flowing through `load_weapon()` and added to the appropriate primary element bucket before combination.

### Weapon Arcanes
Deadhead, Merciless, Cascadia Flare — stack-based bonuses tied to kill/headshot triggers. Not implemented.

### More Conclave mods
Prize Kill had no Conclave text in data. More PVP-only mods may exist without the "Fighting form" phrase. Cross-reference wiki's Conclave mod category to find them.

---

## Data Counts
- `data/weapons.json` — 588 weapons
- `data/mods.json` — 1,512 mods
- `data/enemies.json` — 983 enemies

## Scripts
- `scripts/fix_secondary_stats.py` — secondary stat patcher; kept for re-use when data is refreshed
- `scripts/fix_fire_rate_mods.py` — fire rate patcher (previous session, same pattern)

## Tests
```bash
pytest   # 205 passing — run before every commit
```
