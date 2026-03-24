# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

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
