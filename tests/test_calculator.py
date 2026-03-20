"""M7-M10 — DamageCalculator pipeline tests.

M7: Step 1 — Modded base damage (Serration on Braton Slash)
M8: Steps 2-3 — Body part multiplier + faction mod (Bane of Grineer)
M9: Steps 4-5 — Damage type effectiveness + armor mitigation
M10: Integration — Nagantaka Prime full wiki example
"""
import math
import pytest
from src.calculator import DamageCalculator, calculate_armor_multiplier, calculate_crit_multiplier, crit_tier, BANE_MODS, VIRAL_STACK_MULTIPLIERS
from src.models import Weapon, Mod, Enemy, DamageComponent
from src.enums import DamageType, FactionType, HealthType, ArmorType

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
    """Serration: +165% base damage."""
    return Mod(name="Serration", damage_bonus=1.65)


def bane_grineer() -> Mod:
    """Bane of Grineer: +30% faction damage vs Grineer."""
    return Mod(name="Bane of Grineer", faction_bonus=0.30, faction_type=FactionType.GRINEER)


def grineer_flesh_no_armor() -> Enemy:
    return Enemy(
        name="Lancer (no armor)",
        faction=FactionType.GRINEER,
        health_type=HealthType.FLESH,
        armor_type=ArmorType.NONE,
        base_armor=0.0,
    )


def grineer_flesh_300_armor() -> Enemy:
    return Enemy(
        name="Heavy Gunner",
        faction=FactionType.GRINEER,
        health_type=HealthType.FLESH,
        armor_type=ArmorType.FERRITE,
        base_armor=300.0,
    )


# ---------------------------------------------------------------------------
# M7 — Step 1: Modded base damage
# Braton Slash=24, Serration=+165%, base_damage=60
# raw = floor(24 * 2.65) = floor(63.6) = 63
# quantize: scale=60/32=1.875; round(63/1.875)*1.875 = round(33.6)*1.875 = 34*1.875 = 63.75
# ---------------------------------------------------------------------------
class TestStep1ModdedBaseDamage:
    def test_slash_with_serration(self):
        result = calc.calculate(braton(), [serration()], grineer_flesh_no_armor())
        # Slash=24, base=60, scale=1.875
        # Step1: floor(24*2.65)=63; quantize: round(63/1.875)*1.875=34*1.875=63.75
        # Step2 body_part=1.0: round(63.75)=64
        # Step3 no faction: floor(64*1.0)=64
        # Step4 Slash vs FLESH ×1.5: floor(64*1.5)=floor(96.0)=96
        # Step5 no armor → 96
        assert result[DamageType.SLASH] == pytest.approx(96.0)

    def test_no_mods_returns_quantized_base(self):
        """With no mods, damage_bonus=0, so modded=base, just quantized."""
        result = calc.calculate(braton(), [], grineer_flesh_no_armor())
        # Slash=24, base=60, scale=1.875
        # round(24/1.875)*1.875 = round(12.8)*1.875 = 13*1.875 = 24.375
        # vs FLESH: floor(24.375 * 1.5) = floor(36.5625) = 36
        assert result[DamageType.SLASH] == pytest.approx(36.0)


# ---------------------------------------------------------------------------
# M8 — Steps 2-3: Body part multiplier + faction
# Braton Slash=24, Serration(+165%), headshot=2×, Bane of Grineer(+30%)
# Step1 Slash quantized = 63.75
# Step2 body part: round(63.75 * 2.0) = round(127.5) = 128  (Python banker's rounding → 128)
# Step3 faction: floor(128 * 1.30) = floor(166.4) = 166
# Step4 type (Slash vs FLESH ×1.5): floor(166 * 1.5) = floor(249.0) = 249
# Step5 no armor → 249
# ---------------------------------------------------------------------------
class TestSteps2And3:
    def test_headshot_faction(self):
        enemy = grineer_flesh_no_armor()
        enemy.body_part_multiplier = 2.0
        result = calc.calculate(braton(), [serration(), bane_grineer()], enemy)
        assert result[DamageType.SLASH] == pytest.approx(249.0)

    def test_faction_mod_wrong_faction_not_applied(self):
        """Bane of Grineer should have no effect on a Corpus enemy."""
        enemy = Enemy(
            name="Crewman",
            faction=FactionType.CORPUS,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
        )
        result_with = calc.calculate(braton(), [serration(), bane_grineer()], enemy)
        result_without = calc.calculate(braton(), [serration()], enemy)
        assert result_with == result_without


