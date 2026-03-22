"""Tests for src/scaling.py — enemy level scaling formulas.

Reference values from CLAUDE.md and wiki.warframe.com/w/Enemy_Level_Scaling.
"""
import pytest
from src.enums import FactionType
from src.scaling import (
    armor_at_level,
    health_multiplier,
    overguard_at_level,
    scale_enemy_stats,
    shield_multiplier,
)


# ---------------------------------------------------------------------------
# Overguard — reference values from CLAUDE.md
# ---------------------------------------------------------------------------

class TestOverguard:
    def test_delta_0_base_value(self):
        # δ=0 → f1 = 1 → 12 * 1 = 12
        assert overguard_at_level(0) == pytest.approx(12.0)

    def test_delta_10(self):
        # δ=10 → f1 = 1 + 0.0015*10^4 = 16 → 12*16 = 192
        assert overguard_at_level(10) == pytest.approx(192.0)

    def test_delta_45(self):
        # δ=45 → f1 = 1 + 0.0015*45^4 = 6151.9375 → 12*6151.9375 = 73823.25
        assert overguard_at_level(45) == pytest.approx(73823.25)

    def test_delta_50_uses_f2(self):
        # δ=50 → fully f2: 1 + 260*50^0.9
        d = 50.0
        expected = 12.0 * (1.0 + 260.0 * d ** 0.9)
        assert overguard_at_level(50) == pytest.approx(expected, rel=1e-6)

    def test_delta_199_reference(self):
        # δ=199 → ~365,676 per CLAUDE.md
        assert overguard_at_level(199) == pytest.approx(365676.0, rel=0.01)

    def test_delta_599_reference(self):
        # δ=599 → ~985,000 per CLAUDE.md
        assert overguard_at_level(599) == pytest.approx(985000.0, rel=0.01)

    def test_increases_monotonically(self):
        deltas = [0, 9, 24, 44, 47, 49, 99, 199]
        values = [overguard_at_level(d) for d in deltas]
        assert all(values[i] < values[i+1] for i in range(len(values)-1))


# ---------------------------------------------------------------------------
# Armor — two-regime smoothstep
# ---------------------------------------------------------------------------

class TestArmor:
    def test_zero_delta(self):
        assert armor_at_level(300.0, 0) == pytest.approx(300.0)

    def test_low_delta_uses_f1(self):
        # δ=50 → f1 only: 1 + 0.005*50^1.75
        expected = 300.0 * (1.0 + 0.005 * 50 ** 1.75)
        assert armor_at_level(300.0, 50) == pytest.approx(expected, rel=1e-6)

    def test_high_delta_uses_f2(self):
        # δ=100 → f2 only: 1 + 0.4*100^0.75
        expected = min(300.0 * (1.0 + 0.4 * 100 ** 0.75), 2700.0)
        assert armor_at_level(300.0, 100) == pytest.approx(expected, rel=1e-6)

    def test_hard_cap_2700(self):
        assert armor_at_level(2700.0, 500) == pytest.approx(2700.0)

    def test_zero_base_armor(self):
        assert armor_at_level(0.0, 100) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Health multiplier — faction-specific coefficients
# ---------------------------------------------------------------------------

class TestHealthMultiplier:
    def test_delta_zero_returns_one(self):
        assert health_multiplier(0, FactionType.GRINEER) == pytest.approx(1.0)

    def test_grineer_low_delta(self):
        # δ=50 → f1 = 1 + 0.015*50^2.12
        expected = 1.0 + 0.015 * 50 ** 2.12
        assert health_multiplier(50, FactionType.GRINEER) == pytest.approx(expected, rel=1e-6)

    def test_corpus_high_delta(self):
        # δ=100 → f2 = 1 + 13.4165*100^0.55
        expected = 1.0 + 13.4165 * 100 ** 0.55
        assert health_multiplier(100, FactionType.CORPUS) == pytest.approx(expected, rel=1e-6)

    def test_infested_high_delta(self):
        # δ=100 → f2 = 1 + 16.1*100^0.72
        expected = 1.0 + 16.1 * 100 ** 0.72
        assert health_multiplier(100, FactionType.INFESTED) == pytest.approx(expected, rel=1e-6)

    def test_corpus_differs_from_grineer(self):
        # Corpus f2 uses different coefficients than Grineer
        assert health_multiplier(100, FactionType.CORPUS) != health_multiplier(100, FactionType.GRINEER)

    def test_kuva_grineer_same_as_grineer(self):
        assert health_multiplier(80, FactionType.KUVA_GRINEER) == pytest.approx(
            health_multiplier(80, FactionType.GRINEER), rel=1e-9
        )

    def test_murmur_high_delta(self):
        # δ=100 → f2 = 1 + 10.7332*100^0.5
        expected = 1.0 + 10.7332 * 100 ** 0.5
        assert health_multiplier(100, FactionType.MURMUR) == pytest.approx(expected, rel=1e-6)

    def test_techrot_high_delta(self):
        # δ=100 → f2 = 1 + 15.1*100^0.7
        expected = 1.0 + 15.1 * 100 ** 0.7
        assert health_multiplier(100, FactionType.TECHROT) == pytest.approx(expected, rel=1e-6)


