"""
loader.py
---------
Loads weapons, mods, and enemies from the JSON data files and returns
the dataclass objects that DamageCalculator expects.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.enums import ArmorType, DamageType, FactionType, HealthType
from src.models import DamageComponent, Enemy, Mod, Weapon, WeaponAttack

DATA_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Mod family helpers
# ---------------------------------------------------------------------------

_FAMILY_PREFIXES = ("Primed ", "Umbral ", "Archon ")


def _mod_family(name: str) -> str:
    """Return the base family name for a mod (strips Primed/Umbral/Archon prefix)."""
    for prefix in _FAMILY_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


# ---------------------------------------------------------------------------
# String → Enum maps
# ---------------------------------------------------------------------------

_DAMAGE_TYPE: dict[str, DamageType] = {
    "impact":       DamageType.IMPACT,
    "puncture":     DamageType.PUNCTURE,
    "slash":        DamageType.SLASH,
    "heat":         DamageType.HEAT,
    "cold":         DamageType.COLD,
    "electricity":  DamageType.ELECTRICITY,
    "toxin":        DamageType.TOXIN,
    "blast":        DamageType.BLAST,
    "corrosive":    DamageType.CORROSIVE,
    "gas":          DamageType.GAS,
    "magnetic":     DamageType.MAGNETIC,
    "radiation":    DamageType.RADIATION,
    "viral":        DamageType.VIRAL,
    "true":         DamageType.TRUE,
    "void":         DamageType.VOID,
    "tau":          DamageType.TAU,
}

_FACTION_TYPE: dict[str, FactionType] = {
    "grineer":       FactionType.GRINEER,
    "kuva_grineer":  FactionType.KUVA_GRINEER,
    "corpus":        FactionType.CORPUS,
    "corpus_amalgam": FactionType.CORPUS_AMALGAM,
    "infested":      FactionType.INFESTED,
    "infestation":   FactionType.INFESTED,
    "deimos_infested": FactionType.DEIMOS_INFESTED,
    "corrupted":     FactionType.CORRUPTED,
    "orokin":        FactionType.CORRUPTED,
    "sentient":      FactionType.SENTIENT,
    "narmer":        FactionType.NARMER,
    "themurmur":     FactionType.MURMUR,
    "murmur":        FactionType.MURMUR,
    "zariman":       FactionType.ZARIMAN,
    "scaldra":       FactionType.SCALDRA,
    "techrot":       FactionType.TECHROT,
    "stalker":       FactionType.NONE,
    "unaffiliated":  FactionType.NONE,
    "anarchs":       FactionType.NONE,
    "none":          FactionType.NONE,
}

_HEALTH_TYPE: dict[str, HealthType] = {
    "flesh":          HealthType.FLESH,
    "robotic":        HealthType.ROBOTIC,
    "ferrite_armor":  HealthType.FERRITE_ARMOR,
    "alloy_armor":    HealthType.ALLOY_ARMOR,
    "shields":        HealthType.SHIELDS,
    "proto_shields":  HealthType.PROTO_SHIELDS,
    "infested_flesh": HealthType.INFESTED_FLESH,
    "fossilized":     HealthType.FOSSILIZED,
    "sinew":          HealthType.SINEW,
}

_ARMOR_TYPE: dict[str, ArmorType] = {
    "none":    ArmorType.NONE,
    "ferrite": ArmorType.FERRITE,
    "alloy":   ArmorType.ALLOY,
}

# Elemental field suffixes in mods.json → DamageType
_ELEM_FIELD: dict[str, DamageType] = {
    "heat_pct":        DamageType.HEAT,
    "cold_pct":        DamageType.COLD,
    "electricity_pct": DamageType.ELECTRICITY,
    "toxin_pct":       DamageType.TOXIN,
    "blast_pct":       DamageType.BLAST,
    "corrosive_pct":   DamageType.CORROSIVE,
    "gas_pct":         DamageType.GAS,
    "magnetic_pct":    DamageType.MAGNETIC,
    "radiation_pct":   DamageType.RADIATION,
    "viral_pct":       DamageType.VIRAL,
}

_IPS_FIELD: dict[str, DamageType] = {
    "impact_pct":   DamageType.IMPACT,
    "puncture_pct": DamageType.PUNCTURE,
    "slash_pct":    DamageType.SLASH,
}


# ---------------------------------------------------------------------------
# Raw JSON loaders
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _raw_weapons() -> dict[str, Any]:
    return json.loads((DATA_DIR / "weapons.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _raw_mods() -> dict[str, Any]:
    return json.loads((DATA_DIR / "mods.json").read_text(encoding="utf-8",
                                                          errors="replace"))


@lru_cache(maxsize=1)
def _raw_enemies() -> dict[str, Any]:
    return json.loads((DATA_DIR / "enemies.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _parse_weapon_attack(raw_attack: dict) -> WeaponAttack:
    """Convert a raw attack dict from weapons.json into a WeaponAttack."""
    base_dmg_raw: dict[str, float] = raw_attack.get("base_damage") or {}
    base_damage = {
        _DAMAGE_TYPE[k]: float(v)
        for k, v in base_dmg_raw.items()
        if k in _DAMAGE_TYPE
    }
    innate_elems: list[DamageComponent] = []
    for k, v in (raw_attack.get("innate_elements") or {}).items():
        dt = _DAMAGE_TYPE.get(k)
        if dt is not None:
            innate_elems.append(DamageComponent(dt, float(v)))
    return WeaponAttack(
        name=raw_attack.get("name", ""),
        base_damage=base_damage,
        innate_elements=innate_elems,
        crit_chance=float(raw_attack.get("crit_chance") or 0.0),
        crit_multiplier=float(raw_attack.get("crit_multiplier") or 1.0),
        status_chance=float(raw_attack.get("status_chance") or 0.0),
        shot_type=raw_attack.get("shot_type", ""),
        fire_rate=float(raw_attack.get("fire_rate") or 0.0),
        multishot=int(raw_attack.get("multishot") or 1),
        falloff_start=raw_attack.get("falloff_start"),
        falloff_end=raw_attack.get("falloff_end"),
        falloff_reduction=float(raw_attack.get("falloff_reduction") or 0.0),
    )


def load_weapon(name: str, attack_name: str | None = None) -> Weapon:
    """Load a weapon by exact name.

    Args:
        name:        Weapon name (case-insensitive fallback).
        attack_name: Attack mode to select (e.g. "Rocket Explosion").
                     Defaults to the first attack in the list.

    Raises KeyError if weapon or attack_name not found.
    """
    raw = _raw_weapons()
    if name not in raw:
        lower = name.lower()
        for k in raw:
            if k.lower() == lower:
                name = k
                break
        else:
            raise KeyError(f"Weapon not found: {name!r}")

    entry = raw[name]

    # Parse all attacks
    attacks_raw: list[dict] = entry.get("attacks") or []
    all_attacks = [_parse_weapon_attack(a) for a in attacks_raw]

    # Fall back to legacy flat base_damage/innate_elements if no attacks array
    if not all_attacks:
        base_dmg_raw: dict[str, float] = entry.get("base_damage") or {}
        base_damage = {
            _DAMAGE_TYPE[k]: float(v)
            for k, v in base_dmg_raw.items()
            if k in _DAMAGE_TYPE
        }
        innate_elems: list[DamageComponent] = []
        for k, v in (entry.get("innate_elements") or {}).items():
            dt = _DAMAGE_TYPE.get(k)
            if dt is not None:
                innate_elems.append(DamageComponent(dt, float(v)))
        selected_base_damage = base_damage
        selected_innate = innate_elems
        selected_cc = float(entry.get("crit_chance") or 0.0)
        selected_cm = float(entry.get("crit_multiplier") or 1.0)
        selected_sc = float(entry.get("status_chance") or 0.0)
        selected_ms_count = 1
        selected_falloff_start = None
        selected_falloff_end = None
        selected_falloff_reduction = 0.0
    else:
        # Select attack by name or default to first
        if attack_name:
            lower_att = attack_name.lower()
            selected_attack = next(
                (a for a in all_attacks if a.name.lower() == lower_att), None
            )
            if selected_attack is None:
                available = [a.name for a in all_attacks]
                raise KeyError(
                    f"Attack {attack_name!r} not found for {name!r}. "
                    f"Available: {available}"
                )
        else:
            selected_attack = all_attacks[0]

        selected_base_damage = selected_attack.base_damage
        selected_innate = selected_attack.innate_elements
        selected_cc = selected_attack.crit_chance
        selected_cm = selected_attack.crit_multiplier
        selected_sc = selected_attack.status_chance
        selected_ms_count = selected_attack.multishot
        selected_falloff_start = selected_attack.falloff_start
        selected_falloff_end = selected_attack.falloff_end
        selected_falloff_reduction = selected_attack.falloff_reduction

    is_kuva_tenet = bool(entry.get("is_kuva_tenet", False))
    family = str(entry.get("family", "") or "")
    if "Kuva" in name or "Tenet" in name or "Kuva" in family or "Tenet" in family:
        is_kuva_tenet = True

    return Weapon(
        name=name,
        base_damage=selected_base_damage,
        innate_elements=selected_innate,
        is_kuva_tenet=is_kuva_tenet,
        attacks=all_attacks,
        crit_chance=selected_cc,
        crit_multiplier=selected_cm,
        status_chance=selected_sc,
        multishot=selected_ms_count,
        falloff_start=selected_falloff_start,
        falloff_end=selected_falloff_end,
        falloff_reduction=selected_falloff_reduction,
    )


def load_mod(name: str) -> Mod:
    """Load a mod by exact name. Raises KeyError if not found."""
    raw = _raw_mods()
    if name not in raw:
        lower = name.lower()
        for k in raw:
            if k.lower() == lower:
                name = k
                break
        else:
            raise KeyError(f"Mod not found: {name!r}")
    if name.startswith("Flawed "):
        raise KeyError(f"Flawed mods are no longer used: {name!r}")

    entry = raw[name]
    damage_bonus = float(entry.get("damage_bonus_pct") or 0.0)

    elemental_bonuses: list[DamageComponent] = []
    for field, dt in _ELEM_FIELD.items():
        v = entry.get(field)
        if v is not None:
            elemental_bonuses.append(DamageComponent(dt, float(v)))

    ips_bonuses: list[DamageComponent] = []
    for field, dt in _IPS_FIELD.items():
        v = entry.get(field)
        if v is not None:
            ips_bonuses.append(DamageComponent(dt, float(v)))

    faction_bonus = float(entry.get("faction_bonus") or 0.0)
    faction_target = entry.get("faction_target") or ""
    faction_type: FactionType | None = _FACTION_TYPE.get(faction_target.lower())

    cc_bonus = float(entry.get("crit_chance_pct") or 0.0)
    cd_bonus = float(entry.get("crit_damage_pct") or 0.0)
    sc_bonus = float(entry.get("status_chance_pct") or 0.0)
    multishot_bonus = float(entry.get("multishot_pct") or 0.0)
    status_damage_bonus = float(entry.get("status_damage_pct") or 0.0)
    fire_rate_bonus = float(entry.get("fire_rate_pct") or 0.0)
    magazine_bonus = float(entry.get("magazine_pct") or 0.0)
    ammo_max_bonus = float(entry.get("ammo_max_pct") or 0.0)
    reload_bonus = float(entry.get("reload_speed_pct") or 0.0)
    condition_overload_bonus = float(entry.get("condition_overload_pct") or 0.0)
    cc_per_combo_tier = float(entry.get("cc_per_combo_tier") or 0.0)
    sc_per_combo_tier = float(entry.get("sc_per_combo_tier") or 0.0)
    galv_kill_stat  = str(entry.get("galv_kill_stat")  or "")
    galv_kill_pct   = float(entry.get("galv_kill_pct")  or 0.0)
    galv_max_stacks = int(entry.get("galv_max_stacks")  or 0)

    return Mod(
        name=name,
        family=_mod_family(name),
        damage_bonus=damage_bonus,
        elemental_bonuses=elemental_bonuses,
        ips_bonuses=ips_bonuses,
        faction_bonus=faction_bonus,
        faction_type=faction_type,
        cc_bonus=cc_bonus,
        cd_bonus=cd_bonus,
        sc_bonus=sc_bonus,
        multishot_bonus=multishot_bonus,
        status_damage_bonus=status_damage_bonus,
        fire_rate_bonus=fire_rate_bonus,
        magazine_bonus=magazine_bonus,
        ammo_max_bonus=ammo_max_bonus,
        reload_bonus=reload_bonus,
        condition_overload_bonus=condition_overload_bonus,
        cc_per_combo_tier=cc_per_combo_tier,
        sc_per_combo_tier=sc_per_combo_tier,
        galv_kill_stat=galv_kill_stat,
        galv_kill_pct=galv_kill_pct,
        galv_max_stacks=galv_max_stacks,
    )


# Riven stat name → Mod field name (or elemental/IPS key for type bonuses)
_RIVEN_STAT_MAP: dict[str, str] = {
    "damage":         "damage_bonus",
    "crit_chance":    "cc_bonus",
    "crit_damage":    "cd_bonus",
    "status_chance":  "sc_bonus",
    "multishot":      "multishot_bonus",
    "fire_rate":      "fire_rate_bonus",
    "heat":           "heat",
    "cold":           "cold",
    "electricity":    "electricity",
    "toxin":          "toxin",
    "blast":          "blast",
    "corrosive":      "corrosive",
    "gas":            "gas",
    "magnetic":       "magnetic",
    "radiation":      "radiation",
    "viral":          "viral",
    "impact":         "impact",
    "puncture":       "puncture",
    "slash":          "slash",
}

RIVEN_STAT_NAMES: frozenset[str] = frozenset(_RIVEN_STAT_MAP)

_RIVEN_ELEM_TYPES: dict[str, DamageType] = {
    "heat":        DamageType.HEAT,
    "cold":        DamageType.COLD,
    "electricity": DamageType.ELECTRICITY,
    "toxin":       DamageType.TOXIN,
    "blast":       DamageType.BLAST,
    "corrosive":   DamageType.CORROSIVE,
    "gas":         DamageType.GAS,
    "magnetic":    DamageType.MAGNETIC,
    "radiation":   DamageType.RADIATION,
    "viral":       DamageType.VIRAL,
}

_RIVEN_IPS_TYPES: dict[str, DamageType] = {
    "impact":   DamageType.IMPACT,
    "puncture": DamageType.PUNCTURE,
    "slash":    DamageType.SLASH,
}


def make_riven_mod(stats: list[dict[str, str | float]], name: str = "Riven") -> Mod:
    """Build a Mod from Riven stat definitions.

    Each stat dict must have:
        "stat":  one of the keys in _RIVEN_STAT_MAP (e.g. "damage", "heat", "impact")
        "value": decimal fraction (e.g. 0.658 means +65.8%)

    Unknown stat keys are silently ignored.
    """
    damage_bonus = 0.0
    cc_bonus = 0.0
    cd_bonus = 0.0
    sc_bonus = 0.0
    multishot_bonus = 0.0
    fire_rate_bonus = 0.0
    elemental_bonuses: list[DamageComponent] = []
    ips_bonuses: list[DamageComponent] = []

    for entry in stats:
        stat = str(entry.get("stat", "")).lower()
        value = float(entry.get("value", 0.0))
        mapped = _RIVEN_STAT_MAP.get(stat)
        if mapped is None:
            continue
        if mapped in _RIVEN_IPS_TYPES:
            ips_bonuses.append(DamageComponent(_RIVEN_IPS_TYPES[mapped], value))
        elif mapped in _RIVEN_ELEM_TYPES:
            elemental_bonuses.append(DamageComponent(_RIVEN_ELEM_TYPES[mapped], value))
        elif mapped == "damage_bonus":
            damage_bonus += value
        elif mapped == "cc_bonus":
            cc_bonus += value
        elif mapped == "cd_bonus":
            cd_bonus += value
        elif mapped == "sc_bonus":
            sc_bonus += value
        elif mapped == "multishot_bonus":
            multishot_bonus += value
        elif mapped == "fire_rate_bonus":
            fire_rate_bonus += value

    return Mod(
        name=name,
        damage_bonus=damage_bonus,
        elemental_bonuses=elemental_bonuses,
        ips_bonuses=ips_bonuses,
        cc_bonus=cc_bonus,
        cd_bonus=cd_bonus,
        sc_bonus=sc_bonus,
        multishot_bonus=multishot_bonus,
        fire_rate_bonus=fire_rate_bonus,
    )


def load_enemy(name: str, body_part: str = "Body", headshot: bool = False) -> Enemy:
    """Load an enemy by exact name.

    Args:
        name:      Exact enemy name (case-insensitive fallback).
        body_part: Name of the body part to target (e.g. "Head", "Body").
                   Defaults to "Body" (multiplier 1.0).
        headshot:  Deprecated alias for body_part="Head".

    Raises KeyError if not found.
    """
    raw = _raw_enemies()
    if name not in raw:
        lower = name.lower()
        for k in raw:
            if k.lower() == lower:
                name = k
                break
        else:
            raise KeyError(f"Enemy not found: {name!r}")

    entry = raw[name]
    faction_type = _FACTION_TYPE.get(entry.get("faction", "").lower(), FactionType.NONE)
    health_type  = _HEALTH_TYPE.get(entry.get("health_type", "").lower(), HealthType.FLESH)
    armor_type   = _ARMOR_TYPE.get(entry.get("armor_type", "").lower(), ArmorType.NONE)

    # Build body_parts dict — supports both new body_parts key and legacy head_multiplier
    raw_parts = entry.get("body_parts")
    if raw_parts:
        body_parts = {k: float(v) for k, v in raw_parts.items()}
    else:
        hm = float(entry.get("head_multiplier") or 1.0)
        body_parts = {"Body": 1.0, "Head": hm}

    effective_part = "Head" if headshot else body_part
    body_part_mult = body_parts.get(effective_part, 1.0)

    return Enemy(
        name=name,
        faction=faction_type,
        health_type=health_type,
        armor_type=armor_type,
        base_armor=float(entry.get("base_armor") or 0.0),
        body_part_multiplier=body_part_mult,
        body_parts=body_parts,
        base_level=int(entry.get("base_level") or 1),
        base_health=float(entry.get("base_health") or 0.0),
        base_shield=float(entry.get("base_shield") or 0.0),
    )


def list_weapons() -> list[str]:
    return sorted(_raw_weapons().keys())


def list_mods() -> list[str]:
    return sorted(k for k in _raw_mods().keys() if not k.startswith("Flawed "))


def list_enemies() -> list[str]:
    return sorted(_raw_enemies().keys())


def list_body_parts(enemy_name: str) -> dict[str, float]:
    """Return the body_parts dict for the named enemy (case-insensitive)."""
    return load_enemy(enemy_name).body_parts


def list_attacks(weapon_name: str) -> list[dict]:
    """Return attack info for the named weapon (case-insensitive).

    Each entry: {"name": str, "crit_chance": float, "crit_multiplier": float,
                 "status_chance": float, "fire_rate": float, "shot_type": str}
    """
    weapon = load_weapon(weapon_name)
    return [
        {
            "name": a.name,
            "crit_chance": a.crit_chance,
            "crit_multiplier": a.crit_multiplier,
            "status_chance": a.status_chance,
            "fire_rate": a.fire_rate,
            "shot_type": a.shot_type,
            "multishot": a.multishot,
            "falloff_start": a.falloff_start,
            "falloff_end": a.falloff_end,
            "falloff_reduction": a.falloff_reduction,
        }
        for a in weapon.attacks
    ]
