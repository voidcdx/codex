# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** v0.8.1. Full damage pipeline, web UI, live tracker, reliquary, alchemy page (vanilla).

**Branch:** `claude/continue-documentation-JrJt7`

---

## What Was Done This Session

### 1. CLAUDE.md cleanup
- Removed stale note about `web/alchemy/` React app ("still exists but is no longer served — can be deleted")

### 2. Deleted `web/alchemy/`
- Old React/Vite alchemy sub-app fully removed from disk (was untracked)
- Vanilla port at `web/static/alchemy.html` + `alchemy.css` + `js/alchemy.js` is the canonical page

### 3. HANDOFF.md reset for new session

---

## Prior Session Summary (for context)

- Alchemy page fully ported to vanilla HTML/CSS/JS — replaced React/Vite app; ~8KB vs 180KB bundle
- Custom stroke-only SVG icons for all 10 elements (placeholder; user plans custom graphics)
- Alchemy data rewritten to post-Update 36 faction-based multipliers (Grineer/Corpus/Infested/Sentient/etc.)
- Recharts removed; custom CSS gradient bars + animations
- Factions page deleted; `.factions-wrap` renamed to `.page-wrap` in `layout.css`

---

## Pending / Known Issues
- **Element icons** — current SVGs are functional placeholders; user wants to create custom graphics (swap icon strings in `js/alchemy.js`)
- **Missing base element glyphs** — Cold, Electricity, Heat, Toxin PNGs not downloaded (run `fetch_images.py --category damage_types`)
- **Alchemy page styling** — could use further refinement to match Void Codex design system
- **URL state / sharing** — not started
- **Sentinel stats** — companions_data.lua has stats but Reliquary sentinel classification doesn't map automatically
- **Mod images not yet wired into UI** — ready for mod picker redesign
- **Baro item names** — some guessed names may be wrong

---

## Image Download Workflow
```bash
# On Windows (wiki blocks automated fetch from sandbox):
python scripts/fetch_images.py                        # all categories
python scripts/fetch_images.py --category arcanes     # single category
python scripts/fetch_images.py --resume               # skip existing
python scripts/fetch_mod_images.py --resume            # mods only
```

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
- Alchemy page: fully vanilla (HTML/CSS/JS) — React/Vite sub-app replaced, no build step
- Element icons: custom stroke-only SVGs in alchemy.js, user plans to make their own later
- Recharts removed — custom CSS bars with gradient fill + glowing tips
- Vanilla port identical visual output to React version with ~95% less bundle weight
- Reliquary images on LEFT side, stats/info on RIGHT — no rotation
- Landscape phones: nav sidebar collapses to burger, header scrolls away
- Factions page fully deleted; `.factions-wrap` renamed to `.page-wrap` (shared wrapper in layout.css)
- Alchemy multiplier cards: 2 faction cards (Strong Against/Resisted By) using FACTION_META color-coded badges + animated bars + SVG glyphs per faction
