import math
from decimal import Decimal
from src.enums import DamageType, HealthType, ArmorType, FactionType
from src.models import Weapon, Mod, Enemy, DamageComponent
from src.quantizer import quantize, quantize_components
from src.combiner import combine_elements, PRIMARY_ELEMENTS

# ---------------------------------------------------------------------------
# Damage type effectiveness table (Update 36.0+: Vulnerable=1.5, Resistant=0.5)
# Key: (HealthType, DamageType) → multiplier; omitted entries are 1.0 (neutral)
# Source: wiki.warframe.com/w/Damage
# ---------------------------------------------------------------------------
EFFECTIVENESS: dict[tuple[HealthType, DamageType], float] = {
    # --- FLESH (Grineer/Corpus humanoids) ---
    (HealthType.FLESH, DamageType.SLASH):       1.5,
    (HealthType.FLESH, DamageType.TOXIN):       1.5,
    (HealthType.FLESH, DamageType.HEAT):        1.5,
    (HealthType.FLESH, DamageType.IMPACT):      0.5,
    (HealthType.FLESH, DamageType.GAS):         1.5,
    (HealthType.FLESH, DamageType.VIRAL):       1.5,

    # --- ROBOTIC ---
    (HealthType.ROBOTIC, DamageType.PUNCTURE):  1.5,
    (HealthType.ROBOTIC, DamageType.ELECTRICITY): 1.5,
    (HealthType.ROBOTIC, DamageType.RADIATION): 1.5,
    (HealthType.ROBOTIC, DamageType.SLASH):     0.5,
    (HealthType.ROBOTIC, DamageType.TOXIN):     0.5,

    # --- SHIELDS (Corpus) ---
    (HealthType.SHIELDS, DamageType.IMPACT):    1.5,
    (HealthType.SHIELDS, DamageType.MAGNETIC):  1.5,
    (HealthType.SHIELDS, DamageType.COLD):      1.5,
    (HealthType.SHIELDS, DamageType.TOXIN):     0.5,
    (HealthType.SHIELDS, DamageType.ELECTRICITY): 0.5,

    # --- PROTO_SHIELDS (Corpus elite) ---
    (HealthType.PROTO_SHIELDS, DamageType.PUNCTURE): 1.5,
    (HealthType.PROTO_SHIELDS, DamageType.CORROSIVE): 1.5,
    (HealthType.PROTO_SHIELDS, DamageType.IMPACT):   0.5,
    (HealthType.PROTO_SHIELDS, DamageType.COLD):     0.5,
    (HealthType.PROTO_SHIELDS, DamageType.MAGNETIC):  0.5,

    # --- FERRITE_ARMOR (Grineer) ---
    (HealthType.FERRITE_ARMOR, DamageType.PUNCTURE):  1.5,
    (HealthType.FERRITE_ARMOR, DamageType.CORROSIVE): 1.5,
    (HealthType.FERRITE_ARMOR, DamageType.BLAST):     0.5,
    (HealthType.FERRITE_ARMOR, DamageType.RADIATION): 0.5,

    # --- ALLOY_ARMOR (Corpus/Corrupted) ---
    (HealthType.ALLOY_ARMOR, DamageType.PUNCTURE):   1.5,
    (HealthType.ALLOY_ARMOR, DamageType.COLD):       1.5,
    (HealthType.ALLOY_ARMOR, DamageType.RADIATION):  1.5,
    (HealthType.ALLOY_ARMOR, DamageType.ELECTRICITY): 0.5,
    (HealthType.ALLOY_ARMOR, DamageType.MAGNETIC):   0.5,
    (HealthType.ALLOY_ARMOR, DamageType.BLAST):      0.5,

    # --- INFESTED_FLESH ---
    (HealthType.INFESTED_FLESH, DamageType.SLASH):   1.5,
    (HealthType.INFESTED_FLESH, DamageType.HEAT):    1.5,
    (HealthType.INFESTED_FLESH, DamageType.GAS):     1.5,
    (HealthType.INFESTED_FLESH, DamageType.COLD):    0.5,
    (HealthType.INFESTED_FLESH, DamageType.ELECTRICITY): 0.5,

    # --- FOSSILIZED (Infested heavy) ---
    (HealthType.FOSSILIZED, DamageType.BLAST):       1.5,
    (HealthType.FOSSILIZED, DamageType.CORROSIVE):   1.5,
    (HealthType.FOSSILIZED, DamageType.COLD):        0.5,
    (HealthType.FOSSILIZED, DamageType.TOXIN):       0.5,

    # --- SINEW (Infested runner) ---
    (HealthType.SINEW, DamageType.PUNCTURE):         1.5,
    (HealthType.SINEW, DamageType.RADIATION):        1.5,
    (HealthType.SINEW, DamageType.SLASH):            0.5,
    (HealthType.SINEW, DamageType.IMPACT):           0.5,
}