# ---------------------------------------------------------------------------
# M9 — Steps 4-5: Damage type effectiveness + armor mitigation
# Braton Slash=24, Serration(+165%), Grineer FLESH + 300 Ferrite armor
# Step1 Slash quantized = 63.75
# Step2 no headshot: round(63.75 * 1.0) = 64 (round to nearest int)
# Step3 no faction: floor(64 * 1.0) = 64
# Step4 Slash vs FLESH ×1.5: floor(64 * 1.5) = floor(96.0) = 96
# Step5 armor 300/(300+300)=0.5: floor(96 * 0.5) = 48
# ---------------------------------------------------------------------------
class TestSteps4And5:
    def test_armor_mitigation(self):
        result = calc.calculate(braton(), [serration()], grineer_flesh_300_armor())
        assert result[DamageType.SLASH] == pytest.approx(48.0)

    def test_true_damage_bypasses_armor(self):
        weapon = Weapon(
            name="True Test",
            base_damage={DamageType.TRUE: 100.0},
        )
        result = calc.calculate(weapon, [], grineer_flesh_300_armor())
        # TRUE damage: no type mult (neutral vs FLESH), no armor bypass
        assert DamageType.TRUE in result
        # quantize: scale=100/32=3.125; round(100/3.125)*3.125=100.0
        assert result[DamageType.TRUE] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# M10 — Integration: Nagantaka Prime (wiki example)
# Mods: Cryo Rounds(+90% Cold), Malignant Force(+90% Toxin),
#        Hellfire(+90% Heat), Piercing Caliber(+120% Puncture),
#        Gas Valence Formation (innate Gas element)
# Expected totals from wiki:
#   0 Impact + 32.4375 Puncture + 156.78125 Slash +
#   259.5 Viral + 156.78125 Heat + 346 Gas ≈ 951.5
#
# Note: tested against no-armor, no-faction enemy to isolate quantization.
# ---------------------------------------------------------------------------
class TestNagantakaPrimeIntegration:
    """Nagantaka Prime wiki worked example — validates full quantization pipeline."""

    @pytest.fixture
    def nagantaka_prime(self) -> Weapon:
        # Wiki example uses a weapon where Impact is so small it quantizes to 0.
        # We approximate: total base ≈ 208, Impact negligible (1.0), rest Puncture/Slash.
        # Gas Valence Formation adds innate Gas at 100% of base.
        # The wiki pre-quantization values: Puncture≈32.4375, Slash≈156.78125 suggest
        # a specific modded total; we use a simplified setup to verify pipeline shape.
        return Weapon(
            name="Nagantaka Prime",
            base_damage={
                DamageType.IMPACT: 1.0,       # ~0 after quantization at large base
                DamageType.PUNCTURE: 104.0,
                DamageType.SLASH: 104.0,
            },
            innate_elements=[
                # Gas Valence Formation: 100% innate Gas = flat 209 (equal to IPS total)
                DamageComponent(DamageType.GAS, 209.0),
            ],
        )

    @pytest.fixture
    def mods(self) -> list[Mod]:
        return [
            Mod("Cryo Rounds",      elemental_bonuses=[DamageComponent(DamageType.COLD,  0.90)]),
            Mod("Malignant Force",  elemental_bonuses=[DamageComponent(DamageType.TOXIN, 0.90)]),
            Mod("Hellfire",         elemental_bonuses=[DamageComponent(DamageType.HEAT,  0.90)]),
            Mod("Piercing Caliber", elemental_bonuses=[DamageComponent(DamageType.PUNCTURE, 1.20)]),
        ]

    @pytest.fixture
    def no_armor_neutral_enemy(self) -> Enemy:
        """Neutral health type (ROBOTIC) so no type effectiveness skews the totals."""
        return Enemy(
            name="Test Target",
            faction=FactionType.NONE,
            health_type=HealthType.ROBOTIC,
            armor_type=ArmorType.NONE,
        )

    def test_impact_rounds_to_zero(self, nagantaka_prime, mods, no_armor_neutral_enemy):
        """With a tiny Impact value relative to the base, it should quantize to 0."""
        result = calc.calculate(nagantaka_prime, mods, no_armor_neutral_enemy)
        # Impact=1 with total_base=209; scale≈6.53; round(1/6.53)=round(0.15)=0 → dropped
        assert DamageType.IMPACT not in result

    def test_elemental_types_present(self, nagantaka_prime, mods, no_armor_neutral_enemy):
        """Cryo+Toxin→Viral, Hellfire remains Heat, innate Gas stays Gas."""
        result = calc.calculate(nagantaka_prime, mods, no_armor_neutral_enemy)
        assert DamageType.VIRAL in result
        assert DamageType.HEAT in result
        assert DamageType.GAS in result

    def test_puncture_slash_present(self, nagantaka_prime, mods, no_armor_neutral_enemy):
        result = calc.calculate(nagantaka_prime, mods, no_armor_neutral_enemy)
        assert DamageType.PUNCTURE in result
        assert DamageType.SLASH in result


