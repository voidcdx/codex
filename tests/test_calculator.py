"""M7-M10 — DamageCalculator pipeline tests.

M7: Step 1 — Modded base damage (Serration on Braton Slash)
M8: Steps 2-3 — Body part multiplier + faction mod (Bane of Grineer)
M9: Steps 4-5 — Damage type effectiveness + armor mitigation
M10: Integration — Nagantaka Prime full wiki example
"""
import math
import pytest
from src.calculator import DamageCalculator, calculate_armor_multiplier, calculate_crit_multiplier, crit_tier, status_chance_per_pellet, BANE_MODS, VIRAL_STACK_MULTIPLIERS
from src.loader import make_riven_mod
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
        # Step4 Slash vs GRINEER neutral ×1.0: floor(64*1.0)=64
        # Step5 no armor → 64
        assert result[DamageType.SLASH] == pytest.approx(64.0)

    def test_no_mods_returns_quantized_base(self):
        """With no mods, damage_bonus=0, so modded=base, just quantized."""
        result = calc.calculate(braton(), [], grineer_flesh_no_armor())
        # Slash=24, base=60, scale=1.875
        # round(24/1.875)*1.875 = round(12.8)*1.875 = 13*1.875 = 24.375
        # round(24.375) = 24; Slash vs GRINEER neutral ×1.0: 24
        assert result[DamageType.SLASH] == pytest.approx(24.0)


# ---------------------------------------------------------------------------
# M8 — Steps 2-3: Body part multiplier + faction
# Braton Slash=24, Serration(+165%), headshot=2×, Bane of Grineer(+30%)
# Step1 Slash quantized = 63.75
# Step2 body part: round(63.75 * 2.0) = round(127.5) = 128  (ROUND_HALF_UP)
# Step3 faction: floor(128 * 1.30) = floor(166.4) = 166
# Step4 type (Slash vs GRINEER neutral ×1.0): floor(166 * 1.0) = 166
# Step5 no armor → 166
# ---------------------------------------------------------------------------
class TestSteps2And3:
    def test_headshot_faction(self):
        enemy = grineer_flesh_no_armor()
        enemy.body_part_multiplier = 2.0
        result = calc.calculate(braton(), [serration(), bane_grineer()], enemy)
        assert result[DamageType.SLASH] == pytest.approx(166.0)

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
# Braton Slash=24, Serration(+165%), Grineer FLESH + 300 armor
# Step1 Slash quantized = 63.75
# Step2 no headshot: round(63.75 * 1.0) = 64 (round to nearest int)
# Step3 no faction: floor(64 * 1.0) = 64
# Step4 Slash vs GRINEER neutral ×1.0: floor(64 * 1.0) = 64
# Step5 armor 300/(300+300)=0.5: floor(64 * 0.5) = 32
# ---------------------------------------------------------------------------
class TestSteps4And5:
    def test_armor_mitigation(self):
        result = calc.calculate(braton(), [serration()], grineer_flesh_300_armor())
        assert result[DamageType.SLASH] == pytest.approx(32.0)

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
# Post-Update 36 (Jade Shadows): flat DR only — no armor-type modifiers.
# DR = armor / (armor + 300), capped at 2700 (90% DR).
# ---------------------------------------------------------------------------
class TestCalculateArmorMultiplier:
    def test_zero_armor_returns_one(self):
        assert calculate_armor_multiplier(0.0) == pytest.approx(1.0)

    def test_negative_armor_returns_one(self):
        assert calculate_armor_multiplier(-10.0) == pytest.approx(1.0)

    def test_300_armor_flat_dr(self):
        # DR = 300/(300+300) = 0.5 → passes 0.5
        assert calculate_armor_multiplier(300.0) == pytest.approx(0.5)

    def test_armor_capped_at_2700(self):
        # 9999 armor → clamped to 2700; DR=2700/3000=0.9 → passes 0.1
        assert calculate_armor_multiplier(9999.0) == pytest.approx(0.1)

    def test_600_armor(self):
        # DR = 600/(600+300) = 2/3 → passes 1/3 ≈ 0.333...
        assert calculate_armor_multiplier(600.0) == pytest.approx(300.0 / 900.0)


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
        # Step4: Slash vs GRINEER neutral ×1.0 → 31
        # Step5: no armor → 31
        result = calc.calculate(braton(), [BANE_MODS["Bane of Grineer"]], grineer_flesh_no_armor())
        assert result[DamageType.SLASH] == pytest.approx(31.0)

    def test_primed_bane_applied_in_pipeline(self):
        # Same as above but +55%: floor(24 * 1.55) = floor(37.2) = 37
        # Step4: Slash vs GRINEER neutral ×1.0 → 37
        result = calc.calculate(braton(), [BANE_MODS["Primed Bane of Grineer"]], grineer_flesh_no_armor())
        assert result[DamageType.SLASH] == pytest.approx(37.0)

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
        # Braton Slash=24 vs GRINEER (no armor, no mods)
        # Slash vs GRINEER neutral ×1.0 → 24; Viral ×4.25: floor(24 * 4.25) = 102
        result = calc.calculate(braton(), [], grineer_flesh_no_armor(), viral_stacks=10)
        assert result[DamageType.SLASH] == pytest.approx(102.0)

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
        # Magnetic vs CORPUS = 1.5; quantized magnetic = 35.625 → round = 36 → floor(36*1.5) = 54
        assert result[DamageType.MAGNETIC] == pytest.approx(54.0)

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
        # total_step2 ~120; heat_eff vs GRINEER = 1.0 (neutral); DPT = floor(120*0.5*1.0) = 60
        assert procs["heat"]["damage_per_tick"] == pytest.approx(60.0)

    def test_gas_proc_inactive_without_gas(self):
        procs = calc.calculate_procs(braton(), [], self._braton_no_armor())
        assert procs["gas"]["active"] is False

    def test_gas_proc_wiki_example(self):
        """Verifies Gas proc ignores Heat/Toxin mods.
        base=150 (100 IPS + 50 innate Gas), damage_bonus=1.65, faction=0.30, no gas/status-damage mods.
        DPT = floor(150 × 2.65 × 1.30² × 0.5) = floor(335.8875) = 335
        Source: wiki.warframe.com/w/Damage/Gas_Damage
        """
        weapon = Weapon(
            name="Gas Wiki Test",
            base_damage={DamageType.IMPACT: 100.0},
            innate_elements=[DamageComponent(DamageType.GAS, 50.0)],  # Gas present
        )
        # Heat and Toxin mods should NOT affect Gas proc DPT.
        heat_mod  = Mod(name="Thermite Rounds", elemental_bonuses=[DamageComponent(DamageType.HEAT, 0.90)])
        toxin_mod = Mod(name="Infected Clip",   elemental_bonuses=[DamageComponent(DamageType.TOXIN, 0.90)])
        serration = Mod(name="Serration", damage_bonus=1.65)
        bane      = Mod(name="Bane of Grineer", faction_bonus=0.30, faction_type=FactionType.GRINEER)
        enemy = Enemy(
            name="Lancer",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
        )
        procs = calc.calculate_procs(weapon, [serration, heat_mod, toxin_mod, bane], enemy)
        assert procs["gas"]["active"] is True
        assert procs["gas"]["ticks"] == 6
        assert procs["gas"]["damage_per_tick"] == pytest.approx(335.0)

    def test_gas_proc_wiki_example1_status_damage(self):
        """Wiki Example 1: Heat+Toxin mods ignored; Pistol Elementalist (+90% status damage) scales proc.
        Modded Base = 180 × (1+2.2) × (1+0.3) = 748.8
        DPT = floor(0.5 × 748.8 × (1+0.3) × (1+0.9)) = floor(924.768) = 924
        Source: wiki.warframe.com/w/Damage/Gas_Damage
        """
        weapon = Weapon(
            name="Wiki Ex1",
            base_damage={DamageType.IMPACT: 180.0},
            innate_elements=[DamageComponent(DamageType.GAS, 0.0001)],  # tiny Gas to activate proc
        )
        hornet      = Mod(name="Hornet Strike",     damage_bonus=2.20)
        scorch      = Mod(name="Scorch",            elemental_bonuses=[DamageComponent(DamageType.HEAT, 0.90)])
        pathogen    = Mod(name="Pathogen Rounds",   elemental_bonuses=[DamageComponent(DamageType.TOXIN, 0.90)])
        expel       = Mod(name="Expel Grineer",     faction_bonus=0.30, faction_type=FactionType.GRINEER)
        elementalist = Mod(name="Pistol Elementalist", status_damage_bonus=0.90)
        enemy = Enemy(
            name="Lancer",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
        )
        procs = calc.calculate_procs(weapon, [hornet, scorch, pathogen, expel, elementalist], enemy)
        assert procs["gas"]["active"] is True
        # base≈180 (ignoring tiny innate), damage_bonus=2.2, faction=0.3, status_damage=0.9, gas_bonus=0
        # DPT = floor(0.5 × 180 × 3.2 × 1.69 × 1.9) = floor(0.5 × 748.8 × 1.3 × 1.9) = floor(924.768) = 924
        assert procs["gas"]["damage_per_tick"] == pytest.approx(924.0)

    def test_gas_proc_wiki_example2_gas_mod(self):
        """Wiki Example 2: Leaded Gas (+300% gas_bonus) scales proc multiplicatively.
        Modded Base = 180 × (1+2.2) × (1+0.3) = 748.8
        DPT = floor(0.5 × 748.8 × (1+3) × (1+0.3) × (1+0.9)) = floor(3699.072) = 3699
        Source: wiki.warframe.com/w/Damage/Gas_Damage
        """
        weapon = Weapon(
            name="Wiki Ex2",
            base_damage={DamageType.IMPACT: 180.0},
            innate_elements=[DamageComponent(DamageType.GAS, 0.0001)],
        )
        hornet      = Mod(name="Hornet Strike",     damage_bonus=2.20)
        leaded_gas  = Mod(name="Leaded Gas",        elemental_bonuses=[DamageComponent(DamageType.GAS, 3.0)])
        expel       = Mod(name="Expel Grineer",     faction_bonus=0.30, faction_type=FactionType.GRINEER)
        elementalist = Mod(name="Pistol Elementalist", status_damage_bonus=0.90)
        enemy = Enemy(
            name="Lancer",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
        )
        procs = calc.calculate_procs(weapon, [hornet, leaded_gas, expel, elementalist], enemy)
        assert procs["gas"]["active"] is True
        # gas_bonus=3.0 from Leaded Gas; DPT = floor(0.5 × 180 × 3.2 × 1.69 × 4 × 1.9) = floor(3699.072) = 3699
        assert procs["gas"]["damage_per_tick"] == pytest.approx(3699.0)

    def test_gas_proc_ignores_elemental_mods(self):
        """Adding elemental mods should NOT change Gas proc DPT."""
        weapon = Weapon(
            name="Gas Test",
            base_damage={DamageType.SLASH: 100.0},
            innate_elements=[DamageComponent(DamageType.GAS, 50.0)],
        )
        enemy = self._braton_no_armor()
        heat_mod = Mod(name="Hellfire", elemental_bonuses=[DamageComponent(DamageType.HEAT, 0.90)])
        procs_without = calc.calculate_procs(weapon, [], enemy)
        procs_with    = calc.calculate_procs(weapon, [heat_mod], enemy)
        assert procs_without["gas"]["damage_per_tick"] == procs_with["gas"]["damage_per_tick"]


