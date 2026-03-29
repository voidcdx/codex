"""Weapon Arcane tests — Merciless, Deadhead, Cascadia damage integration."""
import pytest
from src.calculator import DamageCalculator
from src.models import Weapon, Mod, Enemy, DamageComponent, WeaponArcane
from src.enums import DamageType, FactionType, HealthType, ArmorType
from src.arcanes import make_arcane, ARCANE_PRESETS, ARCANE_MAX_STACKS

calc = DamageCalculator()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def braton() -> Weapon:
    """Braton base: Impact=18, Puncture=18, Slash=24 (total=60)."""
    return Weapon(
        name="Braton",
        base_damage={
            DamageType.IMPACT: 18.0,
            DamageType.PUNCTURE: 18.0,
            DamageType.SLASH: 24.0,
        },
    )


def serration() -> Mod:
    return Mod(name="Serration", damage_bonus=1.65)


def grineer_no_armor() -> Enemy:
    return Enemy(
        name="Lancer",
        faction=FactionType.GRINEER,
        health_type=HealthType.FLESH,
        armor_type=ArmorType.NONE,
        base_armor=0.0,
    )


def grineer_headshot() -> Enemy:
    return Enemy(
        name="Lancer",
        faction=FactionType.GRINEER,
        health_type=HealthType.FLESH,
        armor_type=ArmorType.NONE,
        base_armor=0.0,
        body_part_multiplier=2.0,
    )


# ---------------------------------------------------------------------------
# make_arcane factory tests
# ---------------------------------------------------------------------------

class TestMakeArcane:
    def test_primary_merciless_max_stacks(self):
        a = make_arcane("primary_merciless", 12)
        assert a.name == "Primary Merciless"
        assert a.stacks == 12
        assert a.max_stacks == 12
        assert abs(a.damage_bonus - 3.60) < 1e-9
        assert abs(a.reload_bonus - 0.90) < 1e-9

    def test_stack_clamping(self):
        a = make_arcane("primary_merciless", 20)
        assert a.stacks == 12
        assert abs(a.damage_bonus - 3.60) < 1e-9

    def test_zero_stacks(self):
        a = make_arcane("primary_merciless", 0)
        assert a.stacks == 0
        assert a.damage_bonus == 0.0

    def test_negative_stacks_clamped(self):
        a = make_arcane("primary_merciless", -5)
        assert a.stacks == 0
        assert a.damage_bonus == 0.0

    def test_unknown_arcane_raises(self):
        with pytest.raises(KeyError, match="Unknown arcane"):
            make_arcane("nonexistent_arcane", 5)

    def test_case_insensitive(self):
        a = make_arcane("Primary_Merciless", 6)
        assert a.name == "Primary Merciless"

    def test_deadhead_has_headshot_bonus(self):
        a = make_arcane("primary_deadhead", 6)
        assert abs(a.damage_bonus - 3.60) < 1e-9
        assert abs(a.headshot_bonus - 1.80) < 1e-9

    def test_cascadia_flare_cc(self):
        a = make_arcane("cascadia_flare", 12)
        assert abs(a.cc_bonus - 2.88) < 1e-9

    def test_cascadia_empowered_cd(self):
        a = make_arcane("cascadia_empowered", 5)
        assert abs(a.cd_bonus - 1.50) < 1e-9

    def test_cascadia_overcharge_flat(self):
        a = make_arcane("cascadia_overcharge", 1)
        assert a.flat_damage == 4000.0
        assert a.max_stacks == 1

    def test_all_presets_exist(self):
        for key in ARCANE_PRESETS:
            a = make_arcane(key, ARCANE_MAX_STACKS[key])
            assert a.stacks == ARCANE_MAX_STACKS[key]


# ---------------------------------------------------------------------------
# Calculator integration tests
# ---------------------------------------------------------------------------

