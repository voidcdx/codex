"""Warframe ability buff presets.

Each preset is a factory function: (ability_strength: float) → Buff.
Ability strength is a multiplier (1.0 = 100%, 2.0 = 200%, etc.).

Pipeline placement per buff category:
  - faction_damage_bonus: Step 5 (additive with Bane), double-dips on procs (Roar)
  - damage_multiplier:    Step 5.5 (multiplicative), no double-dip (Eclipse)
  - elemental_type/bonus: Step 1 (adds elemental damage) (Xata's Whisper, Nourish)
"""
from src.enums import DamageType
from src.models import Buff


def _roar(s: float) -> Buff:
    return Buff("Roar", faction_damage_bonus=0.50 * s)


def _eclipse(s: float) -> Buff:
    return Buff("Eclipse", damage_multiplier=2.00 * s)


def _xatas_whisper(s: float) -> Buff:
    return Buff("Xata's Whisper", elemental_type=DamageType.VOID, elemental_bonus=0.26 * s)


def _nourish(s: float) -> Buff:
    return Buff("Nourish", elemental_type=DamageType.VIRAL, elemental_bonus=0.75 * s)


# Map of buff name → factory function
# Keys are lowercase for case-insensitive lookup
BUFF_PRESETS: dict[str, callable] = {
    "roar":           _roar,
    "eclipse":        _eclipse,
    "xatas_whisper":  _xatas_whisper,
    "nourish":        _nourish,
}

# Display names for UI
BUFF_DISPLAY_NAMES: dict[str, str] = {
    "roar":           "Roar (Rhino)",
    "eclipse":        "Eclipse (Mirage)",
    "xatas_whisper":  "Xata's Whisper (Xaku)",
    "nourish":        "Nourish (Grendel)",
}


def make_buff(name: str, strength: float = 1.0) -> Buff:
    """Create a Buff from a preset name and ability strength multiplier.

    Args:
        name: Preset name (case-insensitive, e.g. "roar", "eclipse").
        strength: Ability strength as multiplier (1.0 = 100%).

    Raises:
        KeyError: If the preset name is not found.
    """
    key = name.lower().replace(" ", "_").replace("'", "")
    factory = BUFF_PRESETS.get(key)
    if factory is None:
        valid = ", ".join(sorted(BUFF_PRESETS.keys()))
        raise KeyError(f"Unknown buff {name!r}. Valid: {valid}")
    return factory(strength)