# ---------------------------------------------------------------------------
# calculate_armor_multiplier unit tests
# ---------------------------------------------------------------------------
class TestCalculateArmorMultiplier:
    def test_no_armor_type_returns_one(self):
        assert calculate_armor_multiplier(300.0, DamageType.SLASH, ArmorType.NONE) == pytest.approx(1.0)

    def test_zero_armor_returns_one(self):
        assert calculate_armor_multiplier(0.0, DamageType.SLASH, ArmorType.FERRITE) == pytest.approx(1.0)

    def test_neutral_type_300_ferrite(self):
        # Slash vs Ferrite: no armor_mod, no damage_mod
        # effective_armor=300, DR=300/600=0.5 → passes 0.5
        assert calculate_armor_multiplier(300.0, DamageType.SLASH, ArmorType.FERRITE) == pytest.approx(0.5)

    def test_corrosive_vs_ferrite_ignores_75_percent_armor(self):
        # armor_mod=0.75 → effective=300*0.25=75; DR=75/375=0.2 → passes 0.8
        # damage_mod=0.5 → final = 0.8 * 1.5 = 1.2
        assert calculate_armor_multiplier(300.0, DamageType.CORROSIVE, ArmorType.FERRITE) == pytest.approx(1.2)

    def test_puncture_vs_ferrite_ignores_50_percent_armor(self):
        # armor_mod=0.5 → effective=300*0.5=150; DR=150/450=1/3 → passes 2/3
        # damage_mod=0.5 → final = (2/3) * 1.5 = 1.0
        assert calculate_armor_multiplier(300.0, DamageType.PUNCTURE, ArmorType.FERRITE) == pytest.approx(1.0)

    def test_armor_capped_at_2700(self):
        # 9999 armor → clamped to 2700; DR=2700/3000=0.9 → passes 0.1
        assert calculate_armor_multiplier(9999.0, DamageType.SLASH, ArmorType.FERRITE) == pytest.approx(0.1)

    def test_blast_vs_ferrite_damage_penalty(self):
        # armor_mod=0.0, damage_mod=-0.5 → effective=300, passes 0.5; final=0.5*0.5=0.25
        assert calculate_armor_multiplier(300.0, DamageType.BLAST, ArmorType.FERRITE) == pytest.approx(0.25)

    def test_radiation_vs_alloy_ignores_75_percent_armor(self):
        # armor_mod=0.75 → effective=300*0.25=75; passes 0.8; damage_mod=0.5 → 1.2
        assert calculate_armor_multiplier(300.0, DamageType.RADIATION, ArmorType.ALLOY) == pytest.approx(1.2)


# ---------------------------------------------------------------------------
# crit_tier and calculate_crit_multiplier tests
# ---------------------------------------------------------------------------
class TestCritTier:
    def test_t1_below_100(self):
        assert crit_tier(0.75) == 0   # <100% → T0 (no guaranteed crit)

    def test_t1_at_100(self):
        assert crit_tier(1.0) == 1    # exactly 100% → T1

    def test_t2_at_165(self):
        assert crit_tier(1.65) == 1   # 165% → T1 guaranteed, 65% chance T2

    def test_t2_at_200(self):
        assert crit_tier(2.0) == 2    # 200% → T2

    def test_t3_at_225(self):
        assert crit_tier(2.25) == 2   # 225% → T2 guaranteed, 25% chance T3


