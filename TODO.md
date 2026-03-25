# TODO

## Done this session
- [x] Fix mod grid scroll on mobile — SortableJS `delay: 150` + `delayOnTouchOnly: true`
- [x] Tighten text field sizing — padding/font reduced across all inputs, mobile-safe (16px iOS preserved)
- [x] Rewrite weapon/enemy combobox — bare-bones, no portal, no ignoreBlur hack, scroll-safe
- [x] Fix dropdown z-index behind panels — `.panel.combobox-open` lifts stacking context
- [x] Fix dropdown collapsing on touch scroll — removed touchstart close listener
- [x] Search UX — clear input on focus, persist stats panel until new selection committed

## Done this session
- [x] Add Kill Time (TTK) calculator — Shots to Kill + Burst/Sustained TTK in results panel
- [x] Style the combobox dropdowns — accent border, box-shadow, subtle row separators
- [x] Condition Overload unique_statuses — confirmed fully wired (UI → API → calculator)

## Outstanding
- [ ] Implement Weapon Arcanes (Deadhead, Merciless, Cascadia Flare) — stack-based bonuses
- [ ] Add build saving and URL sharing — encode build state in URL params (deferred, needs research)
- [ ] Add mod optimizer — find highest-DPS mod combination for a target faction/enemy
- [ ] Add side-by-side weapon comparison — two builds, DPS/TTK columns next to each other
- [ ] Header / branding — needs mobile-first design (≤375px), no SVG wings
