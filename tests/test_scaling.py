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
    def test_level_1_base_value(self):
        # δ_OG = 0 → f1 = 1 + 0.0015*0^4 = 1 → 12 * 1 = 12
        assert overguard_at_level(1) == pytest.approx(12.0)

    def test_level_11(self):
        # δ_OG = 10 → f1 = 1 + 0.0015*10^4 = 1 + 15 = 16 → 12*16 = 192
        # (CLAUDE.md listed 1812 which was from the old power-law fit — incorrect)
        assert overguard_at_level(11) == pytest.approx(192.0)

    def test_level_46(self):
        # δ_OG = 45 → f1 = 1 + 0.0015*45^4 = 6151.9375 → 12*6151.9375 = 73823.25
        assert overguard_at_level(46) == pytest.approx(73823.25)

    def test_level_51_uses_f2(self):
        # δ_OG = 50 → fully f2 territory: 1 + 260*50^0.9
        import math
        d = 50.0
        expected = 12.0 * (1.0 + 260.0 * d ** 0.9)
        assert overguard_at_level(51) == pytest.approx(expected, rel=1e-6)

    def test_level_200_reference(self):
        # δ_OG=199 → ~365,676 per CLAUDE.md
        assert overguard_at_level(200) == pytest.approx(365676.0, rel=0.01)

    def test_level_600_reference(self):
        # δ_OG=599 → ~985,000 per CLAUDE.md
        assert overguard_at_level(600) == pytest.approx(985000.0, rel=0.01)

    def test_increases_monotonically(self):
        levels = [1, 10, 25, 45, 48, 50, 100, 200]
        values = [overguard_at_level(lv) for lv in levels]
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
