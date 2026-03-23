"""Warframe ability buff presets.

Each preset is a factory function: (ability_strength: float) → Buff.
Ability strength is a multiplier (1.0 = 100%, 2.0 = 200%, etc.).

Pipeline placement per buff category:
  - faction_damage_bonus: Step 5 (additive with Bane), double-dips on procs (Roar)
  - damage_multiplier:    Step 5.5 (multiplicative), no double-dip (Eclipse, Vex Armor, Octavia)
  - sonar_multiplier:     Step 2 (multiplies body part) (Sonar)
  - elemental_type/bonus: Step 1 (adds elemental damage) (Xata's Whisper, Toxic Lash, Nourish)
  - crit_damage_bonus:    Pre-calc (Volt Shield — flat +2.0, not scaled by strength)
  - electricity_bonus:    Step 1 (adds Electricity) (Volt Shield)
  - fire_rate_bonus:      Pre-calc (Wisp Haste)
"""
from src.enums import DamageType
from src.models import Buff


def _roar(s: float) -> Buff:
    return Buff("Roar", faction_damage_bonus=0.50 * s)


def _eclipse(s: float) -> Buff:
    return Buff("Eclipse", damage_multiplier=2.00 * s)


def _vex_armor(s: float) -> Buff:
    return Buff("Vex Armor", damage_multiplier=2.75 * s)


def _octavia_amp(s: float) -> Buff:
    return Buff("Octavia Amp", damage_multiplier=0.30 * s)


def _sonar(s: float) -> Buff:
    return Buff("Sonar", sonar_multiplier=5.00 * s)


def _xatas_whisper(s: float) -> Buff:
    return Buff("Xata's Whisper", elemental_type=DamageType.VOID, elemental_bonus=0.26 * s)


def _toxic_lash(s: float) -> Buff:
    return Buff("Toxic Lash", elemental_type=DamageType.TOXIN, elemental_bonus=0.30 * s)


def _nourish(s: float) -> Buff:
    return Buff("Nourish", elemental_type=DamageType.VIRAL, elemental_bonus=0.30 * s)


def _volt_shield(s: float) -> Buff:
    # Electricity scales with strength; crit damage is flat +2.0 (does not scale)
    return Buff("Volt Shield", electricity_bonus=0.50 * s, crit_damage_bonus=2.0)


def _wisp_haste(s: float) -> Buff:
    return Buff("Wisp Haste", fire_rate_bonus=0.30 * s)


# Map of buff name → factory function
# Keys are lowercase for case-insensitive lookup
BUFF_PRESETS: dict[str, callable] = {
    "roar":           _roar,
    "eclipse":        _eclipse,
    "vex_armor":      _vex_armor,
    "octavia_amp":    _octavia_amp,
    "sonar":          _sonar,
    "xatas_whisper":  _xatas_whisper,
    "toxic_lash":     _toxic_lash,
    "nourish":        _nourish,
    "volt_shield":    _volt_shield,
    "wisp_haste":     _wisp_haste,
}

# Display names for UI
BUFF_DISPLAY_NAMES: dict[str, str] = {
    "roar":           "Roar (Rhino)",
    "eclipse":        "Eclipse (Mirage)",
    "vex_armor":      "Vex Armor (Chroma)",
    "octavia_amp":    "Amp (Octavia)",
    "sonar":          "Sonar (Banshee)",
    "xatas_whisper":  "Xata's Whisper (Xaku)",
    "toxic_lash":     "Toxic Lash (Saryn)",
    "nourish":        "Nourish (Grendel)",
    "volt_shield":    "Electric Shield (Volt)",
    "wisp_haste":     "Haste Mote (Wisp)",
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
