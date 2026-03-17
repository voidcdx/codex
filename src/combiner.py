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

    Algorithm:
    1. Build ordered queue: mod elements first (left→right), then innate.
       - Kuva/Tenet innate: first primary sorted by HCET goes second-to-last.
    2. Walk the queue accumulating amounts per primary type.
       Whenever two primaries are present, combine the oldest pair.
    3. Combined element total is quantized at 1/32 of base_damage.
    4. Unconsumed primaries are also quantized and returned.

    Returns list of DamageComponents (secondaries + remaining primaries).
    """
    # Merge mod elements into accumulator (ordered list of (DamageType, float))
    # preserving first-seen order for combination priority
    ordered: list[tuple[DamageType, float]] = []
    accumulated: dict[DamageType, float] = {}

    def _add(dtype: DamageType, amount: float) -> None:
        if dtype not in accumulated:
            ordered.append((dtype, 0.0))
        accumulated[dtype] = accumulated.get(dtype, 0.0) + amount

    for comp in mod_elements:
        if comp.type in PRIMARY_ELEMENTS:
            _add(comp.type, comp.amount)

    # Sort innate elements for Kuva/Tenet weapons
    innate_primaries = [c for c in innate_elements if c.type in PRIMARY_ELEMENTS]
    if is_kuva_tenet and innate_primaries:
        innate_primaries.sort(key=lambda c: HCET_ORDER.index(c.type))
        # First by HCET order → second-to-last in queue; rest are last
        for comp in innate_primaries:
            _add(comp.type, comp.amount)
    else:
        for comp in innate_primaries:
            _add(comp.type, comp.amount)

    # Refresh ordered list with final amounts
    active: list[tuple[DamageType, float]] = [
        (dt, accumulated[dt]) for dt, _ in ordered if dt in accumulated
    ]

    result: list[DamageComponent] = []

    # Greedily combine pairs in order of appearance
    while True:
        # Find the first two distinct primaries
        seen: list[int] = []
        for i, (dt, _) in enumerate(active):
            if dt in PRIMARY_ELEMENTS:
                seen.append(i)
            if len(seen) == 2:
                break

        if len(seen) < 2:
            break

        i0, i1 = seen[0], seen[1]
        dt0, amt0 = active[i0]
        dt1, amt1 = active[i1]
        key = frozenset({dt0, dt1})

        if key not in COMBINATION_TABLE:
            # Not a valid combo — stop trying to combine these two
            break

        combined_type = COMBINATION_TABLE[key]
        combined_amount = quantize(amt0 + amt1, base_damage)
        result.append(DamageComponent(combined_type, combined_amount))

        # Remove the two consumed primaries
        active = [item for idx, item in enumerate(active) if idx not in (i0, i1)]

    # Remaining primaries
    for dt, amt in active:
        if dt in PRIMARY_ELEMENTS:
            q = quantize(amt, base_damage)
            if q != 0.0:
                result.append(DamageComponent(dt, q))

    return result
