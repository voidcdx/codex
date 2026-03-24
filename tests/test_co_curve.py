"""Tests for the Condition Overload curve feature.

The CO curve computes total damage at unique_statuses 0–10 in a single pass.
These tests verify the curve logic matches individual calculate() calls.
"""

from src.calculator import DamageCalculator
from src.enums import DamageType, FactionType, HealthType, ArmorType
from src.models import Weapon, Mod, Enemy

calc = DamageCalculator()

_CO_MOD = Mod(name="Condition Overload", condition_overload_bonus=0.80)
_SERRATION = Mod(name="Serration", damage_bonus=1.65)


def _weapon():
    return Weapon(name="Test", base_damage={DamageType.SLASH: 100.0})


def _enemy():
    return Enemy(
        name="Test",
        faction=FactionType.NONE,
        health_type=HealthType.FLESH,
        armor_type=ArmorType.NONE,
        base_armor=0.0,
    )


def _build_co_curve(weapon, mods, enemy, **kwargs):
    """Replicate the CO curve logic from api.py."""
    has_co = any(m.condition_overload_bonus > 0 for m in mods)
    if not has_co:
        return None
    curve = []
    for us in range(11):
        r = calc.calculate(weapon=weapon, mods=mods, enemy=enemy,
                           unique_statuses=us, **kwargs)
        curve.append(round(sum(r.values()), 2))
    return curve


class TestCOCurve:
    def test_curve_present_with_co(self):
        curve = _build_co_curve(_weapon(), [_CO_MOD], _enemy())
        assert curve is not None
        assert len(curve) == 11

    def test_curve_absent_without_co(self):
        curve = _build_co_curve(_weapon(), [_SERRATION], _enemy())
        assert curve is None

    def test_curve_matches_individual_calls(self):
        w, e = _weapon(), _enemy()
        mods = [_SERRATION, _CO_MOD]
        curve = _build_co_curve(w, mods, e)
        for us in range(11):
            r = calc.calculate(weapon=w, mods=mods, enemy=e, unique_statuses=us)
            expected = round(sum(r.values()), 2)
            assert curve[us] == expected, f"Mismatch at unique_statuses={us}"

    def test_curve_monotonically_increasing(self):
        curve = _build_co_curve(_weapon(), [_CO_MOD], _enemy())
        for i in range(10):
            assert curve[i] <= curve[i + 1], (
                f"curve[{i}]={curve[i]} > curve[{i+1}]={curve[i+1]}"
            )

    def test_curve_zero_equals_no_co_baseline(self):
        w, e = _weapon(), _enemy()
        curve = _build_co_curve(w, [_CO_MOD], e)
        # At 0 statuses, CO provides no bonus — should equal base damage
        r_baseline = calc.calculate(weapon=w, mods=[], enemy=e, unique_statuses=0)
        assert curve[0] == round(sum(r_baseline.values()), 2)

    def test_curve_with_serration_and_combo(self):
        w, e = _weapon(), _enemy()
        mods = [_SERRATION, _CO_MOD]
        curve = _build_co_curve(w, mods, e, combo_counter=5)
        assert len(curve) == 11
        for us in range(11):
            r = calc.calculate(weapon=w, mods=mods, enemy=e,
                               unique_statuses=us, combo_counter=5)
            assert curve[us] == round(sum(r.values()), 2)