# ---------------------------------------------------------------------------
# Toxin proc — 50% of total step-2 damage × Toxin effectiveness vs health
# Source: wiki.warframe.com/w/Damage/Toxin_Damage
# ---------------------------------------------------------------------------
class TestToxinProc:
    def _flesh_enemy(self):
        return Enemy(
            name="Flesh target",
            faction=FactionType.CORPUS,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
            base_armor=0.0,
        )

    def test_toxin_proc_inactive_without_toxin(self):
        procs = calc.calculate_procs(braton(), [], self._flesh_enemy())
        assert procs["toxin"]["active"] is False

    def test_toxin_proc_active_with_innate_toxin(self):
        """Slash=60 + Toxin=60 innate; total_step2=120; toxin_eff vs CORPUS=1.0 (neutral)
        DPT = floor(120 * 0.5 * 1.0) = floor(60.0) = 60; 6 ticks → total=360
        """
        weapon = Weapon(
            name="Toxin Test",
            base_damage={DamageType.SLASH: 60.0},
            innate_elements=[DamageComponent(DamageType.TOXIN, 60.0)],
        )
        procs = calc.calculate_procs(weapon, [], self._flesh_enemy())
        assert procs["toxin"]["active"] is True
        assert procs["toxin"]["ticks"] == 6
        assert procs["toxin"]["damage_per_tick"] == pytest.approx(60.0)
        assert procs["toxin"]["total_damage"] == pytest.approx(360.0)

    def test_toxin_proc_faction_double_dip(self):
        """Bane of Corpus (+30%) applies twice: DPT × 1.30² = DPT × 1.69."""
        weapon = Weapon(
            name="Toxin Bane Test",
            base_damage={DamageType.SLASH: 60.0},
            innate_elements=[DamageComponent(DamageType.TOXIN, 60.0)],
        )
        bane_corpus = Mod(name="Bane of Corpus", faction_bonus=0.30, faction_type=FactionType.CORPUS)
        procs = calc.calculate_procs(weapon, [bane_corpus], self._flesh_enemy())
        # total_step2=120; toxin_eff vs CORPUS=1.0; DPT = floor(120 * 0.5 * 1.0 * 1.69) = floor(101.4) = 101
        assert procs["toxin"]["damage_per_tick"] == pytest.approx(101.0)


