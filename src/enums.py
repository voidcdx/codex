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
    # Core factions
    GRINEER = auto()
    KUVA_GRINEER = auto()       # Kuva Lich / Sisters of Parvos allies
    CORPUS = auto()
    CORPUS_AMALGAM = auto()     # Amalgam units (Jupiter/Ropalolyst)
    INFESTED = auto()
    DEIMOS_INFESTED = auto()    # Deimos / Cambion Drift variants
    CORRUPTED = auto()          # Orokin Void
    SENTIENT = auto()
    # Newer factions (Update 35+)
    NARMER = auto()             # Narmer / Veil units
    MURMUR = auto()             # Void Cascade / Whispers in the Walls
    ZARIMAN = auto()            # Zariman / Angels of Zariman
    SCALDRA = auto()            # Jade Shadows / Technocyte
    TECHROT = auto()            # 1999 update
    ANARCHS = auto()            # 1999 update sub-faction
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
