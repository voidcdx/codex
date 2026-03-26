from decimal import Decimal, ROUND_HALF_UP

from src.models import DamageComponent


def warframe_round(x: float | Decimal) -> int:
    """Round x to nearest integer using ROUND_HALF_UP (standard rounding).

    NEVER use Python's built-in round() — it uses Banker's Rounding
    (round-half-to-even), which gives wrong results on .5 boundaries.
    e.g. round(2.5) -> 2, but warframe_round(2.5) -> 3.
    """
    return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def quantize(amount: float, base_damage: float) -> float:
    """Round amount to the nearest multiple of base_damage/32 (1/32nd scale).

    Per wiki: scale = base_damage / 32
    quantized = warframe_round(amount / scale) * scale
    """
    if base_damage == 0.0:
        return 0.0
    scale = Decimal(str(base_damage)) / 32
    d_amount = Decimal(str(amount))
    steps = int((d_amount / scale).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    return float(steps * scale)


def quantize_cdm(cdm: float) -> float:
    """Quantize critical damage multiplier to Warframe's internal precision.

    Formula: Round(CDM × 4095/32) × 32/4095
    This snaps CDM to the nearest multiple of 32/4095 (~0.00781).
    """
    d_cdm = Decimal(str(cdm))
    factor = Decimal('4095') / Decimal('32')
    steps = int((d_cdm * factor).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    return float(Decimal(str(steps)) / factor)


def quantize_components(
    components: list[DamageComponent],
    base_damage: float,
) -> list[DamageComponent]:
    """Quantize each damage component independently.

    Components whose quantized value is 0 are dropped (they won't register
    in-game — e.g. a very small Impact value rounding to 0).
    """
    result: list[DamageComponent] = []
    for c in components:
        q = quantize(c.amount, base_damage)
        if q != 0.0:
            result.append(DamageComponent(c.type, q))
    return result
