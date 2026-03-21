"""Enemy level scaling formulas.

Sourced from wiki.warframe.com/w/Enemy_Level_Scaling.
These formulas are community-derived from in-game testing and have not
been officially confirmed by Digital Extremes.
"""

from src.enums import FactionType

# Per-faction health coefficients: (f1_A, f1_exp, f2_A, f2_exp)
# f1(δ) = 1 + f1_A * δ^f1_exp   (δ < 70)
# f2(δ) = 1 + f2_A * δ^f2_exp   (δ > 80)
_HEALTH_COEFFS: dict[str, tuple[float, float, float, float]] = {
    "grineer":  (0.015,  2.12, 10.7332, 0.72),
    "corpus":   (0.015,  2.12, 13.4165, 0.55),
    "infested": (0.0225, 2.12, 16.1,    0.72),
    "corrupted":(0.015,  2.10, 10.7332, 0.685),
    "murmur":   (0.015,  2.0,  10.7332, 0.5),
    "techrot":  (0.02,   2.12, 15.1,    0.7),
}

# Per-faction shield coefficients: (f1_A, f1_exp, f2_A, f2_exp)
_SHIELD_COEFFS: dict[str, tuple[float, float, float, float]] = {
    "corpus":   (0.02, 1.76, 2.0, 0.76),
    "corrupted":(0.02, 1.75, 2.0, 0.75),
    "grineer":  (0.02, 1.75, 1.6, 0.75),  # also Sentient
    "techrot":  (0.02, 1.76, 3.5, 0.76),
}


def _faction_key(faction: FactionType) -> str:
    """Map FactionType → coefficient table key."""
    if faction in {FactionType.GRINEER, FactionType.KUVA_GRINEER, FactionType.SCALDRA}:
        return "grineer"
    if faction in {FactionType.CORPUS, FactionType.CORPUS_AMALGAM}:
        return "corpus"
    if faction in {FactionType.INFESTED, FactionType.DEIMOS_INFESTED}:
        return "infested"
    if faction == FactionType.CORRUPTED:
        return "corrupted"
    if faction == FactionType.TECHROT:
        return "techrot"
    # Sentient, Narmer, Murmur, Zariman, Unaffiliated/None
    return "murmur"


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _blend(f1: float, f2: float, delta: float, lo: float = 70.0, hi: float = 80.0) -> float:
    """Smoothstep blend between f1 and f2 over [lo, hi]."""
    if delta <= lo:
        return f1
    if delta >= hi:
        return f2
    t = (delta - lo) / (hi - lo)
    return f1 + (f2 - f1) * _smoothstep(t)


def health_multiplier(delta: float, faction: FactionType = FactionType.GRINEER) -> float:
    """Health multiplier for a given ΔLevel from base."""
    if delta <= 0:
        return 1.0
    A1, e1, A2, e2 = _HEALTH_COEFFS[_faction_key(faction)]
    f1 = 1.0 + A1 * delta ** e1
    f2 = 1.0 + A2 * delta ** e2
    return _blend(f1, f2, delta)


def shield_multiplier(delta: float, faction: FactionType = FactionType.GRINEER) -> float:
    """Shield multiplier for a given ΔLevel from base."""
    if delta <= 0:
        return 1.0
    key = _faction_key(faction)
    A1, e1, A2, e2 = _SHIELD_COEFFS.get(key, _SHIELD_COEFFS["grineer"])
    f1 = 1.0 + A1 * delta ** e1
    f2 = 1.0 + A2 * delta ** e2
    return _blend(f1, f2, delta)


def overguard_at_level(level: int) -> float:
    """Overguard for an Eximus unit at the given level.

    Base Overguard = 12. δ_OG = level − 1 (fixed base of 1, not enemy base level).
    Two-regime smoothstep blend over δ_OG 45–50.
    """
    BASE_OG = 12.0
    d = max(0.0, float(level) - 1.0)
    f1 = 1.0 + 0.0015 * d ** 4
    f2 = 1.0 + 260.0  * d ** 0.9
    return BASE_OG * _blend(f1, f2, d, lo=45.0, hi=50.0)


def armor_at_level(base_armor: float, delta: float) -> float:
    """Scaled armor, hard-capped at 2700 per wiki.

    Two-regime smoothstep (same 70–80 transition as health/shields).
    """
    if delta <= 0 or base_armor <= 0:
        return base_armor
    f1 = 1.0 + 0.005 * delta ** 1.75
    f2 = 1.0 + 0.4   * delta ** 0.75
    scaled = base_armor * _blend(f1, f2, delta)
    return min(2700.0, scaled)


def _eximus_health_floor(base_health: float, level: int, has_shield_or_armor: bool) -> float:
    """Piecewise Eximus base health floor (wiki 2.1 — Eximus section).

    Applied on top of faction health scaling: take max(faction_scaled, floor).
    Uses absolute level (not ΔLevel).
    """
    factor = 0.25 if has_shield_or_armor else 0.375
    pool = base_health + 900.0
    x = level
    if x <= 15:
        piecewise = 1.0
    elif x <= 25:
        piecewise = 1.0 + 0.025 * (x - 15)
    elif x <= 35:
        piecewise = 1.25 + 0.125 * (x - 25)
    elif x <= 50:
        piecewise = 2.5 + (2.0 / 15.0) * (x - 35)
    elif x <= 100:
        piecewise = 4.5 + 0.03 * (x - 50)
    else:
        piecewise = 6.0
    return max(base_health * 1.1, factor * pool * piecewise)


def scale_enemy_stats(
    base_health: float,
    base_shield: float,
    base_armor: float,
    base_level: int,
    target_level: int,
    steel_path: bool = False,
    eximus: bool = False,
    faction: FactionType = FactionType.GRINEER,
) -> dict:
    """Return scaled enemy stats for the given level + modifiers.

    Steel Path: +100 level, ×2.5 health and shields.
    Eximus: Overguard (base 12, level-scaled) + Eximus health floor.
    """
    level = target_level
    sp_mult = 1.0

    if steel_path:
        level += 100
        sp_mult = 2.5

    delta = max(0, level - base_level)

    health = base_health * health_multiplier(delta, faction) * sp_mult
    shield = base_shield * shield_multiplier(delta, faction) * sp_mult
    armor  = armor_at_level(base_armor, delta)

    if eximus:
        has_shield_or_armor = base_shield > 0 or base_armor > 0
        floor = _eximus_health_floor(base_health, level, has_shield_or_armor)
        health = max(health, floor * sp_mult)
        overguard = overguard_at_level(level)
    else:
        overguard = 0.0

    return {
        "level":     level,
        "health":    health,
        "shield":    shield,
        "armor":     armor,
        "overguard": overguard,
    }