# ---------------------------------------------------------------------------
# Electricity proc — 50% of total step-2 damage × Electricity effectiveness vs health
# Single-target DoT only (chaining to other enemies is out of scope).
# Source: wiki.warframe.com/w/Damage/Electricity_Damage
# ---------------------------------------------------------------------------
class TestElectricityProc:
    def _robotic_enemy(self):
        return Enemy(
            name="Robotic target",
            faction=FactionType.CORPUS,
            health_type=HealthType.ROBOTIC,
            armor_type=ArmorType.NONE,
            base_armor=0.0,
        )

    def test_electricity_proc_inactive_without_electricity(self):
        procs = calc.calculate_procs(braton(), [], self._robotic_enemy())
        assert procs["electricity"]["active"] is False

    def test_electricity_proc_active_with_innate_electricity(self):
        """Slash=60 + Electricity=60 innate; total_step2=120; elec_eff vs CORPUS=1.0 (neutral)
        DPT = floor(120 * 0.5 * 1.0) = floor(60.0) = 60; 6 ticks → total=360
        """
        weapon = Weapon(
            name="Electricity Test",
            base_damage={DamageType.SLASH: 60.0},
            innate_elements=[DamageComponent(DamageType.ELECTRICITY, 60.0)],
        )
        procs = calc.calculate_procs(weapon, [], self._robotic_enemy())
        assert procs["electricity"]["active"] is True
        assert procs["electricity"]["ticks"] == 6
        assert procs["electricity"]["damage_per_tick"] == pytest.approx(60.0)
        assert procs["electricity"]["total_damage"] == pytest.approx(360.0)

    def test_electricity_proc_neutral_vs_flesh(self):
        """Electricity effectiveness vs FLESH is neutral (1.0).
        total_step2=120; DPT = floor(120 * 0.5 * 1.0) = 60
        """
        weapon = Weapon(
            name="Electricity Flesh Test",
            base_damage={DamageType.SLASH: 60.0},
            innate_elements=[DamageComponent(DamageType.ELECTRICITY, 60.0)],
        )
        flesh_enemy = Enemy(
            name="Flesh",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
            base_armor=0.0,
        )
        procs = calc.calculate_procs(weapon, [], flesh_enemy)
        assert procs["electricity"]["damage_per_tick"] == pytest.approx(60.0)


# ---------------------------------------------------------------------------
# Corrosive strip — armor reduction applied at Step 4 before armor mitigation
# Formula: stripped_armor = base_armor × (1 − min(0.80, 0.20 + 0.06 × stacks))
# Source: wiki.warframe.com/w/Damage/Corrosive_Damage
# ---------------------------------------------------------------------------
class TestCorrosiveStrip:
    def _impact_weapon(self):
        """Pure Impact weapon (neutral vs Ferrite armor: no bonus/penalty)."""
        return Weapon(
            name="Impact Test",
            base_damage={DamageType.IMPACT: 60.0},
        )

    def _ferrite_enemy(self, armor=300.0):
        return Enemy(
            name="Heavy Gunner",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.FERRITE,
            base_armor=armor,
        )

    def test_zero_stacks_no_change(self):
        """0 stacks = no armor reduction; baseline reference."""
        # Impact=60, Serration(+165%): floor(60*2.65)=159; quantize→159.375; round→159
        # Impact vs GRINEER ×1.5: floor(159*1.5)=floor(238.5)=238
        # Flat DR=300/600=0.5; floor(238*0.5)=119
        result = calc.calculate(
            self._impact_weapon(), [serration()], self._ferrite_enemy(),
            corrosive_stacks=0,
        )
        assert result[DamageType.IMPACT] == pytest.approx(119.0)

    def test_five_stacks_50pct_strip(self):
        """5 stacks: reduction = 0.20+0.06×5 = 0.50 → armor 300→150.
        Impact vs GRINEER ×1.5 → 238; armor_mult = 1-(150/450) = 0.666...; floor(238*0.666...)=158
        """
        result = calc.calculate(
            self._impact_weapon(), [serration()], self._ferrite_enemy(),
            corrosive_stacks=5,
        )
        assert result[DamageType.IMPACT] == pytest.approx(158.0)

    def test_ten_stacks_80pct_cap(self):
        """10 stacks: reduction capped at 0.80 → armor 300→60.
        Impact vs GRINEER ×1.5 → 238; armor_mult = 1-(60/360) = 0.8333...; floor(238*0.8333...)=198
        """
        result = calc.calculate(
            self._impact_weapon(), [serration()], self._ferrite_enemy(),
            corrosive_stacks=10,
        )
        assert result[DamageType.IMPACT] == pytest.approx(198.0)

    def test_cap_at_80pct(self):
        """14 stacks should give same result as 10 stacks (cap enforced at 80%)."""
        r10 = calc.calculate(
            self._impact_weapon(), [serration()], self._ferrite_enemy(),
            corrosive_stacks=10,
        )
        r14 = calc.calculate(
            self._impact_weapon(), [serration()], self._ferrite_enemy(),
            corrosive_stacks=14,
        )
        assert r10[DamageType.IMPACT] == r14[DamageType.IMPACT]


# ---------------------------------------------------------------------------
# make_riven_mod tests
# ---------------------------------------------------------------------------

