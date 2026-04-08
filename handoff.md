# Handoff — Warframe Damage Calculator

> **Start of session:** always run `git pull` before making any changes to avoid merge conflicts with Cowork pushes.

## Current Status
**304 tests passing.** v0.8.1. `GAME_DATA_VERSION = "Update 42 — The Shadowgrapher"`.

**Branch:** `claude/continue-documentation-JrJt7`

Full damage pipeline, web UI, live tracker, reliquary, alchemy page (vanilla, post-Update 36 faction-based).

---

## What Was Done This Session

### 1. CLAUDE.md cleanup
- Removed stale note about `web/alchemy/` React app ("still exists but is no longer served — can be deleted")

### 2. Deleted `web/alchemy/`
- Old React/Vite alchemy sub-app fully removed from disk (was untracked)
- Vanilla port at `web/static/alchemy.html` + `alchemy.css` + `js/alchemy.js` is the canonical page

### 3. Voruna Prime added
- `data/warframes.json` — new entry (455hp / 270sh / 265ar / 130en / 1.2sp)
- `web/static/images/warframes/Voruna-Prime.png` — portrait added

### 4. HANDOFF.md merge conflict resolved
- Merged HEAD + remote (a67aa967) — no data lost

---

## Prior Sessions Summary (for context)

### Factions page deleted
- Removed `factions.html`, `factions.css`, `factions.js`, API route, and sidebar nav entries
- Renamed `.factions-wrap` → `.page-wrap` in `layout.css` (shared wrapper with dot bg)

### Nightwave act resolution — 11 new mappings
`scripts/parse_worldstate.py` `_NW_NAMES` + `_NW_DESCRIPTIONS` dicts now have 169 / 167 entries.

**First batch (4 + 1 rename):**
- `TransmuteMods` → "Everything Old is New Again"
- `KillEnemiesWithCorrosive` → "Meltdown"
- `FriendsDefense` → "Defense"
- `HighGround` → "High Ground"
- `KillEnemies` renamed from "Not A Warning Shot" → "Not A Warning Shot XXIV"
- `KillEnemiesWithHeadshots` → "Not A Warning Shot" (new mapping for the original title)

**Second batch (6 from live worldstate, resolved via wiki scrape):**
- `ZarimanBountyHunter` → "Zariman Bounty Hunter" (Weekly)
- `RiseOfTheMachine` → "Rise of the Machine" (Elite)
- `CompleteMission` → "Agent" / "Complete a Mission" (Daily, alias)
- `DeployGlyph` → "Graffiti" / "Deploy a Glyph while on a mission" (Daily, alias)
- `CompleteRace` → "Ollie Oop!" / "Play Ollie's Crash Course and complete a race" (Weekly, user-verified)
- `KuvaSurvivalNoCapsules` → "Hold Your Breath" / "Survive for over 20 minutes in Kuva Survival" (Elite, user-verified)

**Workflow used:** Cowork scraped `wiki.warframe.com/w/Nightwave` → `data/nightwave_acts.json` (131 acts with name/description/tier). Future sessions: grep that file to resolve new CamelCase keys as they appear.

### Alchemy page — faction-based rewrite
- Discovered page was using pre-Update 36 health-type multipliers (Ferrite, Alloy, Cloned Flesh, Shields) that no longer affect damage in-game
- Rewrote `web/static/js/alchemy.js`:
  - ELEMENTS data now has `factions: { 'Grineer': 0.5, ... }` instead of `multipliers: { armor: [...] }`
  - Added `FACTION_META` with 13 factions (Grineer, Kuva Grineer, Narmer, Corpus, Corpus Amalgam, Infested, Deimos Infested, Corrupted, Sentient, Murmur, Scaldra, Techrot, Anarchs) — each with color, short code, SVG glyph
  - `renderCards()` now emits 2 cards: "Strong Against" (positive) + "Resisted By" (negative) instead of 4 health-type cards
  - Source of truth: `src/calculator.py` FACTION_EFFECTIVENESS table (extracted from wiki.warframe.com/w/Damage/Overview)
  - Updated `TACTIC_TIPS` with faction-based tactical advice

