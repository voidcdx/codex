# Handoff — Warframe Damage Calculator

## Current Status
**235 tests passing.** Full 6-step damage pipeline: weapon + mods + enemy → per-type damage breakdown + status procs (DoT + CC) + DPS. Warframe ability buffs (4 presets). Web UI fully functional: dark theme, mod card grid, special slots (stance/exilus), weapon images, riven mod builder, enemy level scaler, alchemy mixer, Kuva/Tenet bonus element selector, Galvanized Stacks, inline SVG damage type icons.

Branch: `claude/continue-handoff-fptyf`

---

## What Was Done This Session

### 1. Warframe Ability Buffs — added then trimmed to 4
Added a full buff system (`src/buffs.py`, `src/models.py` Buff dataclass) with pipeline placement per buff category. Initially 10 presets, then trimmed to 4 at user request:

| Buff | Category | Pipeline Step | Base Value |
|------|----------|---------------|------------|
| Roar (Rhino) | Faction-type | Step 5 — additive with Bane | +50% × strength |
| Eclipse (Mirage) | Damage multiplier | Step 5.5 — multiplicative | +200% × strength |
| Xata's Whisper (Xaku) | Elemental (Void) | Step 1 — adds damage | +26% × strength |
| Nourish (Grendel) | Elemental (Viral) | Step 1 — adds damage | +75% × strength |

- Roar double-dips on DoT procs (faction-type)
- Eclipse applies once to procs (no double-dip)
- Elemental buffs add to modded damage pool before quantization
- CLI: `--buff roar` or `--buff roar:1.5` (150% strength)
- API: `buffs: [{name: "roar", strength: 1.5}]`
- Web UI: dropdown + strength % input, multiple buffs supported

**Removed buffs:** Vex Armor, Octavia Amp, Sonar, Toxic Lash, Volt Shield, Wisp Haste — along with their Buff dataclass fields (`sonar_multiplier`, `crit_damage_bonus`, `electricity_bonus`, `fire_rate_bonus`).

### 2. Per-pellet status chance
Shotguns/multi-pellet weapons now correctly compute per-pellet status chance using `1 - (1 - total_sc)^(1/pellet_count)`. Displayed in CLI, API, and web UI.

### 3. Inline SVG damage type icons
All 15 damage types (Impact, Puncture, Slash, Heat, Cold, Electricity, Toxin, Blast, Corrosive, Gas, Magnetic, Radiation, Viral, True, Void) have inline SVG icons in the web UI results table.

---

## Architecture Quick Reference

### Damage Pipeline (6 Steps)
```
1. Base Damage × (1 + ΣDamageMods)         → Modded Base   [floor]
2. Modded Base × Body Part × Crit           → Part Damage   [round nearest]
3. Part Damage × Faction Type Effectiveness  → Typed Damage   [floor]
4. Typed Damage × Armor Mitigation          → Mitigated     [floor]
5. Mitigated × (1 + FactionMod + Roar)      → Final         [floor]
5.5. Final × Eclipse multiplier             → Buffed Final   [floor]
6. Buffed Final × Viral stacks              → Viral Damage   [floor]
```

### Key Files
| File | Lines | Purpose |
|------|-------|---------|
| `src/calculator.py` | 585 | 6-step pipeline + crit + armor + faction + Viral + procs |
| `src/loader.py` | 495 | JSON → Weapon/Mod/Enemy; case-insensitive; attack selection |
| `src/buffs.py` | 64 | 4 buff presets (Roar, Eclipse, Xata's Whisper, Nourish) |
| `src/models.py` | 98 | Weapon, WeaponAttack, Mod, Enemy, Buff, DamageComponent |
| `src/scaling.py` | 181 | Enemy level scaling per faction |
| `src/combiner.py` | 85 | Elemental combination by mod slot order |
| `src/quantizer.py` | 44 | quantize() — Decimal + ROUND_HALF_UP |
| `web/api.py` | 610 | FastAPI endpoints |
| `web/static/index.html` | 2,116 | SPA (dark theme) |
| `web/static/style.css` | 1,323 | Dark theme styles |
| `__main__.py` | 399 | CLI interface |

### Data Files
| File | Records | Size |
|------|---------|------|
| `data/weapons.json` | 588 weapons | 657 KB |
| `data/mods.json` | 1,405 mods | 370 KB |
| `data/enemies.json` | 983 enemies | 234 KB |

---

## Known Gaps / TODO

### Not yet implemented
- **Weapon Arcanes** — Deadhead, Merciless, Cascadia Flare. Stack-based bonuses not modelled.
- **Kill Time (TTK)** — Shots and seconds to kill at given enemy level.
- **Build saving / URL sharing** — Encode build state in URL params.
- **Mod optimizer** — Find highest-DPS mod combination for target faction/enemy.
- **Side-by-side comparison** — Two builds, DPS/TTK columns next to each other.

### Partially wired
- **Condition Overload** — `condition_overload_bonus` parsed and stored on Mod. Calculator uses `unique_statuses` parameter. But API/CLI never pass actual unique status counts from the UI — caller-side wiring missing.

### Design unsettled
- **Header / Branding** — Current plain header works but user wants something better. Previous attempts (SVG wings, hero banner) all removed. Needs mobile-first design (≤375px).

---

## Scripts (run order after rescrape)
```bash
python scripts/parse_wiki_data.py      # rebuild weapons.json + mods.json from raw
python scripts/fix_secondary_stats.py  # backfill 109 secondary stat fields
python scripts/fix_galv_stats.py       # restore 10 galvanized mod fields
```

## Tests
```bash
pytest   # 235 passing — run before every commit
```