# ---------------------------------------------------------------------------
# Armor type modifiers: (ArmorType, DamageType) → (armor_mod, damage_mod)
# armor_mod: fraction of armor ignored (effective_armor = armor × (1 − armor_mod))
# damage_mod: additive damage bonus (e.g. 0.5 → ×1.5, -0.5 → ×0.5)
# Omitted entries: (0.0, 0.0) — no armor ignore, neutral damage
# ---------------------------------------------------------------------------
ARMOR_TYPE_MODIFIERS: dict[tuple[ArmorType, DamageType], tuple[float, float]] = {
    # Ferrite Armor (Grineer)
    (ArmorType.FERRITE, DamageType.PUNCTURE):  (0.5,  0.5),
    (ArmorType.FERRITE, DamageType.CORROSIVE): (0.75, 0.5),
    (ArmorType.FERRITE, DamageType.BLAST):     (0.0, -0.5),
    (ArmorType.FERRITE, DamageType.RADIATION): (0.0, -0.5),
    # Alloy Armor (Corpus/Corrupted)
    (ArmorType.ALLOY, DamageType.PUNCTURE):    (0.5,  0.5),
    (ArmorType.ALLOY, DamageType.COLD):        (0.0,  0.5),
    (ArmorType.ALLOY, DamageType.RADIATION):   (0.75, 0.5),
    (ArmorType.ALLOY, DamageType.ELECTRICITY): (0.0, -0.5),
    (ArmorType.ALLOY, DamageType.MAGNETIC):    (0.0, -0.5),
    (ArmorType.ALLOY, DamageType.BLAST):       (0.0, -0.5),
}


# ---------------------------------------------------------------------------
# Bane Mods (faction damage multipliers)
# Standard Bane mods: +30% at max rank
# Primed Bane mods:   +55% at max rank
# Formula (Step 3): Modded Damage × (1 + faction_bonus)
# ---------------------------------------------------------------------------
BANE_MODS: dict[str, Mod] = {
    # Standard
    "Bane of Grineer":   Mod("Bane of Grineer",   faction_bonus=0.30, faction_type=FactionType.GRINEER),
    "Bane of Corpus":    Mod("Bane of Corpus",     faction_bonus=0.30, faction_type=FactionType.CORPUS),
    "Bane of Infested":  Mod("Bane of Infested",   faction_bonus=0.30, faction_type=FactionType.INFESTED),
    "Bane of Corrupted": Mod("Bane of Corrupted",  faction_bonus=0.30, faction_type=FactionType.CORRUPTED),
    # Primed
    "Primed Bane of Grineer":   Mod("Primed Bane of Grineer",   faction_bonus=0.55, faction_type=FactionType.GRINEER),
    "Primed Bane of Corpus":    Mod("Primed Bane of Corpus",     faction_bonus=0.55, faction_type=FactionType.CORPUS),
    "Primed Bane of Infested":  Mod("Primed Bane of Infested",   faction_bonus=0.55, faction_type=FactionType.INFESTED),
    "Primed Bane of Corrupted": Mod("Primed Bane of Corrupted",  faction_bonus=0.55, faction_type=FactionType.CORRUPTED),
}