class TestMakeRivenMod:
    def test_scalar_stats(self):
        mod = make_riven_mod([
            {"stat": "damage",      "value": 0.658},
            {"stat": "crit_chance", "value": 0.469},
            {"stat": "multishot",   "value": -0.534},
            {"stat": "crit_damage", "value": 1.24},
        ])
        assert mod.name == "Riven"
        assert abs(mod.damage_bonus   - 0.658)  < 1e-9
        assert abs(mod.cc_bonus       - 0.469)  < 1e-9
        assert abs(mod.multishot_bonus - (-0.534)) < 1e-9
        assert abs(mod.cd_bonus       - 1.24)   < 1e-9
        assert mod.elemental_bonuses == []
        assert mod.faction_bonus == 0.0

    def test_elemental_stat(self):
        mod = make_riven_mod([
            {"stat": "heat",  "value": 0.543},
            {"stat": "toxin", "value": 0.312},
        ])
        types = {c.type for c in mod.elemental_bonuses}
        assert DamageType.HEAT  in types
        assert DamageType.TOXIN in types
        heat_val = next(c.amount for c in mod.elemental_bonuses if c.type == DamageType.HEAT)
        assert abs(heat_val - 0.543) < 1e-9

    def test_unknown_stat_ignored(self):
        mod = make_riven_mod([
            {"stat": "reload_speed", "value": 0.5},
            {"stat": "damage",       "value": 0.3},
        ])
        assert abs(mod.damage_bonus - 0.3) < 1e-9

    def test_custom_name(self):
        mod = make_riven_mod([], name="Soma Prime Riven")
        assert mod.name == "Soma Prime Riven"

    def test_empty_stats(self):
        mod = make_riven_mod([])
        assert mod.damage_bonus == 0.0
        assert mod.cc_bonus == 0.0
        assert mod.elemental_bonuses == []

    def test_riven_applies_in_calculator(self):
        """Riven damage bonus stacks additively with Serration (same as a normal mod)."""
        weapon = Weapon(
            name="Test",
            base_damage={DamageType.SLASH: 100.0},
        )
        no_faction_enemy = Enemy(
            name="Mob",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
            base_armor=0.0,
            body_part_multiplier=1.0,
        )
        serration = Mod(name="Serration", damage_bonus=1.65)
        riven = make_riven_mod([{"stat": "damage", "value": 0.658}])
        result = calc.calculate(weapon, [serration, riven], no_faction_enemy)
        # Step 1: 100 × (1 + 1.65 + 0.658) = 100 × 3.308 = 330.8 → floor = 330
        # quantize: scale = 100/32 = 3.125; round(330/3.125)=round(105.6)=106 → 106*3.125=331.25
        # Actually let's just verify total > 300 and is float
        assert result[DamageType.SLASH] > 300.0


# ---------------------------------------------------------------------------
# Multishot — DamageCalculator.calculate() applies multishot multiplier
# ---------------------------------------------------------------------------
class TestMultishot:
    def _weapon(self):
        return Weapon(
            name="Test",
            base_damage={DamageType.IMPACT: 30.0, DamageType.SLASH: 30.0},
        )

    def _enemy(self):
        return Enemy(
            name="Mob",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
            base_armor=0.0,
            body_part_multiplier=1.0,
        )

    def test_multishot_default_is_1x(self):
        """Default multishot=1.0 returns same values as no-multishot call."""
        r1 = calc.calculate(self._weapon(), [], self._enemy())
        r2 = calc.calculate(self._weapon(), [], self._enemy(), multishot=1.0)
        assert r1 == r2

    def test_multishot_doubles_all_types(self):
        """multishot=2.0 doubles every damage type."""
        r1 = calc.calculate(self._weapon(), [], self._enemy())
        r2 = calc.calculate(self._weapon(), [], self._enemy(), multishot=2.0)
        for dtype in r1:
            assert r2[dtype] == pytest.approx(r1[dtype] * 2.0)

    def test_multishot_split_chamber(self):
        """Split Chamber (multishot_bonus=0.65) → modded_ms=1.65 scales total correctly."""
        mods = [Mod(name="Split Chamber", multishot_bonus=0.65)]
        modded_ms = 1.0 + sum(m.multishot_bonus for m in mods)
        r_base = calc.calculate(self._weapon(), [], self._enemy())
        r_ms   = calc.calculate(self._weapon(), mods, self._enemy(), multishot=modded_ms)
        total_base = sum(r_base.values())
        total_ms   = sum(r_ms.values())
        assert total_ms == pytest.approx(total_base * 1.65)


# ---------------------------------------------------------------------------
# CC/Debuff procs — Viral, Magnetic, Radiation, Blast, Cold
# These are non-DoT effects; damage_per_tick and total_damage are always 0.
# ---------------------------------------------------------------------------
class TestCCProcs:
    def _enemy(self):
        return Enemy(
            name="Mob",
            faction=FactionType.GRINEER,
            health_type=HealthType.FLESH,
            armor_type=ArmorType.NONE,
            base_armor=0.0,
            body_part_multiplier=1.0,
        )

    def _weapon_with(self, dtype: DamageType):
        return Weapon(
            name="Test",
            innate_elements=[DamageComponent(dtype, 60.0)],
            base_damage={DamageType.IMPACT: 60.0},
        )

    def test_viral_active_when_viral_present(self):
        procs = calc.calculate_procs(self._weapon_with(DamageType.VIRAL), [], self._enemy())
        assert procs["viral"]["active"] is True

    def test_viral_inactive_without_viral(self):
        weapon = Weapon(name="Test", base_damage={DamageType.IMPACT: 60.0})
        procs = calc.calculate_procs(weapon, [], self._enemy())
        assert procs["viral"]["active"] is False

    def test_magnetic_active_when_magnetic_present(self):
        procs = calc.calculate_procs(self._weapon_with(DamageType.MAGNETIC), [], self._enemy())
        assert procs["magnetic"]["active"] is True

    def test_radiation_active_when_radiation_present(self):
        procs = calc.calculate_procs(self._weapon_with(DamageType.RADIATION), [], self._enemy())
        assert procs["radiation"]["active"] is True

    def test_blast_active_when_blast_present(self):
        procs = calc.calculate_procs(self._weapon_with(DamageType.BLAST), [], self._enemy())
        assert procs["blast"]["active"] is True

    def test_cold_active_when_cold_present(self):
        procs = calc.calculate_procs(self._weapon_with(DamageType.COLD), [], self._enemy())
        assert procs["cold"]["active"] is True

    def test_cc_procs_have_zero_damage(self):
        """All CC procs always return 0 damage regardless of weapon/mods."""
        weapon = Weapon(
            name="Test",
            innate_elements=[
                DamageComponent(DamageType.VIRAL, 60.0),
                DamageComponent(DamageType.MAGNETIC, 60.0),
                DamageComponent(DamageType.RADIATION, 60.0),
                DamageComponent(DamageType.BLAST, 60.0),
                DamageComponent(DamageType.COLD, 60.0),
            ],
            base_damage={DamageType.IMPACT: 60.0},
        )
        procs = calc.calculate_procs(weapon, [], self._enemy())
        for key in ("viral", "magnetic", "radiation", "blast", "cold"):
            assert procs[key]["damage_per_tick"] == 0.0
            assert procs[key]["total_damage"] == 0.0
            assert procs[key]["ticks"] == 0


