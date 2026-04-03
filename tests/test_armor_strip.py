"""Tests for ability armor strip and Corrosive Projection."""
import pytest
from src.calculator import DamageCalculator, calculate_armor_multiplier
from src.models import Weapon, Mod, Enemy
from src.enums import DamageType, FactionType, HealthType, ArmorType

calc = DamageCalculator()


def impact_weapon() -> Weapon:
    """Pure Impact weapon."""
    return Weapon(
        name="Strip Test",
        base_damage={DamageType.IMPACT: 60.0},
    )


def armored_enemy(armor: float = 300.0) -> Enemy:
    """Grineer enemy with configurable base armor."""
    return Enemy(
        name="Strip Enemy",
        faction=FactionType.GRINEER,
        health_type=HealthType.FLESH,
        armor_type=ArmorType.FERRITE,
        base_armor=armor,
    )


def no_mods() -> list:
    return []


class TestAbilityStrip:
    def test_ability_strip_50pct(self):
        """50% ability strip on 300-armor enemy: armor 300→150, DR 50%→33.3%."""
        stripped = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            ability_strip_pct=0.5,
        )
        baseline = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
        )
        # Stripped enemy should deal more damage
        assert sum(stripped.values()) > sum(baseline.values())

        # Verify armor value: 300*0.5=150; DM=1−0.9×150/2700=0.95
        # Impact vs GRINEER ×1.5: floor(60*1.5)=90; floor(90*0.95)=85
        assert stripped[DamageType.IMPACT] == pytest.approx(85.0)

    def test_cp_strip_additive(self):
        """ability_strip_pct=0.3 + cp_strip_pct=0.3 = 60% total strip.
        armor = 300 * 0.4 = 120."""
        result = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            ability_strip_pct=0.3,
            cp_strip_pct=0.3,
        )
        # 120 armor; DM=1−0.9×120/2700=0.96
        # Impact vs GRINEER ×1.5: floor(60*1.5)=90; floor(90*0.96)=86
        assert result[DamageType.IMPACT] == pytest.approx(86.0)

    def test_pct_capped_at_100(self):
        """ability_strip_pct=0.6 + cp_strip_pct=0.6 → capped at 1.0 → armor=0, full damage."""
        result = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            ability_strip_pct=0.6,
            cp_strip_pct=0.6,
        )
        # With armor=0, no DR; Impact vs GRINEER ×1.5: floor(60*1.5)=90
        assert result[DamageType.IMPACT] == pytest.approx(90.0)

    def test_zero_armor_enemy_no_op(self):
        """Enemy with base_armor=0 → strip params have no effect."""
        baseline = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(0.0),
        )
        stripped = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(0.0),
            ability_strip_pct=0.5,
            cp_strip_pct=0.25,
        )
        assert sum(stripped.values()) == pytest.approx(sum(baseline.values()))
