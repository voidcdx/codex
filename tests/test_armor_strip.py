"""Tests for ability armor strip, Corrosive Projection, and Shattering Impact."""
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

        # Verify armor value: 300*0.5=150; DR=150/450=0.333…; mult=1-0.333=0.667
        # Impact vs GRINEER ×1.5: floor(60*1.5)=90; armor_mult=150/(150+300)=1/3
        # floor(90 * (1-150/450)) = floor(90 * 0.6666...) = floor(60.0) = 60
        assert stripped[DamageType.IMPACT] == pytest.approx(60.0)

    def test_cp_strip_additive(self):
        """ability_strip_pct=0.3 + cp_strip_pct=0.3 = 60% total strip.
        armor = 300 * 0.4 = 120."""
        result = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            ability_strip_pct=0.3,
            cp_strip_pct=0.3,
        )
        # 120 armor; DR=120/420≈0.2857; mult≈0.7143
        # Impact vs GRINEER ×1.5: floor(60*1.5)=90; floor(90*(300/(300+120)))=floor(90*0.7142...)=floor(64.28)=64
        assert result[DamageType.IMPACT] == pytest.approx(64.0)

    def test_pct_capped_at_100(self):
        """ability_strip_pct=0.6 + cp_strip_pct=0.6 → capped at 1.0 → armor=0, full damage."""
        result = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            ability_strip_pct=0.6,
            cp_strip_pct=0.6,
        )
        # With armor=0, no DR; Impact vs GRINEER ×1.5: floor(60*1.5)=90
        assert result[DamageType.IMPACT] == pytest.approx(90.0)

    def test_shattering_impact_flat(self):
        """shattering_impact_flat=60 on 300-armor enemy → armor=240."""
        result = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            shattering_impact_flat=60.0,
        )
        # 240 armor; DR=240/540=0.4444...; mult=0.5555...
        # Impact vs GRINEER ×1.5: floor(60*1.5)=90; floor(90*(300/(300+240)))=floor(90*0.5555...)=floor(50)=50
        assert result[DamageType.IMPACT] == pytest.approx(50.0)

    def test_si_cannot_go_below_zero(self):
        """shattering_impact_flat=9999 on 300-armor enemy → armor clamped to 0, not negative."""
        result = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            shattering_impact_flat=9999.0,
        )
        # armor=0, no DR; Impact vs GRINEER ×1.5: floor(60*1.5)=90
        assert result[DamageType.IMPACT] == pytest.approx(90.0)

    def test_all_combined(self):
        """ability_strip_pct=0.5 + shattering_impact_flat=60 → armor = 300*0.5 - 60 = 90."""
        result = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(300.0),
            ability_strip_pct=0.5,
            shattering_impact_flat=60.0,
        )
        # 90 armor; DR=90/390=0.2307...; mult=0.7692...
        # Impact vs GRINEER ×1.5: floor(60*1.5)=90; floor(90*(300/(300+90)))=floor(90*0.7692...)=floor(69.23)=69
        assert result[DamageType.IMPACT] == pytest.approx(69.0)

    def test_zero_armor_enemy_no_op(self):
        """Enemy with base_armor=0 → strip params have no effect."""
        baseline = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(0.0),
        )
        stripped = calc.calculate(
            impact_weapon(), no_mods(), armored_enemy(0.0),
            ability_strip_pct=0.5,
            cp_strip_pct=0.25,
            shattering_impact_flat=100.0,
        )
        assert sum(stripped.values()) == pytest.approx(sum(baseline.values()))