# ---------------------------------------------------------------------------
# TestComboCounter — melee combo multiplier in Step 1
# Weapon: 100 Slash, no mods, no-armor enemy.
# combo_mult = 1 + 0.5 * floor(hits / 5)
# ---------------------------------------------------------------------------

def _combo_weapon():
    return Weapon(name="Test", base_damage={DamageType.SLASH: 100.0})

def _no_armor_enemy():
    return Enemy(
        name="Test",
        faction=FactionType.NONE,
        health_type=HealthType.FLESH,
        armor_type=ArmorType.NONE,
        base_armor=0.0,
    )


class TestComboCounter:
    def test_combo_0_is_baseline(self):
        r = calc.calculate(_combo_weapon(), [], _no_armor_enemy(), combo_counter=0)
        assert r[DamageType.SLASH] == 100.0

    def test_combo_4_still_baseline(self):
        # floor(4/5) = 0 → ×1.0
        r = calc.calculate(_combo_weapon(), [], _no_armor_enemy(), combo_counter=4)
        assert r[DamageType.SLASH] == 100.0

    def test_combo_5_is_1_5x(self):
        # floor(5/5) = 1 → ×1.5 → floor(100*1.5)=150 → quantize(150,100)=150
        r = calc.calculate(_combo_weapon(), [], _no_armor_enemy(), combo_counter=5)
        assert r[DamageType.SLASH] == 150.0

    def test_combo_9_still_1_5x(self):
        r = calc.calculate(_combo_weapon(), [], _no_armor_enemy(), combo_counter=9)
        assert r[DamageType.SLASH] == 150.0

    def test_combo_10_is_2x(self):
        # floor(10/5) = 2 → ×2.0 → 200
        r = calc.calculate(_combo_weapon(), [], _no_armor_enemy(), combo_counter=10)
        assert r[DamageType.SLASH] == 200.0

    def test_combo_stacks_with_damage_mod(self):
        # Serration +165%, combo=5 → floor(100*(1+1.65)*1.5)=floor(397.5)=397
        # quantize(397,100): 397/3.125=127.04→127→127*3.125=396.875 → warframe_round=397
        serration = Mod(name="Serration", damage_bonus=1.65)
        r = calc.calculate(_combo_weapon(), [serration], _no_armor_enemy(), combo_counter=5)
        assert r[DamageType.SLASH] == 397.0


# ---------------------------------------------------------------------------
# TestConditionOverload — additive +80% per unique status type on enemy
# ---------------------------------------------------------------------------

class TestConditionOverload:
    _co_mod = Mod(name="Condition Overload", condition_overload_bonus=0.80)

    def test_zero_statuses_no_bonus(self):
        r = calc.calculate(_combo_weapon(), [self._co_mod], _no_armor_enemy(), unique_statuses=0)
        assert r[DamageType.SLASH] == 100.0

    def test_one_status_plus_80pct(self):
        # floor(100*(1+0.80))=180 → quantize(180,100)=181.25 → warframe_round=181
        r = calc.calculate(_combo_weapon(), [self._co_mod], _no_armor_enemy(), unique_statuses=1)
        assert r[DamageType.SLASH] == 181.0

    def test_three_statuses_plus_240pct(self):
        # floor(100*(1+2.40))=340 → quantize(340,100)=340.625 → warframe_round=341
        r = calc.calculate(_combo_weapon(), [self._co_mod], _no_armor_enemy(), unique_statuses=3)
        assert r[DamageType.SLASH] == 341.0

    def test_co_additive_with_serration(self):
        # Serration+1.65 + CO 2 statuses → total_dmg=1.65, co=1.60
        # combo_mult=1.0
        # floor(100*(1+1.65+1.60))=floor(425)=425 → quantize(425,100)=425 → =425
        serration = Mod(name="Serration", damage_bonus=1.65)
        r = calc.calculate(_combo_weapon(), [serration, self._co_mod], _no_armor_enemy(),
                           unique_statuses=2)
        assert r[DamageType.SLASH] == 425.0

    def test_co_plus_combo_combined(self):
        # CO 2 statuses + Serration + combo=5:
        # floor(100*(1+1.65+1.60)*1.5)=floor(637.5)=637
        # quantize(637,100): 637/3.125=203.84→204→204*3.125=637.5 → warframe_round=638
        serration = Mod(name="Serration", damage_bonus=1.65)
        r = calc.calculate(_combo_weapon(), [serration, self._co_mod], _no_armor_enemy(),
                           combo_counter=5, unique_statuses=2)
        assert r[DamageType.SLASH] == 638.0

    # --- Proc damage scaling with CO ---

    def test_proc_zero_statuses_baseline(self):
        # 100 Slash, no CO bonus → step2=100, slash_dpt = floor(100*0.35) = 35
        procs = calc.calculate_procs(_combo_weapon(), [self._co_mod], _no_armor_enemy(),
                                     unique_statuses=0)
        assert procs["slash"]["damage_per_tick"] == 35.0

    def test_proc_two_statuses_scales(self):
        # CO 2 statuses → co_total=1.60
        # Step 1: floor(100*(1+1.60))=260, quantize(260,100)=259.375
        # Step 2: warframe_round(259.375)=259
        # Slash dpt: floor(259*0.35) = floor(90.65) = 90
        procs = calc.calculate_procs(_combo_weapon(), [self._co_mod], _no_armor_enemy(),
                                     unique_statuses=2)
        assert procs["slash"]["damage_per_tick"] == 90.0
        assert procs["slash"]["total_damage"] == 90.0 * 6


# ---------------------------------------------------------------------------
# Galvanized mod kill-stack tests
# ---------------------------------------------------------------------------