### Alchemy page — glassmorphism styling
- Added `.panel` class to wheel card, combiner, selected banner, tactic card, dynamic faction cards
- Removed `<div class="alchemy-section-label">Interactive Elemental Matrix</div>`
- Renamed "Tactical Optimization" → "Optimization"
- Replaced all hardcoded gold `#c5a059` / `rgba(197,160,89,...)` with crimson `var(--accent2)` + `var(--accent-aXX)` alpha stops
- Fonts normalized: `var(--font-display)` (Exo 2) / `var(--font-body)` (Rajdhani)
- Wheel rings, tooltips, bar tracks, analysis line all themed — auto-switches with Stalker/Jade/Ash

### Alchemy page — vanilla port
- Fully ported from React/Vite to vanilla HTML/CSS/JS — ~8KB vs 180KB bundle, no build step
- Custom stroke-only SVG icons for all 10 elements (placeholder; user plans custom graphics)
- Recharts removed; custom CSS gradient bars + animations

### Prime vaulting — Update 42
User refreshed wiki data via Playwright on Windows (new `weapons_data.lua` + `void_data.lua`).

**Newly released primes (auto from wiki):** Voruna, Perigale, Sarofang, Keres (4 items, 11 new relics)

**Newly vaulted primes:** Protea, Velox, Okina (3 items) — **manually flipped** because wiki `Module:Void/data` hadn't caught the vault yet. Script at session time walked all unvaulted relics and flipped `vaulted: true` on any containing a Protea/Velox/Okina part → 16 relics flipped.

**Important:** This is a temporary override. Next `parse_relic_data.py` run once wiki contributors update the module will either confirm or overwrite — same outcome.

Stats: 743 total relics, 708 vaulted, 35 unvaulted, 43 unique unvaulted Prime items.

### `GAME_DATA_VERSION` bumped
- `src/version.py:2` = `"Update 42 — The Shadowgrapher"` (was `"Update 41 — The Old Peace"`)
- Flows through `/api/version`, Guide modal footer, CLI `--version`

### Höllvania mojibake fix (`web/api.py`)
- Bug: live drops data showed "HÃ¶llvania" instead of "Höllvania"
- Root cause: `_fetch_drops()` uses `requests.Response.text` but CDN serves HTML without `charset` in `Content-Type` → falls back to ISO-8859-1
- Fix: set `r.encoding = "utf-8"` before reading `r.text`
- Disk `data/drops.json` was unaffected; only in-memory `_drops_cache` was corrupted
- To clear stale cache: restart server OR `POST /api/refresh-drops`

---

## Key Files Changed (prior sessions)
```
scripts/parse_worldstate.py         # +11 NW mappings, 169 NAMES / 167 DESCRIPTIONS
src/version.py                      # GAME_DATA_VERSION bump
web/api.py                          # Höllvania UTF-8 fix in _fetch_drops()
web/static/alchemy.html             # .panel classes, label removal, title rename
web/static/alchemy.css              # glassmorphism rewrite, var()-based theming
web/static/js/alchemy.js            # full rewrite: factions{} data + renderCards() for 2 panels
web/static/layout.css               # .page-wrap replaces .factions-wrap
data/relics.json                    # 16 relics manually vaulted (Protea/Velox/Okina)
data/weapons.json                   # refreshed to Update 42 (auto via parse_wiki_data.py)
data/mods.json                      # refreshed to Update 42
data/void_data.lua                  # refreshed
data/mods_data.lua                  # refreshed
data/nightwave_acts.json            # NEW — wiki-scraped NW reference (131 acts, not loaded at runtime)
```

---

