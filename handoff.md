# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/continue-previous-work-V8gSh`

---

## What Was Done This Session

### Reliquary Controls Redesign

#### Search Glass Icon — Centered
- Root cause: `.search-toggle-btn` had no `padding: 0` (UA browser default padding shifted flex content)
- Added `padding: 0` to reset UA padding
- Changed `height: 30px` → `height: 100%` on button, then reverted to explicit `height: 30px` + `width: 30px` after further issues
- SVG lock icon paths shifted up 2px to center visually in viewBox

#### Search Pill — Absolute Overlay (No Layout Shift)
- `.search-input-wrap` changed from in-flow (caused tier pills to shift) to `position: absolute`
- Container `.relic-search-expand` now `overflow: visible` so input wrap can extend beyond it
- Container given explicit `width: 30px; height: 30px` (border-box) for perfect circle
- When open: `border-right: none; border-radius: 20px 0 0 20px`
- Input wrap: `left: 29px; top: -1px; height: 30px; max-width: 0→210px; opacity: 0→1`
- `border: 1px solid var(--border-highlight); border-left: none` always (constant, no box-model shift)
- `max-width: 0 + overflow: hidden` for closed clipping (no 1px artifact)
- `opacity: 0/1` transition (avoids jerk from toggling border)

#### UNRESOLVED — Search Glass Off-Center After Absolute Overlay Change
- User reports the glass icon is still off-center after the `width: 30px; height: 30px` restore
- Root issue: `.relic-search-expand` has `width: 30px; height: 30px` border-box → inner content = 28×28px
- Button is `width: 30px; height: 30px` — overflows the 28px content area by 1px each side
- With `overflow: visible`, this overflow is transparent and invisible
- But the container now has explicit `width: 30px` AND `border: 1px` — making inner = 28px
- The button at 30px overflows the container → the centering may appear off due to sub-pixel rendering differences
- **Next session should investigate**: is the icon actually off-center, or is it the container border-radius making it *look* off? Try: `overflow: hidden` on the container with a wrapper div providing the absolute containing block for the input wrap. Or: move the border from the container to the button itself.

#### Vault Filter — Circle Button + Pill Dropdown
- Replaced `All/Unvaulted/Vaulted` segmented control with a 28px circle lock-icon button
- Click opens a pill dropdown (position: absolute, z-index: 100) with All/Unvaulted/Vaulted
- Dropdown uses `max-height + opacity` transition for expand-down animation
- Lock icon accents with `var(--accent2)` when filter is not "all"
- Click-outside closes dropdown
- Lock SVG paths adjusted to center visually in viewBox

#### Search Input Text Alignment (RESOLVED from last session)
- `.search-input-wrap`: `height: 30px` → `height: 100%`
- `.relic-search-expand input.relic-search-input`: added `margin-bottom: 0` to kill global 8px from `panels.css`

---

## Search CSS — Current State (`web/static/reliquary.css`)

```css
.relic-search-expand {
  display: flex; align-items: center; position: relative;
  flex-shrink: 0; width: 30px; height: 30px;
  border: 1px solid var(--border); border-radius: 20px;
  overflow: visible;
  transition: border-color 0.15s, border-radius 0.1s;
}
.relic-search-expand.open {
  border-color: var(--border-highlight);
  border-right: none;
  border-radius: 20px 0 0 20px;
}

.search-toggle-btn {
  width: 30px; height: 30px; padding: 0;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none;
  /* overflows container inner (28px) by 1px each side — transparent, invisible */
}

.search-input-wrap {
  position: absolute; left: 29px; top: -1px; height: 30px;
  max-width: 0; overflow: hidden; opacity: 0;
  border: 1px solid var(--border-highlight); border-left: none;
  border-radius: 0 20px 20px 0;
  background: var(--dropdown-bg); z-index: 5;
  transition: max-width 0.25s ease, opacity 0.15s ease;
}
.relic-search-expand.open .search-input-wrap {
  max-width: 210px; opacity: 1;
}
```

---

## Vault Dropdown CSS — Current State

```css
.vault-drop-wrap { position: relative; margin-left: auto; flex-shrink: 0; }
.vault-drop-btn { 28px × 28px circle; box-sizing: border-box; border: 1px solid var(--border); border-radius: 50%; }
.vault-drop-menu { position: absolute; top: calc(100%+6px); right: 0; display: flex; max-height: 0→40px; opacity: 0→1; }
```

---

## Pending / Known Issues
- **Search glass off-center** — unresolved. Container is 30px border-box (28px inner), button is 30px (overflows). Sub-pixel rendering may cause visual off-centering. Consider: move border to button directly (remove from container), use `overflow: hidden` with a separate absolute-positioning wrapper outside the container.
- **Drop location data** — not in `Module:Void/data`. Requires separate wiki module.
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **URL state / sharing** — high-value missing feature (no work started).

---

## Key Files Changed This Session
```
web/static/reliquary.css       # search pill, vault dropdown, input wrap
web/static/reliquary.html      # vault circle button + lock SVG; search HTML unchanged
web/static/js/reliquary.js     # setVault(), vault toggle + click-outside handler
```

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables; * { box-sizing: border-box; margin: 0; padding: 0; }
web/static/layout.css      # shared dot bg on .content/.live-wrap/.factions-wrap
web/static/panels.css      # .panel, global input[type=text] (margin-bottom:8px — override where needed)
web/static/reliquary.css   # all reliquary styles — controls, search, vault dropdown, tier seg, pagination
web/static/js/reliquary.js # filter state, search toggle, vault toggle, renderGrid, renderPagination
```

---

## Current State — Themes
```
stalker  (default, no class)   bg: #0a0a0a   surface: #121212   accent: #8b0000 → #e53e3e
jade     body.theme-jade        bg: #080808   surface: rgba(10,18,16,0.85)   accent: #00897b → #00e5c8
ash      body.theme-ash         bg: #080808   surface: rgba(16,16,16,0.85)   accent: #466482 → #7393b3
```

---

## Git Notes
- Working branch: `claude/continue-previous-work-V8gSh`
- User is on same branch locally — just `git pull origin claude/continue-previous-work-V8gSh`
- `&&` not supported in Windows PowerShell — run git commands separately
