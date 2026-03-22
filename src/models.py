from dataclasses import dataclass, field
from src.enums import DamageType, FactionType, HealthType, ArmorType


@dataclass
class DamageComponent:
    type: DamageType
    amount: float  # IEEE 754 float64

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DamageComponent):
            return NotImplemented
        return self.type == other.type and abs(self.amount - other.amount) < 1e-9


@dataclass
class WeaponAttack:
    name: str
    base_damage: dict[DamageType, float]
    innate_elements: list[DamageComponent] = field(default_factory=list)
    crit_chance: float = 0.0
    crit_multiplier: float = 1.0
    status_chance: float = 0.0
    shot_type: str = ""
    fire_rate: float = 0.0


@dataclass
class Weapon:
    name: str
    base_damage: dict[DamageType, float]          # IPS + any fixed elemental (from selected attack)
    innate_elements: list[DamageComponent] = field(default_factory=list)
    is_kuva_tenet: bool = False
    attacks: list[WeaponAttack] = field(default_factory=list)
    crit_chance: float = 0.0
    crit_multiplier: float = 1.0
    status_chance: float = 0.0

    @property
    def total_base_damage(self) -> float:
        return sum(self.base_damage.values()) + sum(c.amount for c in self.innate_elements)


@dataclass
class Mod:
    name: str
    damage_bonus: float = 0.0                     # additive, e.g. 1.65 for Serration
    elemental_bonuses: list[DamageComponent] = field(default_factory=list)
    faction_bonus: float = 0.0
    faction_type: FactionType | None = None        # Python 3.10+ union syntax
    cc_bonus: float = 0.0                         # additive crit chance, e.g. 1.5 for Point Strike
    cd_bonus: float = 0.0                         # additive crit damage, e.g. 1.2 for Vital Sense
    sc_bonus: float = 0.0                         # additive status chance, e.g. 0.9 for Rifle Aptitude
    multishot_bonus: float = 0.0                 # additive, e.g. 1.65 for Split Chamber
    status_damage_bonus: float = 0.0             # additive, e.g. 0.90 for Pistol Elementalist
    fire_rate_bonus: float = 0.0                 # additive, e.g. -0.20 for Critical Delay
    magazine_bonus: float = 0.0                  # additive, e.g. 0.60 for Ammo Stock (clip size)
    ammo_max_bonus: float = 0.0                  # additive, e.g. 0.90 for Ammo Drum (reserve)
    reload_bonus: float = 0.0                    # additive, e.g. 0.30 for Fast Hands
    condition_overload_bonus: float = 0.0        # additive per unique status on enemy (Condition Overload)


@dataclass
class Enemy:
    name: str
    faction: FactionType
    health_type: HealthType
    armor_type: ArmorType
    base_armor: float = 0.0
    body_part_multiplier: float = 1.0
    body_parts: dict = field(default_factory=lambda: {"Body": 1.0})
    base_level: int = 1
    base_health: float = 0.0
    base_shield: float = 0.0