def crit_tier(total_cc: float) -> int:
    """Crit Tier T = floor(total_crit_chance).

    Args:
        total_cc: Crit chance as a decimal (1.65 = 165%). NOT a percentage.
    """
    return math.floor(total_cc)


def calculate_crit_multiplier(
    total_cc: float,
    modded_cm: float,
    mode: str = "average",
) -> float:
    """Critical hit damage multiplier.

    Args:
        total_cc:  Total crit chance as a decimal (e.g. 1.65 for 165%).
        modded_cm: Modded crit multiplier (e.g. 3.5 for 350%).
        mode:      "average"   — weighted average across all possible tiers (DPS use)
                   "guaranteed"— floor tier only, worst case per-hit
                   "max"       — ceiling tier, best case per-hit

    Formula: M_crit = 1 + T × (modded_cm − 1)
    Average is exact for all tiers: 1 + total_cc × (modded_cm − 1)
    """
    d_cc = Decimal(str(total_cc))
    d_cm = Decimal(str(modded_cm))
    if mode == "average":
        return float(Decimal('1') + d_cc * (d_cm - Decimal('1')))
    if mode == "guaranteed":
        T = Decimal(crit_tier(total_cc))
        return float(Decimal('1') + T * (d_cm - Decimal('1')))
    if mode == "max":
        T = Decimal(crit_tier(total_cc) + 1)
        return float(Decimal('1') + T * (d_cm - Decimal('1')))
    raise ValueError(f"Unknown mode {mode!r}. Use 'average', 'guaranteed', or 'max'.")


def calculate_armor_multiplier(
    armor: float,
    damage_type: DamageType,
    armor_type: ArmorType,
) -> float:
    """Damage fraction passing through armor, per-type.

    Applies type-specific armor ignore and damage bonus, then clamps to the
    2,700 armor cap before computing DR = armor / (armor + 300).
    Returns 1.0 when there is no armor.
    """
    if armor_type == ArmorType.NONE or armor == 0.0:
        return 1.0
    armor_mod, damage_mod = ARMOR_TYPE_MODIFIERS.get((armor_type, damage_type), (0.0, 0.0))
    d_armor = Decimal(str(armor))
    d_armor_mod = Decimal(str(armor_mod))
    d_damage_mod = Decimal(str(damage_mod))
    effective_armor = d_armor * (Decimal('1') - d_armor_mod)
    clamped_armor = max(Decimal('0'), min(Decimal('2700'), effective_armor))
    armor_multiplier = Decimal('1') - (clamped_armor / (clamped_armor + Decimal('300')))
    return float(armor_multiplier * (Decimal('1') + d_damage_mod))


