"""M2 + M3 — quantize() and quantize_components() tests.

Wiki reference: Damage/Calculation page example
  base_damage = 100, scale = 100/32 = 3.125
  Impact  30 → round(9.6)  = 10 → 10 * 3.125 = 31.25
  Puncture 35 → round(11.2) = 11 → 11 * 3.125 = 34.375
  Slash   35 → round(11.2) = 11 → 11 * 3.125 = 34.375
"""
import pytest
from src.quantizer import quantize, quantize_components
from src.models import DamageComponent
from src.enums import DamageType


class TestQuantize:
    def test_impact_wiki_example(self):
        assert quantize(30.0, 100.0) == pytest.approx(31.25)

    def test_puncture_wiki_example(self):
        assert quantize(35.0, 100.0) == pytest.approx(34.375)

    def test_slash_wiki_example(self):
        assert quantize(35.0, 100.0) == pytest.approx(34.375)

    def test_rounds_down_when_below_half(self):
        # 0.5 / 3.125 = 0.16 → round to 0 → 0.0
        assert quantize(0.5, 100.0) == pytest.approx(0.0)

    def test_zero_base_damage_returns_zero(self):
        assert quantize(50.0, 0.0) == 0.0

    def test_exact_multiple_unchanged(self):
        # 31.25 is already on the grid
        assert quantize(31.25, 100.0) == pytest.approx(31.25)

    def test_scale_reflects_base_damage(self):
        # base=64 → scale=2.0; 30 → round(15.0)*2 = 30.0
        assert quantize(30.0, 64.0) == pytest.approx(30.0)


class TestQuantizeComponents:
    BASE = 100.0

    def test_full_ips_wiki_example(self):
        components = [
            DamageComponent(DamageType.IMPACT, 30.0),
            DamageComponent(DamageType.PUNCTURE, 35.0),
            DamageComponent(DamageType.SLASH, 35.0),
        ]
        result = quantize_components(components, self.BASE)
        assert len(result) == 3
        assert result[0] == DamageComponent(DamageType.IMPACT, 31.25)
        assert result[1] == DamageComponent(DamageType.PUNCTURE, 34.375)
        assert result[2] == DamageComponent(DamageType.SLASH, 34.375)

    def test_zero_amount_dropped(self):
        components = [
            DamageComponent(DamageType.IMPACT, 0.4),   # rounds to 0
            DamageComponent(DamageType.SLASH, 50.0),
        ]
        result = quantize_components(components, self.BASE)
        assert len(result) == 1
        assert result[0].type == DamageType.SLASH

    def test_empty_components(self):
        assert quantize_components([], self.BASE) == []

    def test_each_type_quantized_independently(self):
        # Different types with same raw amount — each should quantize the same
        components = [
            DamageComponent(DamageType.HEAT, 10.0),
            DamageComponent(DamageType.COLD, 10.0),
        ]
        result = quantize_components(components, self.BASE)
        # 10 / 3.125 = 3.2 → round to 3 → 9.375
        assert result[0].amount == pytest.approx(9.375)
        assert result[1].amount == pytest.approx(9.375)


class TestBoundaries:
    """Verify ROUND_HALF_UP behaviour at exact 0.5 boundaries.

    With base_dmg=32, scale=1.0 — so modded/scale is always a clean .5 value,
    making it easy to confirm Banker's Rounding would fail here.
    """

    BASE = 32.0  # scale = 32/32 = 1.0

    def test_half_boundary_rounds_up(self):
        # 0.5 / 1.0 = 0.5 → ROUND_HALF_UP → 1 → 1 * 1.0 = 1.0
        # Python's round(0.5) = 0 (Banker's) — this would fail with round()
        assert quantize(0.5, self.BASE) == pytest.approx(1.0)

    def test_one_and_half_boundary_rounds_up(self):
        # 1.5 / 1.0 = 1.5 → ROUND_HALF_UP → 2 → 2.0
        # Python's round(1.5) = 2 (happens to be correct here by chance)
        assert quantize(1.5, self.BASE) == pytest.approx(2.0)

    def test_two_and_half_boundary_rounds_up(self):
        # 2.5 / 1.0 = 2.5 → ROUND_HALF_UP → 3 → 3.0
        # Python's round(2.5) = 2 (Banker's) — this would fail with round()
        assert quantize(2.5, self.BASE) == pytest.approx(3.0)

    def test_three_and_half_boundary_rounds_up(self):
        # 3.5 / 1.0 = 3.5 → ROUND_HALF_UP → 4 → 4.0
        # Python's round(3.5) = 4 (happens to be correct here by chance)
        assert quantize(3.5, self.BASE) == pytest.approx(4.0)

    def test_four_and_half_boundary_rounds_up(self):
        # 4.5 / 1.0 = 4.5 → ROUND_HALF_UP → 5 → 5.0
        # Python's round(4.5) = 4 (Banker's) — this would fail with round()
        assert quantize(4.5, self.BASE) == pytest.approx(5.0)
