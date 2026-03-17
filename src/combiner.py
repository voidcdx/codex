from src.enums import DamageType
from src.models import DamageComponent
from src.quantizer import quantize

# All six secondary element recipes
COMBINATION_TABLE: dict[frozenset, DamageType] = {
    frozenset({DamageType.HEAT,        DamageType.COLD}):        DamageType.BLAST,
    frozenset({DamageType.ELECTRICITY, DamageType.TOXIN}):       DamageType.CORROSIVE,
    frozenset({DamageType.HEAT,        DamageType.TOXIN}):       DamageType.GAS,
    frozenset({DamageType.COLD,        DamageType.ELECTRICITY}): DamageType.MAGNETIC,
    frozenset({DamageType.HEAT,        DamageType.ELECTRICITY}): DamageType.RADIATION,
    frozenset({DamageType.COLD,        DamageType.TOXIN}):       DamageType.VIRAL,
}

# Primary elements only
PRIMARY_ELEMENTS = {
    DamageType.HEAT,
    DamageType.COLD,
    DamageType.ELECTRICITY,
    DamageType.TOXIN,
}

# HCET priority order for Kuva/Tenet innate elements
HCET_ORDER = [
    DamageType.HEAT,
    DamageType.COLD,
    DamageType.ELECTRICITY,
    DamageType.TOXIN,
]


def combine_elements(
    mod_elements: list[DamageComponent],    # ordered by mod slot (left → right)
    innate_elements: list[DamageComponent],
    base_damage: float,
    is_kuva_tenet: bool = False,
) -> list[DamageComponent]:
    """Combine primary elements into secondary elements per mod-order priority.

    Only the first instance of a primary element determines its position in
    the combination queue. All instances contribute their amounts.

    Returns list of DamageComponents (secondaries + remaining primaries).
    """
    seen_set: set[DamageType] = set()
    unique_elements: list[DamageType] = []
    accumulated: dict[DamageType, float] = {}

    def _add(dtype: DamageType, amount: float) -> None:
        if dtype not in seen_set:
            seen_set.add(dtype)
            unique_elements.append(dtype)
        accumulated[dtype] = accumulated.get(dtype, 0.0) + amount

    for comp in mod_elements:
        if comp.type in PRIMARY_ELEMENTS:
            _add(comp.type, comp.amount)

    innate_primaries = [c for c in innate_elements if c.type in PRIMARY_ELEMENTS]
    if is_kuva_tenet and innate_primaries:
        innate_primaries.sort(key=lambda c: HCET_ORDER.index(c.type))
    for comp in innate_primaries:
        _add(comp.type, comp.amount)

    # Walk unique_elements i / i+1, combining adjacent pairs
    result: list[DamageComponent] = []
    i = 0
    while i < len(unique_elements):
        current = unique_elements[i]
        if i + 1 < len(unique_elements):
            nxt = unique_elements[i + 1]
            combo_key = frozenset({current, nxt})
            if combo_key in COMBINATION_TABLE:
                combined_amount = quantize(
                    accumulated[current] + accumulated[nxt], base_damage
                )
                result.append(DamageComponent(COMBINATION_TABLE[combo_key], combined_amount))
                i += 2
                continue
        q = quantize(accumulated[current], base_damage)
        if q != 0.0:
            result.append(DamageComponent(current, q))
        i += 1

    return result