# ---------------------------------------------------------------------------
# Shield multiplier — separate from health
# ---------------------------------------------------------------------------

class TestShieldMultiplier:
    def test_delta_zero_returns_one(self):
        assert shield_multiplier(0, FactionType.CORPUS) == pytest.approx(1.0)

    def test_corpus_high_delta(self):
        # δ=100 → f2 = 1 + 2.0*100^0.76
        expected = 1.0 + 2.0 * 100 ** 0.76
        assert shield_multiplier(100, FactionType.CORPUS) == pytest.approx(expected, rel=1e-6)

    def test_techrot_shields_differ_from_corpus(self):
        assert shield_multiplier(100, FactionType.TECHROT) != shield_multiplier(100, FactionType.CORPUS)


# ---------------------------------------------------------------------------
# scale_enemy_stats integration
# ---------------------------------------------------------------------------

class TestScaleEnemyStats:
    def test_base_level_no_scaling(self):
        result = scale_enemy_stats(100.0, 50.0, 200.0, 10, 10, faction=FactionType.GRINEER)
        assert result["health"] == pytest.approx(100.0)
        assert result["shield"] == pytest.approx(50.0)
        assert result["overguard"] == pytest.approx(0.0)

    def test_steel_path_adds_100_and_multiplies(self):
        base = scale_enemy_stats(100.0, 50.0, 0.0, 1, 1, faction=FactionType.GRINEER)
        sp   = scale_enemy_stats(100.0, 50.0, 0.0, 1, 1, steel_path=True, faction=FactionType.GRINEER)
        assert sp["level"] == 101
        assert sp["health"] > base["health"]

    def test_eximus_has_overguard(self):
        result = scale_enemy_stats(100.0, 0.0, 0.0, 1, 1, eximus=True, faction=FactionType.GRINEER)
        assert result["overguard"] == pytest.approx(12.0)

    def test_eximus_overguard_scales_with_level(self):
        low  = scale_enemy_stats(100.0, 0.0, 0.0, 1, 11, eximus=True, faction=FactionType.GRINEER)
        high = scale_enemy_stats(100.0, 0.0, 0.0, 1, 46, eximus=True, faction=FactionType.GRINEER)
        assert high["overguard"] > low["overguard"]
        assert low["overguard"]  == pytest.approx(192.0)
        assert high["overguard"] == pytest.approx(73823.25)

    def test_armor_hard_cap(self):
        result = scale_enemy_stats(100.0, 0.0, 5000.0, 1, 9999, faction=FactionType.GRINEER)
        assert result["armor"] == pytest.approx(2700.0)

    def test_grineer_power_carrier_lv500_sp_eximus(self):
        # Reference: wiki.warframe.com — Grineer Power Carrier lv500 +SP Eximus
        # base_health=650, base_armor=100, base_level=15, faction=Grineer
        result = scale_enemy_stats(
            650.0, 0.0, 100.0, 15, 500,
            steel_path=True, eximus=True,
            faction=FactionType.GRINEER,
        )
        assert result["health"]    == pytest.approx(5_361_635.79, rel=0.001)
        assert result["armor"]     == pytest.approx(2700.0)
        assert result["overguard"] == pytest.approx(815_320.85,   rel=0.001)
