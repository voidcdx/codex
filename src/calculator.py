import math
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


class DamageCalculator:
    """Implements the 5-step Warframe damage pipeline.

    Step 1: Base Damage × (1 + ΣDamageMods)      → Modded Base   [math.floor]
    Step 2: Modded Base × Body Part Multiplier    → Part Damage   [round]
    Step 3: Part Damage × (1 + FactionMod)        → Faction Dmg   [math.floor]
    Step 4: Faction Dmg × DamageType Multiplier   → Typed Dmg     [math.floor]
    Step 5: Typed Dmg × Armor Mitigation          → Final Dmg     [math.floor]
    """

    def calculate(
        self,
        weapon: Weapon,
        mods: list[Mod],      # ordered by slot position (slot 0 = top-left)
        enemy: Enemy,
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
        scaled_innate_primary = [
            DamageComponent(c.type, c.amount * base_damage)
            for c in weapon.innate_elements
            if c.type in PRIMARY_ELEMENTS
        ]
        innate_secondary = [
            DamageComponent(c.type, quantize(c.amount * base_damage, base_damage))
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

        # --- Step 2: Body part multiplier [round to nearest] ---
        after_bodypart: list[DamageComponent] = [
            DamageComponent(c.type, round(c.amount * enemy.body_part_multiplier))
            for c in modded
        ]

        # --- Step 3: Faction multiplier [math.floor] ---
        after_faction: list[DamageComponent] = [
            DamageComponent(c.type, math.floor(c.amount * (1.0 + faction_bonus)))
            for c in after_bodypart
        ]

        # --- Step 4: Damage type effectiveness [math.floor] ---
        after_type: list[DamageComponent] = [
            DamageComponent(
                c.type,
                math.floor(c.amount * self._type_multiplier(c.type, enemy.health_type))
            )
            for c in after_faction
        ]

        # --- Step 5: Armor mitigation [math.floor] ---
        armor_mult = self._armor_mitigation(enemy)
        final: dict[DamageType, float] = {}
        for c in after_type:
            effective = self._armor_effectiveness(c.type, enemy.armor_type)
            if effective:
                value = math.floor(c.amount * armor_mult)
            else:
                value = c.amount
            if value > 0:
                final[c.type] = float(value)

        return final

    # ------------------------------------------------------------------
    def _type_multiplier(self, dtype: DamageType, health: HealthType) -> float:
        return EFFECTIVENESS.get((health, dtype), 1.0)

    def _armor_mitigation(self, enemy: Enemy) -> float:
        """300 / (300 + effective_armor). Returns 1.0 when no armor."""
        if enemy.base_armor == 0.0 or enemy.armor_type == ArmorType.NONE:
            return 1.0
        return 300.0 / (300.0 + enemy.base_armor)

    def _armor_effectiveness(self, dtype: DamageType, armor: ArmorType) -> bool:
        """True if this damage type is mitigated by the given armor type.

        TRUE and VOID damage bypass armor entirely.
        """
        if armor == ArmorType.NONE:
            return False
        if dtype in (DamageType.TRUE, DamageType.VOID):
            return False
        return True
