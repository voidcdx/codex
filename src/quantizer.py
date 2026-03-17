from src.models import DamageComponent


def quantize(amount: float, base_damage: float) -> float:
    """Round amount to the nearest multiple of base_damage/32 (1/32nd scale).

    Per wiki: scale = base_damage / 32
    quantized = round(amount / scale) * scale
    """
    if base_damage == 0.0:
        return 0.0
    scale = base_damage / 32.0
    return round(amount / scale) * scale


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