## Pending / Known Issues
- **Element icons** — current SVGs are functional placeholders; user wants custom graphics (swap icon strings in `js/alchemy.js`)
- **Missing base element glyphs** — Cold, Electricity, Heat, Toxin PNGs not downloaded (run `fetch_images.py --category damage_types`)
- **Vaulted relic override is temporary** — will be auto-corrected on next wiki refresh once contributors update `Module:Void/data`
- **URL state / sharing** — not started
- **Sentinel stats** — companions_data.lua has stats but Reliquary sentinel classification doesn't map automatically
- **Mod images not yet wired into UI** — ready for mod picker redesign
- **Baro item names** — some guessed names may be wrong

---

## Nightwave Resolution Workflow (for new unresolved acts)
When the live page shows CamelCase act names like "Some New Act":

1. Get the list from the user (tier + CamelCase display)
2. Grep `data/nightwave_acts.json` for keywords from the CamelCase segments to find the real wiki display name + description
3. Add mappings to `scripts/parse_worldstate.py`:
   - `_NW_NAMES[CamelCaseKey] = "Wiki Display Name"`
   - `_NW_DESCRIPTIONS[CamelCaseKey] = "Wiki challenge text"`
4. For Elite-only variants that collide with weekly versions, use `_NW_ELITE_NAMES` / `_NW_ELITE_DESCRIPTIONS` overrides instead
5. Verify with `pw._nw_title('SeasonWeeklyCamelCaseKey', is_elite=False)` in a Python REPL
6. Run `pytest` (should stay at 304)
7. Commit + push

**To refresh `nightwave_acts.json` when DE rolls a whole new Nightwave season:** Ask Cowork/Playwright to re-scrape `wiki.warframe.com/w/Nightwave` into the same JSON format.

---

## Data Refresh Workflow (Update NN)
```bash
# On Windows (wiki blocks sandbox fetches):
python scripts/fetch_wiki_playwright.py              # downloads all .lua files

# Then parse (order matters for some):
python scripts/parse_lua.py                          # → weapons_raw.json, mods_raw.json
python scripts/parse_wiki_data.py                    # → weapons.json, mods.json, enemies.json
python scripts/parse_warframe_data.py                # → warframes.json
python scripts/parse_relic_data.py                   # → relics.json
python scripts/fix_galv_stats.py                     # re-patch Galvanized mods if touched
pytest                                                # verify 304 pass

# Then bump:
# src/version.py → GAME_DATA_VERSION = "Update NN — Name"
```

## Image Download Workflow
```bash
# On Windows:
python scripts/fetch_images.py                      # all categories
python scripts/fetch_images.py --category arcanes   # single
python scripts/fetch_images.py --resume             # skip existing
python scripts/fetch_mod_images.py --resume          # mods only
```

---

## Design Decisions Log
- Alchemy page: fully vanilla (HTML/CSS/JS) — React/Vite sub-app replaced, no build step
- Element icons: custom stroke-only SVGs in alchemy.js, user plans to make their own later
- Recharts removed — custom CSS bars with gradient fill + glowing tips
- Vanilla port identical visual output to React version with ~95% less bundle weight
- Alchemy multiplier cards: 2 faction cards (Strong Against/Resisted By) — not 4 health-type cards — per Update 36+
- Alchemy styling: glassmorphism via `.panel`, crimson accent, all vars from `base.css`
- Nightwave mapping: hardcoded dict in `parse_worldstate.py`, reference data in `data/nightwave_acts.json`
- Vaulted override workflow: manual flip in `relics.json` acceptable when wiki lags DE
- Factions page: fully deleted; `.page-wrap` is the shared dot-bg wrapper for all pages
- Reliquary images LEFT, stats RIGHT, no rotation
- Landscape phones: nav sidebar collapses to burger, header scrolls away
- `r.text` is unsafe for CDN HTML without charset — always set `r.encoding = 'utf-8'`
