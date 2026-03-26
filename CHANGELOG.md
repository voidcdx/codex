# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased] — 2026-03-26

### Changed
- Panel surfaces made semi-transparent (`rgba(18,10,10,0.50)`) with local crimson radial glow (`::after` pseudo-element) — glassmorphism-style blur visible without a page-wide background
- Fluid typography — body font now `clamp(13px, 1.1vw, 16px)`; all text sizes converted to `rem` so they scale proportionally with viewport width
- Mods panel moved under Weapon/Enemy panel in the main column (left side)
- Options panel collapsed by default
- Help panel text raised to `var(--text)` (#a0a0a0) from `var(--text-dim)` (#666666) — significantly easier to read
- Tooltip bubbles restyled to crimson theme — dark crimson-black background, `--border-red` border, `var(--text-primary)` text

### Fixed
- Armor Strip panel labels (Ability Strip %, Corrosive Projection %) were hardcoded 10px — now `0.67rem`
- Mobile horizontal scroll caused by `panel::after` extending 24px past edges — fixed with `overflow-x: hidden` on `html`
- Combobox/mod-picker dropdowns had green tint (`rgba(5,9,4)`) — corrected to `rgba(5,5,5)`

## [0.5.3] — 2026-03-26

### Added
- Armor Strip panel — models ability strip %, Corrosive Projection aura %, and Shattering Impact flat removal; shows remaining armor and DR% live; feeds into damage calculation
- Panel help (?) buttons on all panels and sub-sections — click to expand inline explanation of mechanics; crimson, borderless, mobile-friendly
- CDM quantization — critical damage multiplier now snapped to Warframe's internal precision grid (`Round(CDM × 4095/32) × 32/4095`)
- Faction Weakness Cheatsheet (`/factions`) — new page with matrix and cards views; shows ×1.5/×0.5 effectiveness for all 13 factions across 13 damage types; search + filter pills; matrix auto-switches to cards on mobile

### Fixed
- Attack mode tabs restyled — gradient underline + neon text-shadow glow replaces box border

## [0.5.2] — 2026-03-26

### Fixed
- Hit Type / Body Part / Bonus Element dropdowns now match the rest of the UI (themed, cross-platform — no more iOS picker)
- Stack inputs (Viral, Corrosive, Cold) clamped to 0–10 via oninput

## [0.5.1] — 2026-03-26

### Fixed
- Mod family exclusivity — Primed/Umbral/Archon variants no longer stack with base version in mod picker or Alchemy Mixer
- Crit chance formula corrected to multiplicative (`base × (1 + mods)`, was additive)
- Blood Rush now scales with combo tiers (contributed 0 at ×1, not flat +40%)
- Multishot result floored to integer per in-game behaviour
- Torid attack stats corrected (all 3 attacks); Mutalist Quanta and Synoid Simulor crit multipliers fixed

### Added
- Cold proc stacks (+0.1 flat CDM each, max 10) in Hit Options
- Weapon data validation script (`scripts/validate_weapons.py`)

## [0.5.0] — 2026-03-25

### Changed
- Major UI layout overhaul — merged Weapon+Enemy into single side-by-side panel with glowing crimson divider, merged Hit Options+Buffs, merged Arcanes into Mods panel
- Options panel moved to right column (collapsible, below Results), Calculate button repositioned below Options
- Builds panel hidden; content grid simplified to 2-column layout
- Sidebar and left panel widened; right column expanded for better results display
- Removed Guide and Changelog buttons from header (accessible via sidebar nav)
- Sidebar footer updated with copyright and data source attribution
- Full layout centered at 1440px max-width
- Sharp edges throughout (border-radius: 0 everywhere except circles)
- Scrollbars hidden globally while preserving scroll functionality
- Scan-line overlay removed
- All hardcoded inline styles extracted to CSS classes (.input-sm, .btn-add, .bonus-element-*, .enemy-level-col, etc.)
- Guide modal content styles moved to CSS (.guide-ol, .guide-em, .badge-vuln, .badge-res, .code-riven)
- We-grid divider uses gradient bright-in-middle line matching panel top-border style
- Panel sub-section headings use .panel-sub-h class

## [0.4.2] — 2026-03-25

### Changed
- Design tweaks — modal theme consistency, CSS variable cleanup, mobile viewport fix

## [0.4.1] — 2026-03-25

### Changed
- Calculator page redesigned to match Stalker/Shadow Acolyte theme — dark crimson palette, Orbitron/Rajdhani fonts, glass panels with crimson glow, right sidebar with brand icon and nav
- UI optimizations — layout, panel structure, and stylesheet organization

## [0.4.0] — 2026-03-25

### Changed
- Full graphical redesign of the Web UI

## [0.3.1] — 2026-03-24

### Added
- Condition Overload scaling curve in calculation results — shows damage at 0–10 unique statuses with bar chart and % increase

## [0.3.0] — 2026-03-24

### Added
- Weapon Arcane support — 11 arcane presets (Merciless, Deadhead, Dexterity, Cascadia variants) with per-arcane stack counts, weapon slot filtering, and full damage pipeline integration
- Arcane panel in Web UI with dropdown filtered by weapon type, stacks input, and max 2 slots
- `--arcane NAME:STACKS` CLI flag (repeatable, max 2)
- `GET /api/arcanes` endpoint returning available presets with display names, max stacks, and restrictions
- `arcanes` field on `/api/calculate` and `/api/modded-weapon` POST endpoints
- Cascadia Overcharge flat damage distributed proportionally among IPS types
- Deadhead headshot multiplier bonus applied additively in Step 2
- Modded reload time in `/api/calculate` response (accounts for Merciless reload bonus)
- 19 new tests covering arcane factories, stack clamping, pipeline integration, and proc calculations

## [0.2.2] — 2026-03-24

### Improved
- Visual cleanup and mobile fixes

## [0.2.1] — 2026-03-23

### Improved
- Web interface JavaScript reorganised into separate, focused modules for improved maintainability and long-term reliability

## [0.2.0] — 2026-03-23

### Added
- Redesigned Alchemy Guide with a glassmorphism modal, detailed mod rows with stat pills, and an equip/unequip toggle
- Element effect data now included in the mods API for richer mod information display

### Improved
- Alchemy Guide responsiveness: mobile centering, scroll containment, and a dedicated "Clear Mods" action
- Gas element colour updated to teal for improved visual clarity

### Fixed
- Text overflow in the damage breakdown table on narrow screens

## [0.1.0] — Initial Release

### Added
- Full damage calculation pipeline with quantization, critical hits, armor mitigation, faction modifiers, and Viral stack scaling
- Elemental combination system respecting mod slot order
- Status proc modeling: damage-over-time and crowd-control/debuff effects
- Multi-attack weapon support with per-attack stat selection
- Galvanized mod stack scaling
- Warframe ability buff integration (Roar, Eclipse, Xata's Whisper, Nourish)
- Per-faction enemy level scaling for health, shields, armor, and overguard
- Web interface, command-line tool, and API backend
- Launch dataset: 588 weapons, 1,405 mods, 983 enemies