class DamageCalculator:
    """Implements the 5-step Warframe damage pipeline.

    Step 1: Base Damage × (1 + ΣDamageMods)      → Modded Base   [math.floor]
    Step 2: Modded Base × Body Part Multiplier    → Part Damage   [warframe_round]
    Step 3: Part Damage × DamageType Multiplier   → Typed Dmg     [math.floor]
    Step 4: Typed Dmg × Armor Mitigation          → Mitigated Dmg [math.floor]
    Step 5: Mitigated Dmg × (1 + FactionMod)      → Final Dmg     [math.floor]

    Crit-on-headshot: if is_crit=True and body_part_multiplier > 1,
    the crit multiplier is doubled before applying to Step 2 output.
    """

    def calculate(
        self,
        weapon: Weapon,
        mods: list[Mod],      # ordered by slot position (slot 0 = top-left)
        enemy: Enemy,
        crit_multiplier: float = 1.0,   # pass calculate_crit_multiplier() result
        is_crit_headshot: bool = False,  # doubles crit multiplier on headshots
    ) -> dict[DamageType, float]:
        """Return final per-type damage values after the full pipeline."""
        base_damage = weapon.total_base_damage

        # --- Collect mod bonuses ---
        total_damage_bonus = sum(m.damage_bonus for m in mods)
        faction_bonus = sum(
            m.faction_bonus for m in mods
            if m.faction_type == enemy.faction
        )

        # Collect elemental mods in slot order
        mod_elements: list[DamageComponent] = []
        for m in mods:
            mod_elements.extend(m.elemental_bonuses)

        # --- Build elemental components ---
        # Scale elemental mod percentages by base_damage
        scaled_mod_elements = [
            DamageComponent(c.type, c.amount * base_damage)
            for c in mod_elements
            if c.type in PRIMARY_ELEMENTS
        ]

        # Split innate elements: primaries go into combiner, secondaries pass through
        # Innate element amounts are flat damage values, not percentages of base_damage
        scaled_innate_primary = [
            DamageComponent(c.type, c.amount)
            for c in weapon.innate_elements
            if c.type in PRIMARY_ELEMENTS
        ]
        innate_secondary = [
            DamageComponent(c.type, quantize(c.amount, base_damage))
            for c in weapon.innate_elements
            if c.type not in PRIMARY_ELEMENTS
        ]

        combined_elements = combine_elements(
            scaled_mod_elements,
            scaled_innate_primary,
            base_damage=base_damage,
            is_kuva_tenet=weapon.is_kuva_tenet,
        )

        elemental_components = combined_elements + [
            c for c in innate_secondary if c.amount != 0.0
        ]

        # --- Build full component list (IPS + elemental) ---
        ips_components = [
            DamageComponent(dt, amt)
            for dt, amt in weapon.base_damage.items()
        ]

        all_components = ips_components + elemental_components

        # --- Step 1: Apply damage mods → modded base, then quantize ---
        modded: list[DamageComponent] = []
        for comp in all_components:
            raw = math.floor(comp.amount * (1.0 + total_damage_bonus))
            q = quantize(float(raw), base_damage)
            if q != 0.0:
                modded.append(DamageComponent(comp.type, q))

        # --- Step 2: Body part multiplier × crit multiplier [warframe_round] ---
        effective_crit = crit_multiplier
        if is_crit_headshot and enemy.body_part_multiplier > 1.0:
            effective_crit = 1.0 + (crit_multiplier - 1.0) * 2.0
        combined_mult = enemy.body_part_multiplier * effective_crit
        from src.quantizer import warframe_round as _wr
        after_bodypart: list[DamageComponent] = [
            DamageComponent(c.type, _wr(c.amount * combined_mult))
            for c in modded
        ]

        # --- Step 3: Damage type effectiveness [math.floor] ---
        after_type: list[DamageComponent] = [
            DamageComponent(
                c.type,
                math.floor(c.amount * self._type_multiplier(c.type, enemy.health_type))
            )
            for c in after_bodypart
        ]

        # --- Step 4: Armor mitigation [math.floor] ---
        after_armor: dict[DamageType, float] = {}
        for c in after_type:
            if c.type in (DamageType.TRUE, DamageType.VOID):
                after_armor[c.type] = float(c.amount)
                continue
            mult = calculate_armor_multiplier(enemy.base_armor, c.type, enemy.armor_type)
            value = math.floor(c.amount * mult)
            if value > 0:
                after_armor[c.type] = float(value)

        # --- Step 5: Faction mod — applied last [math.floor] ---
        final: dict[DamageType, float] = {}
        for dtype, value in after_armor.items():
            final[dtype] = float(math.floor(value * (1.0 + faction_bonus)))

        return final

    # ------------------------------------------------------------------
    def _type_multiplier(self, dtype: DamageType, health: HealthType) -> float:
        return EFFECTIVENESS.get((health, dtype), 1.0)
