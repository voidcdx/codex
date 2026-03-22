"""Tests for src/loader.py — JSON → dataclass conversion."""
import pytest

from src.enums import ArmorType, DamageType, FactionType, HealthType
from src.loader import load_enemy, load_mod, load_weapon, list_weapons, list_mods, list_enemies


# ---------------------------------------------------------------------------
# load_weapon
# ---------------------------------------------------------------------------

class TestLoadWeapon:
    def test_soma_prime_ips(self):
        w = load_weapon("Soma Prime")
        assert DamageType.IMPACT    in w.base_damage
        assert DamageType.PUNCTURE  in w.base_damage
        assert DamageType.SLASH     in w.base_damage

    def test_soma_prime_ips_values(self):
        w = load_weapon("Soma Prime")
        assert abs(w.base_damage[DamageType.IMPACT]   - 1.2) < 1e-6
        assert abs(w.base_damage[DamageType.PUNCTURE] - 4.8) < 1e-6
        assert abs(w.base_damage[DamageType.SLASH]    - 6.0) < 1e-6

    def test_soma_prime_total_base(self):
        w = load_weapon("Soma Prime")
        assert abs(w.total_base_damage - 12.0) < 1e-6

    def test_case_insensitive_fallback(self):
        w = load_weapon("soma prime")
        assert w.name == "Soma Prime"

    def test_unknown_weapon_raises(self):
        with pytest.raises(KeyError):
            load_weapon("Nonexistent Weapon XYZ")

    def test_kuva_weapon_is_flagged(self):
        # Any Kuva weapon should have is_kuva_tenet = True
        w = load_weapon("Kuva Bramma")
        assert w.is_kuva_tenet is True

    def test_no_innate_elements_for_soma(self):
        w = load_weapon("Soma Prime")
        assert w.innate_elements == []


# ---------------------------------------------------------------------------
# load_mod
# ---------------------------------------------------------------------------

class TestLoadMod:
    def test_serration_damage_bonus(self):
        m = load_mod("Serration")
        assert abs(m.damage_bonus - 1.65) < 1e-6

    def test_serration_no_elemental(self):
        m = load_mod("Serration")
        assert m.elemental_bonuses == []

    def test_hellfire_elemental(self):
        m = load_mod("Hellfire")
        types = [c.type for c in m.elemental_bonuses]
        assert DamageType.HEAT in types

    def test_hellfire_heat_amount(self):
        m = load_mod("Hellfire")
        heat = next(c for c in m.elemental_bonuses if c.type == DamageType.HEAT)
        assert abs(heat.amount - 0.9) < 1e-6

    def test_primed_bane_corpus_faction(self):
        m = load_mod("Primed Bane of Corpus")
        assert m.faction_type == FactionType.CORPUS
        assert abs(m.faction_bonus - 0.55) < 1e-6

    def test_bane_grineer_faction(self):
        m = load_mod("Bane of Grineer")
        assert m.faction_type == FactionType.GRINEER
        assert abs(m.faction_bonus - 0.30) < 1e-6

    def test_case_insensitive_mod(self):
        m = load_mod("serration")
        assert m.name == "Serration"

    def test_unknown_mod_raises(self):
        with pytest.raises(KeyError):
            load_mod("Nonexistent Mod ABC")


# ---------------------------------------------------------------------------
# load_enemy
# ---------------------------------------------------------------------------

class TestLoadEnemy:
    def test_heavy_gunner_faction(self):
        e = load_enemy("Heavy Gunner")
        assert e.faction == FactionType.GRINEER

    def test_heavy_gunner_health_type(self):
        e = load_enemy("Heavy Gunner")
        assert e.health_type == HealthType.FLESH

    def test_heavy_gunner_armor_type(self):
        e = load_enemy("Heavy Gunner")
        assert e.armor_type == ArmorType.FERRITE

    def test_heavy_gunner_armor_value(self):
        e = load_enemy("Heavy Gunner")
        assert e.base_armor == 500.0

    def test_body_shot_multiplier_default_one(self):
        e = load_enemy("Heavy Gunner")
        assert e.body_part_multiplier == 1.0

    def test_headshot_uses_head_multiplier(self):
        e = load_enemy("Heavy Gunner", headshot=True)
        assert e.body_part_multiplier == 3.0

    def test_body_part_head_uses_head_multiplier(self):
        e = load_enemy("Heavy Gunner", body_part="Head")
        assert e.body_part_multiplier == 3.0

    def test_body_parts_dict_populated(self):
        e = load_enemy("Heavy Gunner")
        assert "Body" in e.body_parts
        assert "Head" in e.body_parts
        assert e.body_parts["Body"] == 1.0
        assert e.body_parts["Head"] == 3.0

    def test_case_insensitive_enemy(self):
        e = load_enemy("heavy gunner")
        assert e.name == "Heavy Gunner"

    def test_unknown_enemy_raises(self):
        with pytest.raises(KeyError):
            load_enemy("Nonexistent Enemy 99")

    def test_corpus_enemy_no_armor_type_none(self):
        # Corpus Crewman has no armor → ArmorType.NONE
        e = load_enemy("Crewman")
        assert e.armor_type == ArmorType.NONE

    def test_infested_enemy_health_type(self):
        e = load_enemy("Charger")
        assert e.health_type == HealthType.INFESTED_FLESH


# ---------------------------------------------------------------------------
# list functions
# ---------------------------------------------------------------------------

class TestListFunctions:
    def test_list_weapons_returns_soma_prime(self):
        names = list_weapons()
        assert "Soma Prime" in names

    def test_list_weapons_sorted(self):
        names = list_weapons()
        assert names == sorted(names)

    def test_list_mods_contains_serration(self):
        assert "Serration" in list_mods()

    def test_list_enemies_contains_heavy_gunner(self):
        assert "Heavy Gunner" in list_enemies()

    def test_list_enemies_count(self):
        # Should have a substantial enemy database
        assert len(list_enemies()) > 100
