"""Weapon arcane presets.

Each preset is a factory function: (stacks: int) → WeaponArcane.
Stacks are clamped to the arcane's max_stacks. Bonuses are pre-multiplied
by the clamped stack count so the calculator can consume them directly.

Damage bonuses are additive with Serration/Hornet Strike in Step 1.
Headshot bonuses (Deadhead) add to body_part_multiplier in Step 2.
CC/CD bonuses are pre-computed in api.py (same pattern as galvanized).
"""
from src.models import WeaponArcane


# --- Factory functions ---

def _primary_merciless(stacks: int) -> WeaponArcane:
    s = min(stacks, 12)
    return WeaponArcane("Primary Merciless", damage_bonus=0.30 * s, reload_bonus=0.075 * s, max_stacks=12, stacks=s)


def _secondary_merciless(stacks: int) -> WeaponArcane:
    s = min(stacks, 12)
    return WeaponArcane("Secondary Merciless", damage_bonus=0.30 * s, reload_bonus=0.075 * s, max_stacks=12, stacks=s)


def _shotgun_merciless(stacks: int) -> WeaponArcane:
    s = min(stacks, 12)
    return WeaponArcane("Shotgun Merciless", damage_bonus=0.30 * s, reload_bonus=0.075 * s, max_stacks=12, stacks=s)


def _primary_deadhead(stacks: int) -> WeaponArcane:
    s = min(stacks, 6)
    return WeaponArcane("Primary Deadhead", damage_bonus=0.60 * s, headshot_bonus=0.30 * s, max_stacks=6, stacks=s)


def _secondary_deadhead(stacks: int) -> WeaponArcane:
    s = min(stacks, 6)
    return WeaponArcane("Secondary Deadhead", damage_bonus=0.60 * s, headshot_bonus=0.30 * s, max_stacks=6, stacks=s)


def _shotgun_deadhead(stacks: int) -> WeaponArcane:
    s = min(stacks, 6)
    return WeaponArcane("Shotgun Deadhead", damage_bonus=0.60 * s, headshot_bonus=0.30 * s, max_stacks=6, stacks=s)


def _primary_dexterity(stacks: int) -> WeaponArcane:
    s = min(stacks, 6)
    return WeaponArcane("Primary Dexterity", damage_bonus=0.60 * s, max_stacks=6, stacks=s)


def _secondary_dexterity(stacks: int) -> WeaponArcane:
    s = min(stacks, 6)
    return WeaponArcane("Secondary Dexterity", damage_bonus=0.60 * s, max_stacks=6, stacks=s)


def _cascadia_flare(stacks: int) -> WeaponArcane:
    s = min(stacks, 12)
    return WeaponArcane("Cascadia Flare", cc_bonus=0.24 * s, max_stacks=12, stacks=s)


def _cascadia_empowered(stacks: int) -> WeaponArcane:
    s = min(stacks, 5)
    return WeaponArcane("Cascadia Empowered", cd_bonus=0.30 * s, max_stacks=5, stacks=s)


def _cascadia_overcharge(stacks: int) -> WeaponArcane:
    s = min(stacks, 1)
    return WeaponArcane("Cascadia Overcharge", flat_damage=4000.0 * s, max_stacks=1, stacks=s)


# --- Preset registries ---

ARCANE_PRESETS: dict[str, callable] = {
    "primary_merciless":   _primary_merciless,
    "secondary_merciless": _secondary_merciless,
    "shotgun_merciless":   _shotgun_merciless,
    "primary_deadhead":    _primary_deadhead,
    "secondary_deadhead":  _secondary_deadhead,
    "shotgun_deadhead":    _shotgun_deadhead,
    "primary_dexterity":   _primary_dexterity,
    "secondary_dexterity": _secondary_dexterity,
    "cascadia_flare":      _cascadia_flare,
    "cascadia_empowered":  _cascadia_empowered,
    "cascadia_overcharge": _cascadia_overcharge,
}

ARCANE_DISPLAY_NAMES: dict[str, str] = {
    "primary_merciless":   "Primary Merciless",
    "secondary_merciless": "Secondary Merciless",
    "shotgun_merciless":   "Shotgun Merciless",
    "primary_deadhead":    "Primary Deadhead",
    "secondary_deadhead":  "Secondary Deadhead",
    "shotgun_deadhead":    "Shotgun Deadhead",
    "primary_dexterity":   "Primary Dexterity",
    "secondary_dexterity": "Secondary Dexterity",
    "cascadia_flare":      "Cascadia Flare",
    "cascadia_empowered":  "Cascadia Empowered",
    "cascadia_overcharge": "Cascadia Overcharge",
}

ARCANE_RESTRICTIONS: dict[str, str] = {
    "primary_merciless":   "primary",
    "secondary_merciless": "secondary",
    "shotgun_merciless":   "shotgun",
    "primary_deadhead":    "primary",
    "secondary_deadhead":  "secondary",
    "shotgun_deadhead":    "shotgun",
    "primary_dexterity":   "primary",
    "secondary_dexterity": "secondary",
    "cascadia_flare":      "secondary",
    "cascadia_empowered":  "secondary",
    "cascadia_overcharge": "secondary",
}

ARCANE_MAX_STACKS: dict[str, int] = {
    "primary_merciless": 12, "secondary_merciless": 12, "shotgun_merciless": 12,
    "primary_deadhead": 6, "secondary_deadhead": 6, "shotgun_deadhead": 6,
    "primary_dexterity": 6, "secondary_dexterity": 6,
    "cascadia_flare": 12, "cascadia_empowered": 5, "cascadia_overcharge": 1,
}


def make_arcane(name: str, stacks: int = 0) -> WeaponArcane:
    """Create a WeaponArcane from a preset name and stack count.

    Args:
        name: Preset name (case-insensitive, e.g. "primary_merciless").
        stacks: Current active stacks (clamped to arcane's max).

    Raises:
        KeyError: If the preset name is not found.
    """
    key = name.lower().replace(" ", "_").replace("'", "")
    factory = ARCANE_PRESETS.get(key)
    if factory is None:
        valid = ", ".join(sorted(ARCANE_PRESETS.keys()))
        raise KeyError(f"Unknown arcane {name!r}. Valid: {valid}")
    return factory(max(0, stacks))
