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
    multishot: int = 1


@dataclass
class Weapon:
    name: str
    base_damage: dict[DamageType, float]          # IPS + any fixed elemental (from selected attack)
    innate_elements: list[DamageComponent] = field(default_factory=list)
    is_kuva_tenet: bool = False
    bonus_element_type: DamageType | None = None  # player-chosen element (Heat/Cold/Electricity/Toxin)
    bonus_element_pct: float = 0.0               # 0.25–0.60; bonus = total_base_damage × pct
    attacks: list[WeaponAttack] = field(default_factory=list)
    crit_chance: float = 0.0
    crit_multiplier: float = 1.0
    status_chance: float = 0.0
    multishot: int = 1

    @property
    def total_base_damage(self) -> float:
        return sum(self.base_damage.values()) + sum(c.amount for c in self.innate_elements)


@dataclass
class Mod:
    name: str
    damage_bonus: float = 0.0                     # additive, e.g. 1.65 for Serration
    elemental_bonuses: list[DamageComponent] = field(default_factory=list)
    ips_bonuses: list[DamageComponent] = field(default_factory=list)  # per-IPS-type % bonus (Impact/Puncture/Slash)
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
    galv_kill_stat: str = ""                     # which stat the on-kill stack bonus applies to
    galv_kill_pct: float = 0.0                   # per-stack bonus amount (e.g. 0.30 for Chamber)
    galv_max_stacks: int = 0                     # mod-specific stack cap


@dataclass
class Buff:
    """Warframe ability buff applied during damage calculation.

    Each buff category applies at a different pipeline step:
    - faction_damage_bonus: Step 5, additive with Bane mods, double-dips on procs (Roar)
    - damage_multiplier: Step 5.5, separate multiplicative, no double-dip (Eclipse, Vex Armor)
    - sonar_multiplier: Step 2, multiplies body part multiplier (Sonar)
    - elemental_type/bonus: Step 1, adds elemental damage as fraction of base (Xata's Whisper)
    - crit_damage_bonus: pre-calc, added to crit multiplier (Volt Shield)
    - electricity_bonus: Step 1, adds Electricity damage as fraction of base (Volt Shield)
    - fire_rate_bonus: pre-calc, added to fire rate multiplier (Wisp Haste)
    """
    name: str
    faction_damage_bonus: float = 0.0   # additive with Bane mods (Roar)
    damage_multiplier: float = 0.0      # multiplicative step (Eclipse, Vex Armor, Octavia)
    sonar_multiplier: float = 0.0       # multiplies body part (Sonar)
    elemental_type: DamageType | None = None  # element to add (Xata's, Toxic Lash, Nourish)
    elemental_bonus: float = 0.0        # fraction of base damage
    crit_damage_bonus: float = 0.0      # flat crit damage addition (Volt Shield)
    electricity_bonus: float = 0.0      # fraction of base damage as Electricity (Volt Shield)
    fire_rate_bonus: float = 0.0        # additive fire rate bonus (Wisp Haste)


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