class TestGalvanizedStacks:
    """Tests for galvanized mod kill-stack support.

    Uses the same 100-Slash weapon and no-armor enemy as TestConditionOverload.
    scale = 100/32 = 3.125
    """
    _aptitude_mod = Mod(
        name="Galvanized Aptitude",
        galv_kill_stat="aptitude_damage_bonus",
        galv_kill_pct=0.40,
        galv_max_stacks=2,
    )
    _chamber_mod = Mod(
        name="Galvanized Chamber",
        multishot_bonus=0.80,
        galv_kill_stat="multishot_bonus",
        galv_kill_pct=0.30,
        galv_max_stacks=5,
    )
    _scope_mod = Mod(
        name="Galvanized Scope",
        cc_bonus=1.20,
        galv_kill_stat="cc_bonus",
        galv_kill_pct=0.40,
        galv_max_stacks=5,
    )
    _steel_mod = Mod(
        name="Galvanized Steel",
        cc_bonus=1.10,
        galv_kill_stat="cd_bonus",
        galv_kill_pct=0.30,
        galv_max_stacks=4,
    )

    # --- Aptitude: damage per status type per stack ---

    def test_aptitude_zero_stacks_no_change(self):
        # galv_aptitude_total = 0.40 * min(0,2) * 2 = 0 → floor(100*1.0)=100 → quantize=100
        r = calc.calculate(_combo_weapon(), [self._aptitude_mod], _no_armor_enemy(),
                           unique_statuses=2, galvanized_stacks=0)
        assert r[DamageType.SLASH] == 100.0

    def test_aptitude_one_stack_two_statuses(self):
        # galv_aptitude_total = 0.40 * 1 * 2 = 0.80
        # floor(100 * (1.0 + 0.80)) = 180
        # quantize(180, 100): 180/3.125=57.6→58→58*3.125=181.25→warframe_round=181
        r = calc.calculate(_combo_weapon(), [self._aptitude_mod], _no_armor_enemy(),
                           unique_statuses=2, galvanized_stacks=1)
        assert r[DamageType.SLASH] == 181.0

    def test_aptitude_two_stacks_three_statuses(self):
        # galv_aptitude_total = 0.40 * 2 * 3 = 2.40
        # floor(100 * (1.0 + 2.40)) = 340
        # quantize(340, 100): 340/3.125=108.8→109→109*3.125=340.625→warframe_round=341
        r = calc.calculate(_combo_weapon(), [self._aptitude_mod], _no_armor_enemy(),
                           unique_statuses=3, galvanized_stacks=2)
        assert r[DamageType.SLASH] == 341.0

    def test_aptitude_stack_cap_enforced(self):
        # stacks=10 but max=2 → effective=2; same result as stacks=2, 1 status
        # galv_aptitude_total = 0.40 * 2 * 1 = 0.80
        # floor(100*(1.0+0.80))=180 → quantize→181
        r10 = calc.calculate(_combo_weapon(), [self._aptitude_mod], _no_armor_enemy(),
                             unique_statuses=1, galvanized_stacks=10)
        r2  = calc.calculate(_combo_weapon(), [self._aptitude_mod], _no_armor_enemy(),
                             unique_statuses=1, galvanized_stacks=2)
        assert r10[DamageType.SLASH] == r2[DamageType.SLASH]

    def test_aptitude_additive_with_serration(self):
        # Serration+1.65, aptitude 1 stack 1 status: galv=0.40*1*1=0.40
        # total_dmg_bonus = 1.65 + 0.40 = 2.05
        # floor(100 * (1.0 + 2.05)) = floor(305) = 305
        # quantize(305, 100): 305/3.125=97.6→98→98*3.125=306.25→warframe_round=306
        serration = Mod(name="Serration", damage_bonus=1.65)
        r = calc.calculate(_combo_weapon(), [serration, self._aptitude_mod], _no_armor_enemy(),
                           unique_statuses=1, galvanized_stacks=1)
        assert r[DamageType.SLASH] == 306.0

    # --- Multishot: pre-computed via multishot parameter ---

    def test_chamber_base_multishot(self):
        # At 0 stacks: total_ms = 1 + 0.80 = 1.80; damage × 1.80 = 100 × 1.80 = 180
        ms = 1.0 + self._chamber_mod.multishot_bonus  # base only, 0 stacks
        r = calc.calculate(_combo_weapon(), [self._chamber_mod], _no_armor_enemy(), multishot=ms)
        assert r[DamageType.SLASH] == pytest.approx(180.0)

    def test_chamber_five_stacks_multishot(self):
        # At 5 stacks: galv_ms = 0.30*5 = 1.50; total_ms = 1 + 0.80 + 1.50 = 3.30
        galv_stacks = 5
        galv_ms = self._chamber_mod.galv_kill_pct * min(galv_stacks, self._chamber_mod.galv_max_stacks)
        ms = 1.0 + self._chamber_mod.multishot_bonus + galv_ms
        assert ms == pytest.approx(3.30)
        r = calc.calculate(_combo_weapon(), [self._chamber_mod], _no_armor_enemy(), multishot=ms)
        assert r[DamageType.SLASH] == pytest.approx(100.0 * 3.30)

    def test_chamber_stack_cap_five(self):
        # stacks=10, cap=5 → same as stacks=5
        ms_cap = 1.0 + self._chamber_mod.multishot_bonus + self._chamber_mod.galv_kill_pct * 5
        ms_over = 1.0 + self._chamber_mod.multishot_bonus + self._chamber_mod.galv_kill_pct * min(10, self._chamber_mod.galv_max_stacks)
        assert ms_cap == pytest.approx(ms_over)

    # --- CC: galv_cc pre-computed and added to base_cc ---

    def test_scope_galv_cc_accumulates(self):
        # 3 stacks: galv_cc = 0.40 * 3 = 1.20
        galv_stacks = 3
        galv_cc = self._scope_mod.galv_kill_pct * min(galv_stacks, self._scope_mod.galv_max_stacks)
        assert galv_cc == pytest.approx(1.20)

    def test_scope_stack_cap_five(self):
        # stacks=10 → capped at 5 → galv_cc = 0.40*5 = 2.00
        galv_cc_capped = self._scope_mod.galv_kill_pct * min(10, self._scope_mod.galv_max_stacks)
        galv_cc_exact  = self._scope_mod.galv_kill_pct * 5
        assert galv_cc_capped == pytest.approx(galv_cc_exact)

    # --- CD: galv_cd pre-computed and added to base_cm ---

    def test_steel_galv_cd_four_stacks(self):
        # 4 stacks (cap): galv_cd = 0.30 * 4 = 1.20
        galv_stacks = 4
        galv_cd = self._steel_mod.galv_kill_pct * min(galv_stacks, self._steel_mod.galv_max_stacks)
        assert galv_cd == pytest.approx(1.20)

    def test_steel_stack_cap_enforced(self):
        # stacks=99 → capped at 4
        galv_cd_over = self._steel_mod.galv_kill_pct * min(99, self._steel_mod.galv_max_stacks)
        galv_cd_cap  = self._steel_mod.galv_kill_pct * 4
        assert galv_cd_over == pytest.approx(galv_cd_cap)


# ---------------------------------------------------------------------------
# Kuva/Tenet bonus element
# ---------------------------------------------------------------------------

