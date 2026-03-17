from enum import Enum, auto


class DamageType(Enum):
    # Physical
    IMPACT = auto()
    PUNCTURE = auto()
    SLASH = auto()
    # Primary elemental
    HEAT = auto()
    COLD = auto()
    ELECTRICITY = auto()
    TOXIN = auto()
    # Secondary (combined) elemental
    BLAST = auto()
    CORROSIVE = auto()
    GAS = auto()
    MAGNETIC = auto()
    RADIATION = auto()
    VIRAL = auto()
    # Special
    TRUE = auto()
    VOID = auto()
    TAU = auto()


class FactionType(Enum):
    GRINEER = auto()
    CORPUS = auto()
    INFESTED = auto()
    CORRUPTED = auto()
    SENTIENT = auto()
    NONE = auto()


class HealthType(Enum):
    FLESH = auto()
    ROBOTIC = auto()
    FERRITE_ARMOR = auto()
    ALLOY_ARMOR = auto()
    SHIELDS = auto()
    PROTO_SHIELDS = auto()
    INFESTED_FLESH = auto()
    FOSSILIZED = auto()
    SINEW = auto()


class ArmorType(Enum):
    NONE = auto()
    FERRITE = auto()
    ALLOY = auto()
