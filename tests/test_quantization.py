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