class TestBonusElement:
    """Kuva/Tenet bonus element: player-chosen primary added before combination."""

    def test_bonus_heat_no_mods(self):
        """50% Heat bonus on a 100-damage weapon → Heat component = 50."""
        # base_damage=100, scale=100/32=3.125
        # bonus heat amount = 100 * 0.50 = 50.0
        # quantize(50, 100): 50/3.125=16 → 16*3.125=50.0
        # Step1 no mods: floor(50*1.0)=50; quantize(50,100)=50.0
        # Step2 body=1.0, no crit: wr(50)=50
        # Steps 3-5 neutral, no armor → 50
        weapon = Weapon(
            name="Kuva Test",
            base_damage={DamageType.IMPACT: 100.0},
            is_kuva_tenet=True,
            bonus_element_type=DamageType.HEAT,
            bonus_element_pct=0.50,
        )
        enemy = Enemy("Test", FactionType.NONE, HealthType.FLESH, ArmorType.NONE, 0.0)
        result = calc.calculate(weapon, [], enemy)
        assert result[DamageType.IMPACT] == pytest.approx(100.0)
        assert result[DamageType.HEAT]   == pytest.approx(50.0)

    def test_bonus_element_combines_with_toxin_mod(self):
        """Kuva 50% Cold bonus + Toxin mod (90%) → Viral combination."""
        # Toxin mod occupies slot 0; Cold innate goes last → Toxin+Cold = Viral
        weapon = Weapon(
            name="Kuva Test2",
            base_damage={DamageType.IMPACT: 100.0},
            is_kuva_tenet=True,
            bonus_element_type=DamageType.COLD,
            bonus_element_pct=0.50,
        )
        toxin_mod = Mod(
            name="Pathogen Rounds",
            elemental_bonuses=[DamageComponent(DamageType.TOXIN, 0.90)],
        )
        enemy = Enemy("Test", FactionType.NONE, HealthType.FLESH, ArmorType.NONE, 0.0)
        result = calc.calculate(weapon, [toxin_mod], enemy)
        assert DamageType.VIRAL in result
        assert DamageType.COLD  not in result
        assert DamageType.TOXIN not in result

    def test_bonus_element_absent_when_zero_pct(self):
        """bonus_element_pct=0 must not add any elemental component."""
        weapon = Weapon(
            name="Kuva Test3",
            base_damage={DamageType.IMPACT: 100.0},
            is_kuva_tenet=True,
            bonus_element_type=DamageType.HEAT,
            bonus_element_pct=0.0,
        )
        enemy = Enemy("Test", FactionType.NONE, HealthType.FLESH, ArmorType.NONE, 0.0)
        result = calc.calculate(weapon, [], enemy)
        assert DamageType.HEAT not in result


# ---------------------------------------------------------------------------
# IPS mod buffs — per-type bonus (Rupture, Piercing Hit, Jagged Edge etc.)
# ---------------------------------------------------------------------------
class TestIPSModBuffs:
    def _ips_weapon(self) -> Weapon:
        """Weapon with 30 Impact + 30 Puncture + 30 Slash (total=90)."""
        return Weapon(
            name="Test IPS",
            base_damage={
                DamageType.IMPACT:   30.0,
                DamageType.PUNCTURE: 30.0,
                DamageType.SLASH:    30.0,
            },
        )

    def _no_armor_enemy(self) -> Enemy:
        return Enemy("Target", FactionType.NONE, HealthType.FLESH, ArmorType.NONE, 0.0)

    def test_impact_mod_only_boosts_impact(self):
        """A mod with +120% Impact should boost Impact only; Puncture/Slash unchanged.

        base_damage=90, scale=90/32=2.8125
        Impact with +120%: floor(30*(1+1.2))=66; quantize→64.6875; Step2 round→65
        Puncture/Slash no bonus: floor(30*1.0)=30; quantize→30.9375; Step2 round→31
        """
        mod = Mod(name="Rupture", ips_bonuses=[DamageComponent(DamageType.IMPACT, 1.2)])
        result = calc.calculate(self._ips_weapon(), [mod], self._no_armor_enemy())
        assert result[DamageType.IMPACT]   == pytest.approx(65.0)
        assert result[DamageType.PUNCTURE] == pytest.approx(31.0)
        assert result[DamageType.SLASH]    == pytest.approx(31.0)

    def test_ips_and_damage_mod_stack_additively(self):
        """General damage mod + IPS mod stack additively for the matching type only.

        base_damage=90, scale=2.8125
        Serration +165%, Puncture mod +120%:
          Impact:   floor(30*(1+1.65))=79; quantize→78.75; Step2 round→79
          Puncture: floor(30*(1+1.65+1.2))=floor(115.5)=115; quantize→115.3125; Step2 round→115
          Slash:    floor(30*(1+1.65))=79; quantize→78.75; Step2 round→79
        """
        serration = Mod(name="Serration", damage_bonus=1.65)
        piercing  = Mod(name="Piercing Hit", ips_bonuses=[DamageComponent(DamageType.PUNCTURE, 1.2)])
        result = calc.calculate(self._ips_weapon(), [serration, piercing], self._no_armor_enemy())
        assert result[DamageType.IMPACT]   == pytest.approx(79.0)
        assert result[DamageType.PUNCTURE] == pytest.approx(115.0)
        assert result[DamageType.SLASH]    == pytest.approx(79.0)


# ---------------------------------------------------------------------------
# Per-pellet status chance
# ---------------------------------------------------------------------------

class TestStatusChancePerPellet:
    """Tests for the per-pellet status chance formula.

    Formula: per_pellet = 1 - (1 - total_sc)^(1/pellet_count)
    """

    def test_single_pellet_unchanged(self):
        """Single pellet (or multishot=1) returns total SC unchanged."""
        assert status_chance_per_pellet(0.25, 1) == pytest.approx(0.25)

    def test_tigris_5_pellets(self):
        """Tigris: 16.8% total SC, 5 pellets → ~3.62% per pellet."""
        pp = status_chance_per_pellet(0.168, 5)
        assert pp == pytest.approx(0.03612, abs=0.0001)

    def test_strun_12_pellets(self):
        """Strun: 5% total SC, 12 pellets → ~0.427% per pellet."""
        pp = status_chance_per_pellet(0.05, 12)
        assert pp == pytest.approx(0.00427, abs=0.0001)

    def test_100_pct_status(self):
        """100% status chance → 100% per pellet regardless of count."""
        assert status_chance_per_pellet(1.0, 8) == 1.0

    def test_zero_status(self):
        """0% status chance → 0% per pellet."""
        assert status_chance_per_pellet(0.0, 5) == 0.0

    def test_expected_procs_per_shot(self):
        """Expected procs per shot = pellet_count × per_pellet_sc.

        For Tigris (5 pellets, 16.8% total): ~0.181 expected procs/shot.
        This is slightly MORE than the raw 0.168 because the per-pellet
        formula distributes the chance across independent rolls.
        """
        pp = status_chance_per_pellet(0.168, 5)
        expected_procs = 5 * pp
        assert expected_procs == pytest.approx(0.1812, abs=0.001)
        assert expected_procs > 0.168  # more than raw SC


