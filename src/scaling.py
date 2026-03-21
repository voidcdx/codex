"""Enemy level scaling formulas.

Sourced from wiki.warframe.com/w/Enemy_Level_Scaling.
These formulas are community-derived from in-game testing and have not
been officially confirmed by Digital Extremes.
"""


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _health_f1(delta: float) -> float:
    """Below ΔLevel 70."""
    return 1.0 + 0.015 * delta ** 2


def _health_f2(delta: float, eximus: bool = False) -> float:
    """Above ΔLevel 80. Eximus units use a higher coefficient (~1.617×)."""
    coeff = 17.3542 if eximus else 10.7332
    return 1.0 + coeff * delta ** 0.72


def health_multiplier(delta: float, eximus: bool = False) -> float:
    """Health/shield multiplier for a given level difference from base."""
    if delta <= 0:
        return 1.0
    if delta <= 70:
        return _health_f1(delta)
    if delta >= 80:
        return _health_f2(delta, eximus)
    t = (delta - 70) / 10.0
    return _health_f1(delta) + (_health_f2(delta, eximus) - _health_f1(delta)) * _smoothstep(t)


def overguard_at_level(delta: float) -> float:
    """Overguard scales linearly with ΔLevel (not the health power law).
    Base overguard = 12. Coefficient backcalculated from wiki data."""
    if delta <= 0:
        return 12.0
    return 12.0 * (1.0 + 76.477 * delta)


def armor_at_level(base_armor: float, delta: float) -> float:
    """Scaled armor, hard-capped at 2700 per wiki."""
    if delta <= 0 or base_armor <= 0:
        return base_armor
    scaled = base_armor * (1.0 + 0.005 * delta ** 1.75)
    return min(2700.0, scaled)


def scale_enemy_stats(
    base_health: float,
    base_shield: float,
    base_armor: float,
    base_level: int,
    target_level: int,
    steel_path: bool = False,
    eximus: bool = False,
) -> dict:
    """Return scaled enemy stats for the given level + modifiers.

    Steel Path: +100 level, ×2.5 health and shields.
    Eximus: adds Overguard (base 12, level-scaled).
    """
    level = target_level
    health_mult = 1.0
    shield_mult = 1.0

    if steel_path:
        level += 100
        health_mult *= 2.5
        shield_mult *= 2.5

    delta = max(0, level - base_level)
    h_mult = health_multiplier(delta, eximus) * health_mult
    s_mult = health_multiplier(delta) * shield_mult
    armor = armor_at_level(base_armor, delta)
    health = base_health * h_mult
    shield = base_shield * s_mult
    overguard = overguard_at_level(delta) if eximus else 0.0

    return {
        "level":     level,
        "health":    health,
        "shield":    shield,
        "armor":     armor,
        "overguard": overguard,
    }
