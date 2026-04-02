# Handoff — Warframe Damage Calculator

## Current Status
**304 tests passing.** Full 6-step damage pipeline, web UI fully functional.

**Version:** `0.7.0`
**Branch:** `claude/continue-handoff-docs-PZ3r7`

---

## What Was Done This Session

### Reliquary Search — Full Rebuild
Scrapped the old two-piece (container + absolute overlay) design entirely.

**New approach: single expanding pill**
- `.search-pill` — `width: 28px → 220px` transition, `overflow: hidden` clips input while closed
- No absolute positioning, no border stitching, no sizing hacks
- Glass icon perfectly centered: 26px button in 28px pill (26px inner after 1px border each side)
- Input fades in via `opacity: 0 → 1`
- Clear button uses SVG × (not text character — text sits on baseline, SVG centers)
- `closePill()` vs `clearSearch()`: click-outside/Enter/toggle → `closePill()` (keeps query); × / Escape → `clearSearch()` (full reset)
- `closePill()` calls `searchInput.blur()` to dismiss mobile keyboard

### Vault Button — Full Rebuild
- SVG ring replaces CSS `border-radius: 50%` (CSS circles pixelate at 28px; SVG anti-aliases properly)
- `.vault-ring` inside the lock SVG — `stroke-opacity: 0` by default, shown on hover/active/vaulted via CSS
- Lock rendered at 16px (native viewBox size) to prevent sub-pixel blur
- States: default = dimmed no ring; unvaulted = accent2 + ring; vaulted = `#e53e3e` + ring; open = text + ring

### panels.css — Scoped Input Styles
`input[type=text]` global rule was bleeding into every page (adding border, background, padding, border-radius to all inputs).
- Changed `select, input[type=text], input[type=number]` → `.panel select, .panel input[type=text], .panel input[type=number]`
- Same for `:focus` rule
- Every page's inputs now use their own class-specific styles only

### iOS Safari — Toolbar Collapse + Safe Area Insets

**Root cause:** All pages had `body { overflow: hidden }` + inner div scroll (`overflow-y: auto` on `.content`, `.live-wrap`, `.factions-wrap`). iOS Safari only collapses toolbar on window-level scroll.

**Fix (mobile ≤900px only, desktop completely unchanged):**
- `viewport-fit=cover` on all 4 HTML meta viewport tags
- `html, body { height: auto; overflow: visible }` on mobile
- `.app { height: auto }`, `.main { overflow: visible; height: auto }`
- `.live-page-wrap { height: auto }`, `.live-page-wrap > .app { flex: none; height: auto }` — needed because live page has extra wrapper with `height: 100%` and higher-specificity `.app` rule
- All scroll containers (`.content`, `.live-wrap`, `.factions-wrap`) → `overflow-y: visible` on mobile
- Header NOT sticky — scrolls away with content (burger is `position: fixed`, always visible)
- `.sidebar { height: 100dvh }` + `padding-bottom: env(safe-area-inset-bottom)`
- `.sidebar-footer { padding-bottom: calc(14px + env(safe-area-inset-bottom)) }`
- `.burger-btn { top: calc(5px + env(safe-area-inset-top)) }`
- `.back-to-top { bottom: calc(16px + env(safe-area-inset-bottom)) }`
- Alchemy modal `max-height: 82vh → 82dvh`

**Static file caching:** Added `Cache-Control: no-store` middleware in `web/api.py` for all `/static/` responses. Without this, mobile browsers cache CSS indefinitely and changes never apply.

**Reliquary pagination:** `goToPage()` uses `window.scrollTo()` on mobile, `.factions-wrap.scrollTop` on desktop.

### Burger + Back-to-Top Button
- `burger-btn border-radius: 0 → 8px` (rounded to match pill controls)
- `.back-to-top` — fixed bottom-right, matches burger style, fades in after 200px scroll
- Listens to `window` scroll (Safari), `document` scroll (Chrome Android), and inner containers (`.main`, `.content`, `.live-wrap`, `.factions-wrap`) — covers all browsers
- Smooth scroll on click (`behavior: 'smooth'` only — no instant `scrollTop = 0` override)
- JS in `theme.js` (loaded on all 4 pages)
- HTML button added to all 4 pages (before `</div><!-- .app -->`)

---

## Key Files Changed This Session
```
web/static/reliquary.html        # search pill HTML, vault SVG ring, back-to-top button
web/static/reliquary.css         # search pill CSS, vault button CSS (SVG ring, states)
web/static/js/reliquary.js       # closePill/clearSearch split, setVault classes, goToPage scroll
web/static/panels.css            # input[type=text] scoped to .panel
web/static/layout.css            # burger radius, back-to-top CSS, mobile scroll refactor, safe area
web/static/base.css              # html/body mobile overflow override
web/static/live.css              # live-page-wrap mobile height override, live-wrap overflow
web/static/factions.css          # factions-wrap mobile overflow + safe area bottom
web/static/js/theme.js           # initBackToTop() — scroll listeners + smooth click
web/static/index.html            # viewport-fit=cover, back-to-top button
web/static/calculator.html       # viewport-fit=cover, back-to-top button
web/static/factions.html         # viewport-fit=cover, back-to-top button
web/api.py                       # Cache-Control: no-store middleware for /static/
```

---

## Pending / Known Issues
- **Drop location data** — not in `Module:Void/data`. Requires separate wiki module.
- **27 placeholder weapons** — fake IPS values in `data/weapons.json`.
- **URL state / sharing** — high-value missing feature (no work started).
- **Chrome mobile toolbar collapse** — iOS Safari collapses toolbar on window scroll. Chrome Android may not collapse its toolbar the same way (different browser behavior, not a bug we can fix).

---

## Mobile Architecture (≤900px)

```
window scrolls (body/html: overflow:visible, height:auto)
  └── .app (height:auto)
        └── .main (overflow:visible, height:auto)
              ├── .header (in-flow, scrolls away)
              └── .content / .live-wrap / .factions-wrap (overflow:visible)

position:fixed elements (always visible):
  .burger-btn    top-right, z-index:200
  .back-to-top   bottom-right, z-index:199
  .sidebar       full-height drawer, z-index:100
```

Desktop (>900px) is completely unchanged — inner div scroll as before.

---

## CSS File Map
```
web/static/base.css        # :root — all CSS variables; html/body rules; mobile overflow override
web/static/layout.css      # shared layout, header, sidebar, burger, back-to-top, mobile scroll refactor
web/static/panels.css      # .panel, input[type=text] scoped to .panel
web/static/reliquary.css   # all reliquary styles — search pill, vault button, tier seg, pagination
web/static/js/reliquary.js # filter state, search pill, vault toggle, renderGrid, pagination
web/static/js/theme.js     # theme switcher + initBackToTop() (loaded on ALL pages)
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
- Working branch: `claude/continue-handoff-docs-PZ3r7`
- User is on same branch locally — just `git pull origin claude/continue-handoff-docs-PZ3r7`
- `&&` not supported in Windows PowerShell — run git commands separately