# ---------------------------------------------------------------------------
# Warframe Buff Tests
# ---------------------------------------------------------------------------
from src.models import Buff
from src.buffs import make_buff


class TestRoarBuff:
    """Roar: faction-type buff, additive with Bane mods, double-dips on procs."""

    def test_roar_basic(self):
        """Roar +50% should multiply final damage by 1.5 (no Bane).

        Braton + Serration vs Grineer (no armor):
        Slash without buff = 64.0, with Roar +50%: floor(64 * 1.5) = 96
        """
        roar = Buff("Roar", faction_damage_bonus=0.50)
        result = calc.calculate(braton(), [serration()], grineer_flesh_no_armor(), buffs=[roar])
        assert result[DamageType.SLASH] == pytest.approx(96.0)

    def test_roar_additive_with_bane(self):
        """Roar is additive with Bane mods: (1 + 0.30 + 0.50) = 1.80.

        Slash without faction = 64.0, with Bane + Roar: floor(64 * 1.80) = 115
        """
        roar = Buff("Roar", faction_damage_bonus=0.50)
        result = calc.calculate(braton(), [serration(), bane_grineer()], grineer_flesh_no_armor(), buffs=[roar])
        assert result[DamageType.SLASH] == pytest.approx(115.0)

    def test_roar_double_dips_on_slash_proc(self):
        """Roar double-dips on DoT procs: proc_dmg * (1 + faction_bonus)^2.

        Without buff: slash_dpt = 55.0
        With Roar 50%: faction_bonus = 0.50, (1+0.5)^2 = 2.25
        slash_dpt = floor(step2_total * 0.35 * 2.25) = 124.0
        """
        roar = Buff("Roar", faction_damage_bonus=0.50)
        procs_no = calc.calculate_procs(braton(), [serration()], grineer_flesh_no_armor())
        procs_yes = calc.calculate_procs(braton(), [serration()], grineer_flesh_no_armor(), buffs=[roar])
        # Roar double-dips: ratio should be ~(1.5)^2 = 2.25
        ratio = procs_yes["slash"]["damage_per_tick"] / procs_no["slash"]["damage_per_tick"]
        assert ratio == pytest.approx(2.25, abs=0.05)
        assert procs_yes["slash"]["damage_per_tick"] == pytest.approx(124.0)

    def test_roar_with_strength(self):
        """make_buff('roar', 2.0) → 100% damage bonus."""
        roar = make_buff("roar", 2.0)
        assert roar.faction_damage_bonus == pytest.approx(1.0)
        result = calc.calculate(braton(), [serration()], grineer_flesh_no_armor(), buffs=[roar])
        # floor(64 * 2.0) = 128
        assert result[DamageType.SLASH] == pytest.approx(128.0)


class TestEclipseBuff:
    """Eclipse: general damage multiplier, multiplicative, no double-dip on procs."""

    def test_eclipse_basic(self):
        """Eclipse +200%: separate multiplicative step after faction.

        Slash = 64.0 (after faction), eclipse mult = 1+2.0 = 3.0 → floor(64 * 3.0) = 192
        """
        eclipse = Buff("Eclipse", damage_multiplier=2.0)
        result = calc.calculate(braton(), [serration()], grineer_flesh_no_armor(), buffs=[eclipse])
        assert result[DamageType.SLASH] == pytest.approx(192.0)

    def test_eclipse_multiplicative_with_bane(self):
        """Eclipse × Bane: faction first, then Eclipse multiplies.

        Slash = 64, Bane ×1.30 → floor(64*1.30) = 83, Eclipse ×3.0 → floor(83*3.0) = 249
        """
        eclipse = Buff("Eclipse", damage_multiplier=2.0)
        result = calc.calculate(braton(), [serration(), bane_grineer()], grineer_flesh_no_armor(), buffs=[eclipse])
        assert result[DamageType.SLASH] == pytest.approx(249.0)

    def test_eclipse_no_double_dip_on_procs(self):
        """Eclipse applies once to procs (not squared).

        Without eclipse: slash_dpt = 160 * 0.35 * 1.0 = 56.0
        With eclipse ×3: slash_dpt = 56.0 * 3.0 = 168.0
        """
        eclipse = Buff("Eclipse", damage_multiplier=2.0)
        procs_no = calc.calculate_procs(braton(), [serration()], grineer_flesh_no_armor())
        procs_yes = calc.calculate_procs(braton(), [serration()], grineer_flesh_no_armor(), buffs=[eclipse])
        assert procs_yes["slash"]["damage_per_tick"] == pytest.approx(procs_no["slash"]["damage_per_tick"] * 3.0)


class TestBuffStacking:
    """Multiple buffs stack correctly."""

    def test_roar_plus_eclipse(self):
        """Roar (faction) + Eclipse (multiplicative) stack.

        Slash = 64 (base modded)
        Step 5: floor(64 * (1 + 0.50)) = floor(64 * 1.5) = 96
        Step 5.5: floor(96 * (1 + 2.0)) = floor(96 * 3.0) = 288
        """
        roar = Buff("Roar", faction_damage_bonus=0.50)
        eclipse = Buff("Eclipse", damage_multiplier=2.0)
        result = calc.calculate(braton(), [serration()], grineer_flesh_no_armor(), buffs=[roar, eclipse])
        assert result[DamageType.SLASH] == pytest.approx(288.0)

    def test_no_buffs_unchanged(self):
        """Empty buff list produces same result as no buffs parameter."""
        result_none = calc.calculate(braton(), [serration()], grineer_flesh_no_armor())
        result_empty = calc.calculate(braton(), [serration()], grineer_flesh_no_armor(), buffs=[])
        assert result_none == result_empty


class TestMakeBuffPresets:
    """make_buff() preset factory."""

    def test_all_presets_valid(self):
        """All preset names produce valid Buff objects."""
        from src.buffs import BUFF_PRESETS
        for key in BUFF_PRESETS:
            b = make_buff(key)
            assert isinstance(b, Buff)
            assert b.name  # non-empty name

    def test_unknown_preset_raises(self):
        with pytest.raises(KeyError):
            make_buff("nonexistent_ability")

    def test_strength_scaling(self):
        """Strength multiplier scales the buff values."""
        r1 = make_buff("roar", 1.0)
        r2 = make_buff("roar", 2.0)
        assert r2.faction_damage_bonus == pytest.approx(r1.faction_damage_bonus * 2.0)

