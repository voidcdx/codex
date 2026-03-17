"""M4-M6 — COMBINATION_TABLE lookup and combine_elements() tests."""
import pytest
from src.combiner import COMBINATION_TABLE, combine_elements
from src.models import DamageComponent
from src.enums import DamageType


class TestCombinationTable:
    """M4 — All six recipes verified."""

    def test_blast(self):
        assert COMBINATION_TABLE[frozenset({DamageType.HEAT, DamageType.COLD})] == DamageType.BLAST

    def test_corrosive(self):
        assert COMBINATION_TABLE[frozenset({DamageType.ELECTRICITY, DamageType.TOXIN})] == DamageType.CORROSIVE

    def test_gas(self):
        assert COMBINATION_TABLE[frozenset({DamageType.HEAT, DamageType.TOXIN})] == DamageType.GAS

    def test_magnetic(self):
        assert COMBINATION_TABLE[frozenset({DamageType.COLD, DamageType.ELECTRICITY})] == DamageType.MAGNETIC

    def test_radiation(self):
        assert COMBINATION_TABLE[frozenset({DamageType.HEAT, DamageType.ELECTRICITY})] == DamageType.RADIATION

    def test_viral(self):
        assert COMBINATION_TABLE[frozenset({DamageType.COLD, DamageType.TOXIN})] == DamageType.VIRAL

    def test_all_six_recipes_present(self):
        assert len(COMBINATION_TABLE) == 6


class TestCombineElements:
    BASE = 100.0

    # M5 — Two primaries
    def test_cold_toxin_produces_viral(self):
        """Nagantaka Prime: Cryo Rounds (Cold) + Malignant Force (Toxin) → Viral."""
        mods = [
            DamageComponent(DamageType.COLD, 90.0),
            DamageComponent(DamageType.TOXIN, 90.0),
        ]
        result = combine_elements(mods, innate_elements=[], base_damage=self.BASE)
        assert len(result) == 1
        assert result[0].type == DamageType.VIRAL
        # combined = 180.0; scale=3.125; round(57.6)=58; 58*3.125=181.25
        assert result[0].amount == pytest.approx(181.25)

    def test_heat_cold_produces_blast(self):
        mods = [
            DamageComponent(DamageType.HEAT, 90.0),
            DamageComponent(DamageType.COLD, 90.0),
        ]
        result = combine_elements(mods, innate_elements=[], base_damage=self.BASE)
        assert len(result) == 1
        assert result[0].type == DamageType.BLAST

    def test_combined_amount_is_sum_of_both_primaries(self):
        """Combined element quantizes the sum, not each primary separately."""
        mods = [
            DamageComponent(DamageType.COLD, 60.0),
            DamageComponent(DamageType.TOXIN, 60.0),
        ]
        result = combine_elements(mods, innate_elements=[], base_damage=self.BASE)
        assert result[0].type == DamageType.VIRAL
        # sum=120; scale=3.125; round(38.4)=38; 38*3.125=118.75
        assert result[0].amount == pytest.approx(118.75)

    # M6 — Three mods
    def test_three_mods_first_two_combine(self):
        """Heat(slot0) + Cold(slot1) → Blast; Toxin(slot2) remains primary."""
        mods = [
            DamageComponent(DamageType.HEAT, 90.0),
            DamageComponent(DamageType.COLD, 90.0),
            DamageComponent(DamageType.TOXIN, 90.0),
        ]
        result = combine_elements(mods, innate_elements=[], base_damage=self.BASE)
        types = {c.type for c in result}
        assert DamageType.BLAST in types
        assert DamageType.TOXIN in types
        assert DamageType.HEAT not in types
        assert DamageType.COLD not in types

    def test_innate_appears_last(self):
        """Innate elements combine after all mod elements."""
        mod_elements = [DamageComponent(DamageType.COLD, 90.0)]
        innate = [DamageComponent(DamageType.TOXIN, 30.0)]
        # Cold(mod) then Toxin(innate) → Viral
        result = combine_elements(mod_elements, innate_elements=innate, base_damage=self.BASE)
        assert len(result) == 1
        assert result[0].type == DamageType.VIRAL

    def test_no_elements_returns_empty(self):
        assert combine_elements([], innate_elements=[], base_damage=self.BASE) == []

    def test_single_primary_no_combo(self):
        mods = [DamageComponent(DamageType.HEAT, 90.0)]
        result = combine_elements(mods, innate_elements=[], base_damage=self.BASE)
        assert len(result) == 1
        assert result[0].type == DamageType.HEAT

    def test_kuva_tenet_innate_hcet_ordering(self):
        """Kuva/Tenet: innate primary sorted by HCET goes second-to-last."""
        # Weapon has innate Cold + Electricity; Heat mod added
        # HCET puts Cold before Electricity, so Cold is second-to-last
        # Queue: Heat(mod), Cold(innate-HCET), Electricity(innate-HCET)
        # Heat + Cold → Radiation? No: Heat+Cold = Blast
        # Then Electricity remains
        mod_elements = [DamageComponent(DamageType.HEAT, 90.0)]
        innate = [
            DamageComponent(DamageType.ELECTRICITY, 30.0),
            DamageComponent(DamageType.COLD, 30.0),
        ]
        result = combine_elements(mod_elements, innate_elements=innate,
                                  base_damage=self.BASE, is_kuva_tenet=True)
        types = {c.type for c in result}
        # Heat + Cold (HCET: Cold before Electricity) → Blast; Electricity remains
        assert DamageType.BLAST in types
        assert DamageType.ELECTRICITY in types
