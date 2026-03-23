"""Warframe ability buff presets.

Each preset is a factory function: (ability_strength: float, subsumed: bool) → Buff.
Ability strength is a multiplier (1.0 = 100%, 2.0 = 200%, etc.).
Subsumed (Helminth) versions have reduced base values.

Pipeline placement per buff category:
  - faction_damage_bonus: Step 5 (additive with Bane), double-dips on procs (Roar)
  - damage_multiplier:    Step 5.5 (multiplicative), no double-dip (Eclipse)
  - elemental_type/bonus: Step 1 (adds elemental damage) (Xata's Whisper, Nourish)
"""
from src.enums import DamageType
from src.models import Buff

# Base values: (original, subsumed)
_ROAR_BASE = (0.50, 0.30)
_ECLIPSE_BASE = (2.00, 0.30)
_XATAS_WHISPER_BASE = (0.26, 0.26)  # Xata's Whisper is not reduced when subsumed
_NOURISH_BASE = (0.75, 0.45)


def _roar(s: float, subsumed: bool = False) -> Buff:
    base = _ROAR_BASE[1] if subsumed else _ROAR_BASE[0]
    return Buff("Roar", faction_damage_bonus=base * s)


def _eclipse(s: float, subsumed: bool = False) -> Buff:
    base = _ECLIPSE_BASE[1] if subsumed else _ECLIPSE_BASE[0]
    return Buff("Eclipse", damage_multiplier=base * s)


def _xatas_whisper(s: float, subsumed: bool = False) -> Buff:
    base = _XATAS_WHISPER_BASE[1] if subsumed else _XATAS_WHISPER_BASE[0]
    return Buff("Xata's Whisper", elemental_type=DamageType.VOID, elemental_bonus=base * s)


def _nourish(s: float, subsumed: bool = False) -> Buff:
    base = _NOURISH_BASE[1] if subsumed else _NOURISH_BASE[0]
    return Buff("Nourish", elemental_type=DamageType.VIRAL, elemental_bonus=base * s)


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


def make_buff(name: str, strength: float = 1.0, subsumed: bool = False) -> Buff:
    """Create a Buff from a preset name and ability strength multiplier.

    Args:
        name: Preset name (case-insensitive, e.g. "roar", "eclipse").
        strength: Ability strength as multiplier (1.0 = 100%).
        subsumed: If True, use reduced Helminth (subsumed) base values.

    Raises:
        KeyError: If the preset name is not found.
    """
    key = name.lower().replace(" ", "_").replace("'", "")
    factory = BUFF_PRESETS.get(key)
    if factory is None:
        valid = ", ".join(sorted(BUFF_PRESETS.keys()))
        raise KeyError(f"Unknown buff {name!r}. Valid: {valid}")
    return factory(strength, subsumed=subsumed)