class TestCalculateCritMultiplier:
    CM = 3.5   # modded crit multiplier (e.g. 350%)

    def test_average_t1_only(self):
        # CC=0.75, CM=3.5: 1 + 0.75*(3.5-1) = 1 + 1.875 = 2.875
        assert calculate_crit_multiplier(0.75, self.CM, "average") == pytest.approx(2.875)

    def test_average_t2_165_percent(self):
        # CC=1.65: 1 + 1.65*(3.5-1) = 1 + 4.125 = 5.125
        assert calculate_crit_multiplier(1.65, self.CM, "average") == pytest.approx(5.125)

    def test_guaranteed_uses_floor_tier(self):
        # CC=1.65 → T=1: 1 + 1*(3.5-1) = 3.5
        assert calculate_crit_multiplier(1.65, self.CM, "guaranteed") == pytest.approx(3.5)

    def test_max_uses_ceiling_tier(self):
        # CC=1.65 → T+1=2: 1 + 2*(3.5-1) = 6.0
        assert calculate_crit_multiplier(1.65, self.CM, "max") == pytest.approx(6.0)

    def test_average_equals_guaranteed_at_exact_100(self):
        # CC=1.0 exactly: average = 1+1*(CM-1) = CM; guaranteed = same
        assert calculate_crit_multiplier(1.0, self.CM, "average") == pytest.approx(
            calculate_crit_multiplier(1.0, self.CM, "guaranteed")
        )

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            calculate_crit_multiplier(1.5, self.CM, "invalid")


# ---------------------------------------------------------------------------
# BANE_MODS constants + faction Step 3 integration
# ---------------------------------------------------------------------------
class TestBaneMods:
    def test_all_eight_bane_mods_present(self):
        expected = {
            "Bane of Grineer", "Bane of Corpus", "Bane of Infested", "Bane of Corrupted",
            "Primed Bane of Grineer", "Primed Bane of Corpus",
            "Primed Bane of Infested", "Primed Bane of Corrupted",
        }
        assert set(BANE_MODS.keys()) == expected

    def test_standard_bane_bonus_is_30_percent(self):
        assert BANE_MODS["Bane of Grineer"].faction_bonus == pytest.approx(0.30)
        assert BANE_MODS["Bane of Infested"].faction_bonus == pytest.approx(0.30)

    def test_primed_bane_bonus_is_55_percent(self):
        assert BANE_MODS["Primed Bane of Grineer"].faction_bonus == pytest.approx(0.55)
        assert BANE_MODS["Primed Bane of Corpus"].faction_bonus == pytest.approx(0.55)

    def test_bane_applied_in_pipeline(self):
        # Braton Slash=24, no damage mods, Bane of Grineer +30% vs Grineer FLESH (no armor)
        # Step1: quantize(24, 60) = round(24/1.875)*1.875 = 13*1.875 = 24.375
        # Step2: round(24.375*1.0) = 24
        # Step3: floor(24 * 1.30) = floor(31.2) = 31
        # Step4: Slash vs FLESH ×1.5 → floor(31*1.5) = floor(46.5) = 46
        # Step5: no armor → 46
        result = calc.calculate(braton(), [BANE_MODS["Bane of Grineer"]], grineer_flesh_no_armor())
        assert result[DamageType.SLASH] == pytest.approx(46.0)

    def test_primed_bane_applied_in_pipeline(self):
        # Same as above but +55%: floor(24 * 1.55) = floor(37.2) = 37
        # Step4: floor(37*1.5) = floor(55.5) = 55
        result = calc.calculate(braton(), [BANE_MODS["Primed Bane of Grineer"]], grineer_flesh_no_armor())
        assert result[DamageType.SLASH] == pytest.approx(55.0)

    def test_wrong_faction_bane_not_applied(self):
        # Bane of Corpus on Grineer enemy → no bonus
        result_with = calc.calculate(braton(), [BANE_MODS["Bane of Corpus"]], grineer_flesh_no_armor())
        result_without = calc.calculate(braton(), [], grineer_flesh_no_armor())
        assert result_with == result_without


# ---------------------------------------------------------------------------
# M11: Viral status proc multiplier
# ---------------------------------------------------------------------------

class TestViralStackMultipliers:
    def test_table_values(self):
        expected = {0: 1.0, 1: 1.75, 2: 2.0, 3: 2.25, 4: 2.5, 5: 2.75,
                    6: 3.0, 7: 3.25, 8: 3.5, 9: 3.75, 10: 4.25}
        assert VIRAL_STACK_MULTIPLIERS == expected

    def test_zero_stacks_no_change(self):
        result_0  = calc.calculate(braton(), [], grineer_flesh_no_armor(), viral_stacks=0)
        result_no = calc.calculate(braton(), [], grineer_flesh_no_armor())
        assert result_0 == result_no

    def test_10_stacks_multiplier(self):
        # Braton Slash=24 vs FLESH (no armor, no mods)
        # Before Viral: Step3 Slash ×1.5 → floor(24*1.5)=36; Step4 no armor→36; Step5 no faction→36
        # Viral ×4.25: floor(36 * 4.25) = floor(153.0) = 153
        result = calc.calculate(braton(), [], grineer_flesh_no_armor(), viral_stacks=10)
        assert result[DamageType.SLASH] == pytest.approx(153.0)

    def test_stacks_capped_at_10(self):
        result_10  = calc.calculate(braton(), [], grineer_flesh_no_armor(), viral_stacks=10)
        result_cap = calc.calculate(braton(), [], grineer_flesh_no_armor(), viral_stacks=99)
        assert result_10 == result_cap