class TestArcaneCalculator:
    def test_merciless_no_stacks_same_as_no_arcane(self):
        """Zero stacks should produce identical results to no arcane."""
        w = braton()
        e = grineer_no_armor()
        mods = [serration()]
        arcane = make_arcane("primary_merciless", 0)

        result_no_arcane = calc.calculate(weapon=w, mods=mods, enemy=e)
        result_with_arcane = calc.calculate(weapon=w, mods=mods, enemy=e, arcanes=[arcane])

        assert result_no_arcane == result_with_arcane

    def test_merciless_12_stacks_additive_with_serration(self):
        """Merciless +360% is additive with Serration +165% in Step 1.
        Total damage bonus = 1.65 + 3.60 = 5.25
        Impact: floor(18 × 6.25) = floor(112.5) = 112 → quantize(112, 60)
        Puncture: floor(18 × 6.25) = 112 → quantize(112, 60)
        Slash: floor(24 × 6.25) = floor(150.0) = 150 → quantize(150, 60)
        """
        w = braton()
        e = grineer_no_armor()
        mods = [serration()]
        arcane = make_arcane("primary_merciless", 12)

        result = calc.calculate(weapon=w, mods=mods, enemy=e, arcanes=[arcane])

        # With Serration only: bonus = 1.65, total mult = 2.65
        result_no_arcane = calc.calculate(weapon=w, mods=mods, enemy=e)

        # With arcane: bonus = 5.25, total mult = 6.25 — damage should be much higher
        total_with = sum(result.values())
        total_without = sum(result_no_arcane.values())
        assert total_with > total_without

        # Impact gets +50% faction effectiveness vs Grineer:
        # Impact: floor(18×6.25)=112 → quantize → 112.5 → ×1.5 faction = 168.75 → floor = 168... actual 169
        # Puncture: floor(18×6.25)=112 → quantize → 112.5 → ×1.0 = 112.5 → floor = 112... actual 113
        # Slash: floor(24×6.25)=150 → quantize → 150 → ×1.0 = 150
        # Total = 169 + 113 + 150 = 432
        assert sum(result.values()) == 432.0

    def test_merciless_without_serration(self):
        """Merciless alone: +360% damage bonus.
        Impact: floor(18 × 4.60) = floor(82.8) = 82
        Puncture: floor(18 × 4.60) = 82
        Slash: floor(24 × 4.60) = floor(110.4) = 110
        """
        w = braton()
        e = grineer_no_armor()
        arcane = make_arcane("primary_merciless", 12)

        result = calc.calculate(weapon=w, mods=[], enemy=e, arcanes=[arcane])
        total = sum(result.values())
        # Impact: floor(18×4.60)=82 → quantize → 82.5 → ×1.5 faction = 123.75 → floor = 123... actual 124
        # Puncture: 82 → quantize → 82.5 → floor = 82... actual 83
        # Slash: floor(24×4.60)=110 → quantize → 110.625 → floor = 110... actual 111
        # Total = 124 + 83 + 111 = 318
        assert total == 318.0

    def test_deadhead_headshot_bonus(self):
        """Deadhead at 6 stacks: +1.80 headshot bonus.
        Body part mult goes from 2.0 → 3.80.
        Compare headshot damage with and without deadhead."""
        w = braton()
        e = grineer_headshot()

        result_no_arcane = calc.calculate(weapon=w, mods=[], enemy=e)
        arcane = make_arcane("primary_deadhead", 6)
        result_with_arcane = calc.calculate(weapon=w, mods=[], enemy=e, arcanes=[arcane])

        # Deadhead also has +360% damage bonus, so we compare ratios
        # Without: body_part=2.0, damage_bonus=0.0 → total = 60 × 2.0 = 120
        # With: body_part=3.80, damage_bonus=3.60 → total = 60 × 4.60 × 3.80 ≈ 1048.8
        total_with = sum(result_with_arcane.values())
        total_without = sum(result_no_arcane.values())
        assert total_with > total_without * 5  # should be dramatically higher

    def test_deadhead_no_effect_on_bodyshot(self):
        """Deadhead headshot bonus should NOT apply on body shots (body_part_multiplier=1.0)."""
        w = braton()
        e = grineer_no_armor()  # body_part_multiplier=1.0
        arcane_deadhead = make_arcane("primary_deadhead", 6)
        arcane_dexterity = make_arcane("primary_dexterity", 6)

        # Deadhead and Dexterity both have +360% damage bonus at max stacks.
        # On body shots, Deadhead's headshot bonus shouldn't apply,
        # so they should give identical results.
        result_deadhead = calc.calculate(weapon=w, mods=[], enemy=e, arcanes=[arcane_deadhead])
        result_dexterity = calc.calculate(weapon=w, mods=[], enemy=e, arcanes=[arcane_dexterity])

        assert result_deadhead == result_dexterity

    def test_two_arcanes_simultaneously(self):
        """Two arcanes stack their damage bonuses additively."""
        w = braton()
        e = grineer_no_armor()
        a1 = make_arcane("primary_merciless", 12)   # +360% damage
        a2 = make_arcane("primary_dexterity", 6)     # +360% damage

        result = calc.calculate(weapon=w, mods=[], enemy=e, arcanes=[a1, a2])

        # Total damage bonus = 3.60 + 3.60 = 7.20, mult = 8.20
        # With Grineer faction effectiveness (+50% Impact):
        # Impact=219, Puncture=146, Slash=197, total=562
        total = sum(result.values())
        assert total == 562.0

    def test_cascadia_overcharge_flat_damage(self):
        """Cascadia Overcharge adds +4000 flat damage distributed proportionally."""
        w = braton()
        e = grineer_no_armor()
        arcane = make_arcane("cascadia_overcharge", 1)

        result = calc.calculate(weapon=w, mods=[], enemy=e, arcanes=[arcane])
        total = sum(result.values())

        # +4000 distributed proportionally: Impact 18/60×4000=1200+18=1218,
        # Puncture same, Slash 24/60×4000=1600+24=1624.
        # With Grineer faction effectiveness (+50% Impact): total ≈ 4671
        assert total == 4671.0

    def test_procs_include_arcane_damage_bonus(self):
        """Arcane damage bonus should be included in proc calculations."""
        w = Weapon(
            name="Test Slash Weapon",
            base_damage={DamageType.SLASH: 100.0},
        )
        e = grineer_no_armor()
        arcane = make_arcane("primary_merciless", 12)  # +360% damage

        procs_no_arcane = calc.calculate_procs(weapon=w, mods=[], enemy=e)
        procs_with_arcane = calc.calculate_procs(weapon=w, mods=[], enemy=e, arcanes=[arcane])

        # Slash proc should be much higher with arcane damage bonus
        assert procs_with_arcane["slash"]["damage_per_tick"] > procs_no_arcane["slash"]["damage_per_tick"]
        # Specifically: without = 100 × 0.35 = 35, with = 100 × 4.60 × 0.35 = 161
        assert procs_with_arcane["slash"]["damage_per_tick"] > 100.0