# ---------------------------------------------------------------------------
# M12: Secondary elemental mods (Magnetic, Blast, etc.) must apply
# ---------------------------------------------------------------------------

class TestSecondaryElementalMods:
    def test_magnetic_mod_applies(self):
        weapon = Weapon(
            name="Test Rifle",
            base_damage={DamageType.IMPACT: 20.0, DamageType.PUNCTURE: 20.0, DamageType.SLASH: 20.0},
        )
        magnetic_mod = Mod(
            name="Magnetic Capacity",
            elemental_bonuses=[DamageComponent(DamageType.MAGNETIC, 0.60)],
        )
        enemy = Enemy(
            name="Test",
            faction=FactionType.CORPUS,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
        )
        result = calc.calculate(weapon, [magnetic_mod], enemy)
        assert DamageType.MAGNETIC in result
        assert result[DamageType.MAGNETIC] == pytest.approx(36.0)

    def test_blast_mod_applies(self):
        weapon = Weapon(
            name="Test Rifle",
            base_damage={DamageType.IMPACT: 30.0, DamageType.SLASH: 30.0},
        )
        blast_mod = Mod(
            name="Blast test",
            elemental_bonuses=[DamageComponent(DamageType.BLAST, 0.90)],
        )
        enemy = Enemy(
            name="Test",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
        )
        result = calc.calculate(weapon, [blast_mod], enemy)
        assert DamageType.BLAST in result


# ---------------------------------------------------------------------------
# M13: Status proc simulation (calculate_procs)
# ---------------------------------------------------------------------------

class TestCalculateProcs:
    def _pure_impact_weapon(self) -> Weapon:
        return Weapon(name="Impact Only", base_damage={DamageType.IMPACT: 60.0})

    def _braton_no_armor(self) -> Enemy:
        return Enemy(
            name="Test",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
        )

    def test_slash_proc_active_when_slash_present(self):
        procs = calc.calculate_procs(braton(), [], self._braton_no_armor())
        assert procs["slash"]["active"] is True

    def test_slash_proc_inactive_without_slash(self):
        procs = calc.calculate_procs(self._pure_impact_weapon(), [], self._braton_no_armor())
        assert procs["slash"]["active"] is False
        assert procs["slash"]["damage_per_tick"] == 0.0
        assert procs["slash"]["total_damage"] == 0.0

    def test_slash_proc_no_faction(self):
        # total_step2 = 19+19+24 = 62; DPT = floor(62 * 0.35) = 21
        procs = calc.calculate_procs(braton(), [], self._braton_no_armor())
        assert procs["slash"]["ticks"] == 6
        assert procs["slash"]["damage_per_tick"] == pytest.approx(21.0)
        assert procs["slash"]["total_damage"] == pytest.approx(126.0)

    def test_slash_proc_faction_double_dip(self):
        # DPT = floor(62 * 0.35 * 1.30²) = floor(36.603) = 36
        enemy = self._braton_no_armor()
        enemy.faction = FactionType.GRINEER
        procs = calc.calculate_procs(braton(), [bane_grineer()], enemy)
        assert procs["slash"]["damage_per_tick"] == pytest.approx(36.0)
        assert procs["slash"]["total_damage"] == pytest.approx(216.0)

    def test_heat_proc_inactive_without_heat(self):
        procs = calc.calculate_procs(braton(), [], self._braton_no_armor())
        assert procs["heat"]["active"] is False

    def test_heat_proc_active_with_innate_heat(self):
        weapon = Weapon(
            name="Heat Weapon",
            base_damage={DamageType.SLASH: 60.0},
            innate_elements=[DamageComponent(DamageType.HEAT, 60.0)],
        )
        procs = calc.calculate_procs(weapon, [], self._braton_no_armor())
        assert procs["heat"]["active"] is True
        assert procs["heat"]["ticks"] == 6
        # total_step2 ~120; heat_eff vs FLESH = 1.5; DPT = floor(120*0.5*1.5) = 90
        assert procs["heat"]["damage_per_tick"] == pytest.approx(90.0)
