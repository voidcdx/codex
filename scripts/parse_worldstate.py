#!/usr/bin/env python3
"""
Parse raw Warframe worldstate JSON → clean, human-readable worldstate.json.

Input:  data/worldstate_raw.json   (from fetch_worldstate.py or browser download)
Input:  data/solnode_map.json      (from fetch_solnodes.py, optional but improves node names)
Output: data/worldstate.json

Can also be imported and called from web/api.py for live parsing.

Run:
  python scripts/parse_worldstate.py
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Node / mission type lookup tables
# ---------------------------------------------------------------------------

# Tier name from the internal fissure modifier key
FISSURE_TIERS: dict[str, str] = {
    "VoidT1": "Lith",
    "VoidT2": "Meso",
    "VoidT3": "Neo",
    "VoidT4": "Axi",
    "VoidT5": "Requiem",
    "VoidT6": "Omnia",
}

# Mission type path suffix → display name (used by some API endpoints)
MISSION_TYPES: dict[str, str] = {
    "Assassination":          "Assassination",
    "Assault":                "Assault",
    "Capture":                "Capture",
    "Defense":                "Defense",
    "Disruption":             "Disruption",
    "Excavation":             "Excavation",
    "Exterminate":            "Exterminate",
    "Hive":                   "Hive",
    "Hijack":                 "Hijack",
    "Infested":               "Infested Salvage",
    "InfestedSalvage":        "Infested Salvage",
    "Interception":           "Interception",
    "Junction":               "Junction",
    "MobileDefense":          "Mobile Defense",
    "Pursuit":                "Pursuit",
    "Rescue":                 "Rescue",
    "Sabotage":               "Sabotage",
    "Spy":                    "Spy",
    "Survival":               "Survival",
    "LongSurvival":           "Endurance",
    "RailjackAerial":         "Skirmish",
    "RailjackMission":        "Railjack",
    "VoidCascade":            "Void Cascade",
    "VoidFlood":              "Void Flood",
    "VoidArmageddon":         "Void Armageddon",
    "GasCity":                "Gas City",
    "ArchwingAssassination":  "Archwing Assassination",
}

# MT_ prefix style used in raw worldstate JSON
MT_MISSION_TYPES: dict[str, str] = {
    "MT_ASSASSINATION":    "Assassination",
    "MT_ASSAULT":          "Assault",
    "MT_CAPTURE":          "Capture",
    "MT_DEFENSE":          "Defense",
    "MT_TERRITORY":        "Disruption",
    "MT_EXCAVATE":         "Excavation",
    "MT_EXTERMINATE":      "Exterminate",
    "MT_HIVE":             "Hive",
    "MT_HIJACK":           "Hijack",
    "MT_INFESTED_SALVAGE": "Infested Salvage",
    "MT_INTERCEPTION":     "Interception",
    "MT_JUNCTION":         "Junction",
    "MT_MOBILE_DEFENSE":   "Mobile Defense",
    "MT_PURSUIT":          "Pursuit",
    "MT_RESCUE":           "Rescue",
    "MT_SABOTAGE":         "Sabotage",
    "MT_INTEL":            "Spy",
    "MT_SURVIVAL":         "Survival",
    "MT_LONG_SURVIVAL":    "Endurance",
    "MT_RAILJACK":         "Railjack",
    "MT_VOID_CASCADE":     "Void Cascade",
    "MT_VOID_FLOOD":       "Void Flood",
    "MT_VOID_ARMAGEDDON":  "Void Armageddon",
    "MT_LANDSCAPE":        "Free Roam",
    "MT_ARENA":            "Arena",
    "MT_ALCHEMY":          "Alchemy",
    "MT_ORPHIX":           "Orphix",
    "MT_CIRCUIT":          "The Circuit",
    "MT_ENDLESS_DEFENSE":  "Endurance Defense",
    "MT_EXTERMINATION":    "Exterminate",
    "MT_ARTIFACT":         "Capture",
    "MT_CORRUPTION":       "Corrupted Fissure",
}

FACTION_NAMES: dict[str, str] = {
    "FC_GRINEER":   "Grineer",
    "FC_CORPUS":    "Corpus",
    "FC_INFESTATION": "Infested",
    "FC_OROKIN":    "Orokin",
    "FC_TENNO":     "Tenno",
    "FC_MURMUR":    "Murmur",
    "FC_NARMER":    "Narmer",
    "FC_CORRUPTED": "Corrupted",
    "FC_SCALDRA":   "Scaldra",
    "FC_TECHROT":   "Techrot",
}

SORTIE_BOSSES: dict[str, str] = {
    "SORTIE_BOSS_VOR":            "Captain Vor",
    "SORTIE_BOSS_HEK":            "Councilor Vay Hek",
    "SORTIE_BOSS_RUK":            "General Sargas Ruk",
    "SORTIE_BOSS_KELA":           "Kela De Thaym",
    "SORTIE_BOSS_TUSK":           "Tusk Thumper",
    "SORTIE_BOSS_KRIL":           "Lieutenant Lech Kril",
    "SORTIE_BOSS_TYL":            "Tyl Regor",
    "SORTIE_BOSS_JACKAL":         "Jackal",
    "SORTIE_BOSS_ALAD":           "Alad V",
    "SORTIE_BOSS_AMBULAS":        "Ambulas",
    "SORTIE_BOSS_HYENA":          "Hyena Pack",
    "SORTIE_BOSS_NEF":            "Nef Anyo",
    "SORTIE_BOSS_RAPTOR":         "Raptor",
    "SORTIE_BOSS_LEPHANTIS":      "Lephantis",
    "SORTIE_BOSS_PHORID":         "Phorid",
    "SORTIE_BOSS_MUTALIST_ALAD":  "Mutalist Alad V",
    "SORTIE_BOSS_CORRUPTED_VOR":  "Corrupted Vor",
    "SORTIE_BOSS_INFALAD":        "Infested Alad V",
    "SORTIE_BOSS_ROPALOLYST":     "Ropalolyst",
    "SORTIE_BOSS_AMAR":           "Amar",
    "SORTIE_BOSS_BOREAL":         "Boreal",
    "SORTIE_BOSS_NIRA":           "Nira",
}

BOSS_FACTION: dict[str, str] = {
    "SORTIE_BOSS_VOR":           "Grineer",
    "SORTIE_BOSS_HEK":           "Grineer",
    "SORTIE_BOSS_RUK":           "Grineer",
    "SORTIE_BOSS_KELA":          "Grineer",
    "SORTIE_BOSS_TUSK":          "Grineer",
    "SORTIE_BOSS_KRIL":          "Grineer",
    "SORTIE_BOSS_TYL":           "Grineer",
    "SORTIE_BOSS_JACKAL":        "Corpus",
    "SORTIE_BOSS_ALAD":          "Corpus",
    "SORTIE_BOSS_AMBULAS":       "Corpus",
    "SORTIE_BOSS_HYENA":         "Corpus",
    "SORTIE_BOSS_NEF":           "Corpus",
    "SORTIE_BOSS_RAPTOR":        "Corpus",
    "SORTIE_BOSS_ROPALOLYST":    "Corpus",
    "SORTIE_BOSS_LEPHANTIS":     "Infested",
    "SORTIE_BOSS_PHORID":        "Infested",
    "SORTIE_BOSS_MUTALIST_ALAD": "Infested",
    "SORTIE_BOSS_INFALAD":       "Infested",
    "SORTIE_BOSS_CORRUPTED_VOR": "Corrupted",
    "SORTIE_BOSS_AMAR":          "Sentient",
    "SORTIE_BOSS_BOREAL":        "Sentient",
    "SORTIE_BOSS_NIRA":          "Sentient",
}

SORTIE_MODIFIERS: dict[str, str] = {
    "SORTIE_MODIFIER_IMPACT":           "Physical Enhancement: Impact",
    "SORTIE_MODIFIER_PUNCTURE":         "Physical Enhancement: Puncture",
    "SORTIE_MODIFIER_SLASH":            "Physical Enhancement: Slash",
    "SORTIE_MODIFIER_FIRE":             "Elemental Enhancement: Heat",
    "SORTIE_MODIFIER_FREEZE":           "Elemental Enhancement: Cold",
    "SORTIE_MODIFIER_ELECTRICITY":      "Elemental Enhancement: Electricity",
    "SORTIE_MODIFIER_TOXIN":            "Elemental Enhancement: Toxin",
    "SORTIE_MODIFIER_RADIATION":        "Elemental Enhancement: Radiation",
    "SORTIE_MODIFIER_MAGNETIC":         "Elemental Enhancement: Magnetic",
    "SORTIE_MODIFIER_GAS":              "Elemental Enhancement: Gas",
    "SORTIE_MODIFIER_VIRAL":            "Elemental Enhancement: Viral",
    "SORTIE_MODIFIER_CORROSIVE":        "Elemental Enhancement: Corrosive",
    "SORTIE_MODIFIER_BLAST":            "Elemental Enhancement: Blast",
    "SORTIE_MODIFIER_ARMOR":            "Augmented Enemy Armor",
    "SORTIE_MODIFIER_SHIELDS":          "Augmented Enemy Shields",
    "SORTIE_MODIFIER_LOW_ENERGY":       "Energy Reduction",
    "SORTIE_MODIFIER_EXIMUS":           "Eximus Stronghold",
    "SORTIE_MODIFIER_SECONDARY_ONLY":   "Secondary Only",
    "SORTIE_MODIFIER_SHOTGUN_ONLY":     "Shotgun Only",
    "SORTIE_MODIFIER_SNIPER_ONLY":      "Sniper Only",
    "SORTIE_MODIFIER_MELEE_ONLY":       "Melee Only",
    "SORTIE_MODIFIER_BOW_ONLY":         "Bow Only",
    "SORTIE_MODIFIER_RIFLE_ONLY":       "Assault Rifle Only",
    "SORTIE_MODIFIER_HAZARD_RADIATION": "Environmental Hazard: Radiation",
    "SORTIE_MODIFIER_HAZARD_MAGNETIC":  "Environmental Hazard: Magnetic",
    "SORTIE_MODIFIER_HAZARD_FOG":       "Environmental Hazard: Dense Fog",
    "SORTIE_MODIFIER_HAZARD_FIRE":      "Environmental Hazard: Fire",
    "SORTIE_MODIFIER_HAZARD_ICE":       "Environmental Hazard: Cryogenic",
    "SORTIE_MODIFIER_HAZARD_COLD":      "Environmental Hazard: Cryogenic",
}
ALL_NODES: dict[str, str] = {
    # Mercury
    "SolNode94":    "Apollodorus (Mercury)",
    "SolNode130":   "Lares (Mercury)",
    "SolNode119":   "Caloris (Mercury)",
    "SolNode12":    "Elion (Mercury)",
    "SolNode103":   "M Prime (Mercury)",
    "SolNode28":    "Terminus (Mercury)",
    "SolNode108":   "Tolstoj (Mercury)",
    "SolNode223":   "Boethius (Mercury)",
    "SolNode224":   "Odin (Mercury)",
    "SolNode225":   "Suisei (Mercury)",
    "SolNode226":   "Pantheon (Mercury)",
    "MercuryHUB":   "Larunda Relay (Mercury)",
    # Venus
    "SolNode129":   "Orb Vallis (Venus)",
    "SolNode123":   "V Prime (Venus)",
    "SolNode61":    "Ishtar (Venus)",
    "SolNode2":     "Aphrodite (Venus)",
    "SolNode23":    "Cytherean (Venus)",
    "SolNode128":   "E Gate (Venus)",
    "SolNode109":   "Linea (Venus)",
    "SolNode104":   "Fossa (Venus)",
    "SolNode66":    "Unda (Venus)",
    "ClanNode1":    "Malva (Venus)",
    "SolNode107":   "Venera (Venus)",
    "SolNode22":    "Tessera (Venus)",
    "SolNode101":   "Kiliken (Venus)",
    "SolNode145":   "Romula (Venus)",
    "SolNode146":   "Montes (Venus)",
    "VenusHUB":     "Vesper Relay (Venus)",
    # Earth
    "SolNode149":   "Plains of Eidolon (Earth)",
    "SolNode7":     "Cervantes (Earth)",
    "SolNode56":    "Mantle (Earth)",
    "SolNode63":    "Cambria (Earth)",
    "SolNode100":   "Oro (Earth)",
    "SolNode106":   "Pacific (Earth)",
    "SolNode96":    "Eurasia (Earth)",
    "SolNode87":    "Everest (Earth)",
    "SolNode89":    "Mariana (Earth)",
    "SolNode131":   "Cetus (Earth)",
    "SolNode76":    "Lith (Earth)",
    "EarthHUB":     "Strata Relay (Earth)",
    # Mars
    "SolNode38":    "War (Mars)",
    "SolNode64":    "Alator (Mars)",
    "SolNode85":    "Kadesh (Mars)",
    "SolNode11":    "Gradivus (Mars)",
    "SolNode67":    "Olympus (Mars)",
    "SolNode86":    "Ara (Mars)",
    "SolNode16":    "Augustus (Mars)",
    "SolNode50":    "Arval (Mars)",
    "SolNode15":    "Spear (Mars)",
    "SolNode216":   "Hellas Basin (Mars)",
    "SolNode82":    "Martialis (Mars)",
    "SolNode170":   "Wahiba (Mars)",
    "SolNode117":   "Valle (Mars)",
    "SolNode44":    "Ultor (Mars)",
    "SolNode79":    "Ares (Mars)",
    "SolNode99":    "Manics (Mars)",
    # Ceres
    "SolNode157":   "Draco (Ceres)",
    "SolNode158":   "Gabii (Ceres)",
    "SolNode148":   "Cinxia (Ceres)",
    "SolNode147":   "Seimeni (Ceres)",
    "SolNode169":   "Casta (Ceres)",
    "SolNode140":   "Nuovo (Ceres)",
    "SolNode141":   "Kiste (Ceres)",
    "SolNode142":   "Bode (Ceres)",
    "SolNode144":   "Lex (Ceres)",
    "SolNode75":    "Ludi (Ceres)",
    "SolNode143":   "Exta (Ceres)",
    "SolNode29":    "Paimon (Ceres)",
    "SolNode39":    "Olla (Ceres)",
    "SolNode19":    "Egeria (Ceres)",
    "SolNode150":   "Ker (Ceres)",
    "SolNode151":   "Thon (Ceres)",
    "SolNode152":   "Hapke (Ceres)",
    "SolNode181":   "Cinxia (Ceres)",
    # Phobos
    "SettlementNode1":  "Roche (Phobos)",
    "SettlementNode3":  "Stickney (Phobos)",
    "SettlementNode2":  "Skyresh (Phobos)",
    "SettlementNode12": "Monolith (Phobos)",
    "SettlementNode10": "Kepler (Phobos)",
    "SettlementNode15": "Sharpless (Phobos)",
    "SettlementNode11": "Gulliver (Phobos)",
    "SettlementNode14": "Shklovsky (Phobos)",
    "ClanNode10":       "Memphis (Phobos)",
    "SettlementNode20": "Iliad (Phobos)",
    "ClanNode11":       "Zeugma (Phobos)",
    # Jupiter
    "SolNode55":  "Themisto (Jupiter)",
    "SolNode65":  "Adrastea (Jupiter)",
    "SolNode46":  "Amalthea (Jupiter)",
    "SolNode164": "Elara (Jupiter)",
    "SolNode167": "Io (Jupiter)",
    "SolNode163": "Carpo (Jupiter)",
    "SolNode177": "Metis (Jupiter)",
    "SolNode183": "Callisto (Jupiter)",
    "SolNode187": "Sinai (Jupiter)",
    "SolNode188": "Ananke (Jupiter)",
    "SolNode196": "Ganymede (Jupiter)",
    "SolNode805": "The Ropalolyst (Jupiter)",
    "SolNode173": "Europa (Jupiter)",
    "SolNode31":  "Carme (Jupiter)",
    "SolNode195": "Io B (Jupiter)",
    # Saturn
    "SolNode47":  "Pandora (Saturn)",
    "SolNode90":  "Anthe (Saturn)",
    "SolNode20":  "Tethys (Saturn)",
    "SolNode14":  "Cassini (Saturn)",
    "SolNode24":  "Titan (Saturn)",
    "SolNode91":  "Telesto (Saturn)",
    "SolNode92":  "Calypso (Saturn)",
    "SolNode93":  "Dione (Saturn)",
    "SolNode41":  "Rhea (Saturn)",
    "SolNode52":  "Helene (Saturn)",
    "SolNode53":  "Caracol (Saturn)",
    "SolNode54":  "Pallene (Saturn)",
    "SolNode110": "Mimas (Saturn)",
    "SolNode111": "Enceladus (Saturn)",
    "SolNode25":  "Phoebe (Saturn)",
    "SaturnHUB":  "Kronia Relay (Saturn)",
    # Uranus
    "SolNode120": "Ophelia (Uranus)",
    "SolNode83":  "Cressida (Uranus)",
    "SolNode98":  "Desdemona (Uranus)",
    "SolNode9":   "Rosalind (Uranus)",
    "SolNode60":  "Caliban (Uranus)",
    "SolNode114": "Puck (Uranus)",
    "ClanNode16": "Ur (Uranus)",
    "SolNode34":  "Sycorax (Uranus)",
    "SolNode122": "Stephano (Uranus)",
    "SolNode907": "Caelus (Uranus)",
    "ClanNode17": "Assur (Uranus)",
    # Neptune
    "SolNode57":  "Sao (Neptune)",
    "SolNode62":  "Neso (Neptune)",
    "SolNode908": "Salacia (Neptune)",
    "SolNode127": "Psamathe (Neptune)",
    "SolNode118": "Laomedeia (Neptune)",
    "SolNode84":  "Nereid (Neptune)",
    "ClanNode20": "Yursa (Neptune)",
    "ClanNode21": "Kelashin (Neptune)",
    "SolNode49":  "Larissa (Neptune)",
    "SolNode1":   "Galatea (Neptune)",
    "SolNode17":  "Proteus (Neptune)",
    "SolNode78":  "Triton (Neptune)",
    "SolNode6":   "Despina (Neptune)",
    # Pluto
    "SolNode42":  "Acheron (Pluto)",
    "SolNode43":  "Outer Terminus (Pluto)",
    "SolNode102": "Hydra (Pluto)",
    "SolNode37":  "Oceanum (Pluto)",
    "SolNode4":   "Narcissus (Pluto)",
    "SolNode35":  "Regna (Pluto)",
    "SolNode36":  "Sechura (Pluto)",
    "SolNode80":  "Cypress (Pluto)",
    "SolNode81":  "Palus (Pluto)",
    "SolNode112": "Minthe (Pluto)",
    "SolNode113": "Hieracon (Pluto)",
    "SolNode48":  "Hades (Pluto)",
    "SolNode73":  "Cerberus (Pluto)",
    "PlutoHUB":   "Orcus Relay (Pluto)",
    # Sedna
    "SolNode115": "Hydron (Sedna)",
    "SolNode116": "Rusalka (Sedna)",
    "SolNode40":  "Tikoloshe (Sedna)",
    "SolNode8":   "Merrow (Sedna)",
    "SolNode51":  "Kelpie (Sedna)",
    "SolNode77":  "Charybdis (Sedna)",
    "SolNode70":  "Berehynia (Sedna)",
    "SolNode69":  "Selkie (Sedna)",
    "SolNode71":  "Vodyanoi (Sedna)",
    "SolNode72":  "Nakki (Sedna)",
    "SolNode68":  "Marid (Sedna)",
    "SolNode74":  "Adaro (Sedna)",
    "SolNode88":  "Yam (Sedna)",
    "SolNode153": "Coba (Sedna)",
    # Europa
    "SolNode300": "Cervantes (Europa)",
    "SolNode301": "Morax (Europa)",
    "SolNode302": "Armaros (Europa)",
    "SolNode303": "Abaddon (Europa)",
    "SolNode304": "Valac (Europa)",
    "SolNode305": "Baal (Europa)",
    "SolNode306": "Paimon (Europa)",
    "SolNode307": "Valefor (Europa)",
    "SolNode308": "Ose (Europa)",
    "SolNode309": "Naamah (Europa)",
    "SolNode310": "Kokabiel (Europa)",
    "SolNode311": "Sorath (Europa)",
    "SolNode312": "Orias (Europa)",
    "SolNode313": "Lillith (Europa)",
    "SolNode314": "Larzac (Europa)",
    "ClanNode14": "Cholistan (Europa)",
    "ClanNode15": "Viver (Europa)",
    "EuropaHUB":  "Leonov Relay (Europa)",
    # Lua
    "SolNode132": "Stöfler (Lua)",
    "SolNode133": "Tycho (Lua)",
    "SolNode134": "Plato (Lua)",
    "SolNode135": "Zeipel (Lua)",
    "SolNode136": "Pavlov (Lua)",
    "SolNode137": "Copernicus (Lua)",
    "SolNode138": "Grimaldi (Lua)",
    "SolNode139": "Apollo (Lua)",
    "SolNode802": "Circulus (Lua)",
    # Eris
    "SolNode125": "Zabala (Eris)",
    "SolNode126": "Akkad (Eris)",
    "SolNode121": "Xini (Eris)",
    "SolNode105": "Naeglar (Eris)",
    "SolNode97":  "Brugia (Eris)",
    "SolNode95":  "Kala-azar (Eris)",
    "SolNode27":  "Histo (Eris)",
    "SolNode26":  "Isos (Eris)",
    "SolNode33":  "Nimus (Eris)",
    "SolNode32":  "Saxis (Eris)",
    "SolNode30":  "Oestrus (Eris)",
    "ErisHUB":    "Kuiper Relay (Eris)",
    # Void
    "SolNode400": "Teshub (Void)",
    "SolNode401": "Hepit (Void)",
    "SolNode402": "Taranis (Void)",
    "SolNode403": "Tiwaz (Void)",
    "SolNode404": "Stribog (Void)",
    "SolNode405": "Ani (Void)",
    "SolNode406": "Ukko (Void)",
    "SolNode407": "Oxomoco (Void)",
    "SolNode408": "Belenus (Void)",
    "SolNode409": "Mot (Void)",
    "SolNode410": "Aten (Void)",
    "SolNode411": "Marduk (Void)",
    "SolNode412": "Mithra (Void)",
    # Kuva Fortress
    "SolNode500": "Koro (Kuva Fortress)",
    "SolNode501": "Nabuk (Kuva Fortress)",
    "SolNode502": "Taveuni (Kuva Fortress)",
    "SolNode503": "Pago (Kuva Fortress)",
    "SolNode504": "Dakata (Kuva Fortress)",
    "SolNode505": "Rotuma (Kuva Fortress)",
    "SolNode506": "Tamu (Kuva Fortress)",
    "SolNode507": "Kuva Survival (Kuva Fortress)",
    # Deimos
    "SolNode706": "Horend (Deimos)",
    "SolNode707": "Hyf (Deimos)",
    "SolNode708": "Phlegyas (Deimos)",
    "SolNode709": "Magnacidium (Deimos)",
    "SolNode710": "Terrorem (Deimos)",
    "SolNode711": "Formido (Deimos)",
    "SolNode712": "Persto (Deimos)",
    "SolNode713": "Effervo (Deimos)",
    "SolNode714": "Nex (Deimos)",
    "SolNode715": "Munio (Deimos)",
    "SolNode716": "Cambire (Deimos)",
    "SolNode717": "Sanctum Anatomica (Deimos)",
    "SolNode741": "Armatus (Deimos)",
    "SolNode742": "Effervo (Deimos)",
    "SolNode743": "Munio (Deimos)",
    "SolNode718": "Rictus (Deimos)",
    "SolNode744": "Exsequias (Deimos)",
    "SolNode747": "Fervicustos (Deimos)",
    # Zariman
    "SolNode780": "Everview Arc (Zariman)",
    "SolNode781": "Tuvul Commons (Zariman)",
    "SolNode782": "Oro Works (Zariman)",
    "SolNode783": "Halako Perimeter (Zariman)",
    "SolNode230": "Halako Perimeter (Zariman)",
    "SolNode232": "Tuvul Commons (Zariman)",
    # Duviri
    "SolNode751": "Duviri (Duviri)",
    "SolNode752": "The Duviri Experience (Duviri)",
    "SolNode753": "The Lone Story (Duviri)",
    "SolNode754": "The Circuit (Duviri)",
    "SolNode755": "The Steel Path Circuit (Duviri)",
    # Railjack Proxima — Earth
    "CrewBattleNode500": "Sover Strait (Earth Proxima)",
    "CrewBattleNode501": "Ogal Cluster (Earth Proxima)",
    "CrewBattleNode502": "Ganalen's Grave (Earth Proxima)",
    "CrewBattleNode503": "Rempei Cluster (Earth Proxima)",
    "CrewBattleNode504": "Iota Temple (Earth Proxima)",
    "CrewBattleNode505": "Korms Belt (Earth Proxima)",
    # Railjack Proxima — Venus
    "CrewBattleNode510": "Kasio's Rest (Venus Proxima)",
    "CrewBattleNode511": "Falling Glory (Venus Proxima)",
    "CrewBattleNode512": "Luckless Expanse (Venus Proxima)",
    "CrewBattleNode513": "Beacon of Affliction (Venus Proxima)",
    "CrewBattleNode514": "Vesper Strait (Venus Proxima)",
    "CrewBattleNode515": "Calabash Depot (Venus Proxima)",
    "CrewBattleNode516": "Enkidu Ice Drifts (Venus Proxima)",
    # Railjack Proxima — Neptune
    "CrewBattleNode520": "Lu-Yan Station (Neptune Proxima)",
    "CrewBattleNode521": "Nu-Gua Mines (Neptune Proxima)",
    "CrewBattleNode522": "Mammon's Prospect (Neptune Proxima)",
    "CrewBattleNode523": "Sovereign Grasp (Neptune Proxima)",
    "CrewBattleNode524": "Arva Vector (Neptune Proxima)",
    # Railjack Proxima — Pluto
    "CrewBattleNode525": "Brom Cluster (Pluto Proxima)",
    "CrewBattleNode526": "Peregrine Axis (Pluto Proxima)",
    "CrewBattleNode527": "Obol Crossing (Pluto Proxima)",
    "CrewBattleNode528": "Fenton's Field (Pluto Proxima)",
    # Railjack Proxima — Veil
    "CrewBattleNode529": "Flexa (Veil Proxima)",
    "CrewBattleNode530": "H-2 Cloud (Veil Proxima)",
    "CrewBattleNode531": "R-9 Cloud (Veil Proxima)",
    "CrewBattleNode532": "Nsu Grid (Veil Proxima)",
    "CrewBattleNode533": "Gian Point (Veil Proxima)",
    "CrewBattleNode534": "Arc Silver (Veil Proxima)",
}

# Node key → faction name, derived from factionIndex (element [2]) in ExportRegions
# NODE_DATA. FACTION_INDEX: 0=Grineer 1=Corpus 2=Infested 3=Orokin 5=Sentient
# 7=Murmur 8=Scaldra 9=Techrot 10=Duviri 11=Neutral 13=Corrupted
NODE_FACTION: dict[str, str] = {
    # Mercury
    "SolNode94": "Infested",   "SolNode130": "Infested",  "SolNode119": "Grineer",
    "SolNode12": "Grineer",    "SolNode103": "Grineer",   "SolNode28":  "Infested",
    "SolNode108": "Grineer",   "SolNode223": "Infested",  "SolNode224": "Grineer",
    "SolNode225": "Grineer",   "SolNode226": "Grineer",   "MercuryHUB": "Neutral",
    # Venus
    "SolNode129": "Corpus",    "SolNode123": "Corpus",    "SolNode61":  "Corpus",
    "SolNode2":   "Corpus",    "SolNode23":  "Corpus",    "SolNode128": "Corpus",
    "SolNode109": "Corpus",    "SolNode104": "Corpus",    "SolNode66":  "Corpus",
    "ClanNode1":  "Infested",  "SolNode107": "Corpus",    "SolNode22":  "Corpus",
    "SolNode101": "Corpus",    "SolNode145": "Corpus",    "SolNode146": "Corpus",
    "VenusHUB":   "Neutral",
    # Earth
    "SolNode149": "Grineer",   "SolNode7":   "Grineer",   "SolNode56":  "Grineer",
    "SolNode63":  "Grineer",   "SolNode100": "Grineer",   "SolNode106": "Grineer",
    "SolNode96":  "Grineer",   "SolNode87":  "Grineer",   "SolNode89":  "Grineer",
    "SolNode131": "Grineer",   "SolNode76":  "Grineer",   "EarthHUB":   "Neutral",
    # Mars
    "SolNode38":  "Grineer",   "SolNode64":  "Grineer",   "SolNode85":  "Grineer",
    "SolNode11":  "Grineer",   "SolNode67":  "Grineer",   "SolNode86":  "Grineer",
    "SolNode16":  "Grineer",   "SolNode50":  "Grineer",   "SolNode15":  "Grineer",
    "SolNode216": "Grineer",   "SolNode82":  "Grineer",   "SolNode170": "Grineer",
    "SolNode117": "Grineer",   "SolNode44":  "Grineer",   "SolNode79":  "Grineer",
    "SolNode99":  "Grineer",
    # Ceres
    "SolNode157": "Grineer",   "SolNode158": "Infested",  "SolNode148": "Grineer",
    "SolNode147": "Infested",  "SolNode169": "Scaldra",   "SolNode140": "Grineer",
    "SolNode141": "Grineer",   "SolNode142": "Grineer",   "SolNode144": "Grineer",
    "SolNode75":  "Grineer",   "SolNode143": "Grineer",   "SolNode29":  "Grineer",
    "SolNode39":  "Grineer",   "SolNode19":  "Grineer",   "SolNode150": "Grineer",
    "SolNode151": "Grineer",   "SolNode152": "Grineer",   "SolNode181": "Grineer",
    # Phobos
    "SettlementNode1":  "Corpus",  "SettlementNode3":  "Corpus",
    "SettlementNode2":  "Corpus",  "SettlementNode12": "Corpus",
    "SettlementNode10": "Corpus",  "SettlementNode15": "Corpus",
    "SettlementNode11": "Corpus",  "SettlementNode14": "Corpus",
    "ClanNode10":       "Infested","SettlementNode20": "Corpus",
    "ClanNode11":       "Infested",
    # Jupiter
    "SolNode55":  "Corpus",    "SolNode65":  "Grineer",   "SolNode46":  "Corpus",
    "SolNode164": "Infested",  "SolNode167": "Infested",  "SolNode163": "Corpus",
    "SolNode177": "Corpus",    "SolNode183": "Corpus",    "SolNode187": "Corpus",
    "SolNode188": "Corpus",    "SolNode196": "Corpus",    "SolNode805": "Sentient",
    "SolNode173": "Corpus",    "SolNode31":  "Corpus",    "SolNode195": "Corpus",
    # Saturn
    "SolNode47":  "Grineer",   "SolNode90":  "Grineer",   "SolNode20":  "Grineer",
    "SolNode14":  "Grineer",   "SolNode24":  "Infested",  "SolNode91":  "Corpus",
    "SolNode92":  "Grineer",   "SolNode93":  "Corpus",    "SolNode41":  "Grineer",
    "SolNode52":  "Grineer",   "SolNode53":  "Grineer",   "SolNode54":  "Corpus",
    "SolNode110": "Infested",  "SolNode111": "Corpus",    "SolNode25":  "Corpus",
    "SaturnHUB":  "Neutral",
    # Uranus
    "SolNode120": "Grineer",   "SolNode83":  "Grineer",   "SolNode98":  "Grineer",
    "SolNode9":   "Grineer",   "SolNode60":  "Grineer",   "SolNode114": "Grineer",
    "ClanNode16": "Infested",  "SolNode34":  "Grineer",   "SolNode122": "Grineer",
    "SolNode907": "Grineer",   "ClanNode17": "Infested",
    # Neptune
    "SolNode57":  "Corpus",    "SolNode62":  "Corpus",    "SolNode908": "Corpus",
    "SolNode127": "Corpus",    "SolNode118": "Corpus",    "SolNode84":  "Corpus",
    "ClanNode20": "Infested",  "ClanNode21": "Infested",  "SolNode49":  "Corpus",
    "SolNode1":   "Corpus",    "SolNode17":  "Corpus",    "SolNode78":  "Corpus",
    "SolNode6":   "Corpus",
    # Pluto
    "SolNode42":  "Corpus",    "SolNode43":  "Scaldra",   "SolNode102": "Corpus",
    "SolNode37":  "Corpus",    "SolNode4":   "Corpus",    "SolNode35":  "Infested",
    "SolNode36":  "Infested",  "SolNode80":  "Corpus",    "SolNode81":  "Infested",
    "SolNode112": "Murmur",    "SolNode113": "Infested",  "SolNode48":  "Corpus",
    "SolNode73":  "Corrupted", "PlutoHUB":   "Neutral",
    # Sedna
    "SolNode115": "Grineer",   "SolNode116": "Grineer",   "SolNode40":  "Grineer",
    "SolNode8":   "Grineer",   "SolNode51":  "Grineer",   "SolNode77":  "Grineer",
    "SolNode70":  "Grineer",   "SolNode69":  "Infested",  "SolNode71":  "Grineer",
    "SolNode72":  "Grineer",   "SolNode68":  "Grineer",   "SolNode74":  "Grineer",
    "SolNode88":  "Grineer",   "SolNode153": "Grineer",
    # Europa
    "SolNode300": "Corpus",    "SolNode301": "Corpus",    "SolNode302": "Corpus",
    "SolNode303": "Corpus",    "SolNode304": "Corpus",    "SolNode305": "Corpus",
    "SolNode306": "Corpus",    "SolNode307": "Corpus",    "SolNode308": "Corrupted",
    "SolNode309": "Corpus",    "SolNode310": "Corpus",    "SolNode311": "Corpus",
    "SolNode312": "Corpus",    "SolNode313": "Corpus",    "SolNode314": "Corpus",
    "ClanNode14": "Infested",  "ClanNode15": "Infested",  "EuropaHUB":  "Neutral",
    # Lua
    "SolNode132": "Orokin",    "SolNode133": "Orokin",    "SolNode134": "Orokin",
    "SolNode135": "Orokin",    "SolNode136": "Orokin",    "SolNode137": "Orokin",
    "SolNode138": "Orokin",    "SolNode139": "Orokin",    "SolNode802": "Orokin",
    # Eris
    "SolNode125": "Infested",  "SolNode126": "Infested",  "SolNode121": "Infested",
    "SolNode105": "Infested",  "SolNode97":  "Techrot",   "SolNode95":  "Infested",
    "SolNode27":  "Infested",  "SolNode26":  "Infested",  "SolNode33":  "Infested",
    "SolNode32":  "Infested",  "SolNode30":  "Infested",  "ErisHUB":    "Neutral",
    # Void
    "SolNode400": "Orokin",    "SolNode401": "Orokin",    "SolNode402": "Orokin",
    "SolNode403": "Orokin",    "SolNode404": "Orokin",    "SolNode405": "Orokin",
    "SolNode406": "Orokin",    "SolNode407": "Orokin",    "SolNode408": "Orokin",
    "SolNode409": "Orokin",    "SolNode410": "Orokin",    "SolNode411": "Orokin",
    "SolNode412": "Orokin",
    # Kuva Fortress
    "SolNode500": "Grineer",   "SolNode501": "Grineer",   "SolNode502": "Infested",
    "SolNode503": "Grineer",   "SolNode504": "Grineer",   "SolNode505": "Grineer",
    "SolNode506": "Grineer",   "SolNode507": "Grineer",
    # Deimos
    "SolNode706": "Infested",  "SolNode707": "Infested",  "SolNode708": "Infested",
    "SolNode709": "Infested",  "SolNode710": "Infested",  "SolNode711": "Infested",
    "SolNode712": "Infested",  "SolNode713": "Murmur",    "SolNode714": "Murmur",
    "SolNode715": "Murmur",    "SolNode716": "Murmur",    "SolNode717": "Murmur",
    "SolNode741": "Murmur",    "SolNode742": "Murmur",    "SolNode743": "Murmur",
    "SolNode718": "Murmur",    "SolNode744": "Murmur",    "SolNode747": "Murmur",
    # Zariman
    "SolNode780": "Corpus",    "SolNode781": "Corpus",    "SolNode782": "Corpus",
    "SolNode783": "Corpus",    "SolNode230": "Corpus",    "SolNode232": "Corpus",
    # Duviri
    "SolNode751": "Duviri",    "SolNode752": "Duviri",    "SolNode753": "Duviri",
    "SolNode754": "Duviri",    "SolNode755": "Duviri",
    # Railjack Proxima
    "CrewBattleNode500": "Grineer",  "CrewBattleNode501": "Grineer",
    "CrewBattleNode502": "Grineer",  "CrewBattleNode503": "Grineer",
    "CrewBattleNode504": "Grineer",  "CrewBattleNode505": "Grineer",
    "CrewBattleNode510": "Corpus",   "CrewBattleNode511": "Corpus",
    "CrewBattleNode512": "Corpus",   "CrewBattleNode513": "Corpus",
    "CrewBattleNode514": "Corpus",   "CrewBattleNode515": "Corpus",
    "CrewBattleNode516": "Corpus",   "CrewBattleNode520": "Corpus",
    "CrewBattleNode521": "Corpus",   "CrewBattleNode522": "Corpus",
    "CrewBattleNode523": "Corpus",   "CrewBattleNode524": "Corpus",
    "CrewBattleNode525": "Corpus",   "CrewBattleNode526": "Corpus",
    "CrewBattleNode527": "Corpus",   "CrewBattleNode528": "Corpus",
    "CrewBattleNode529": "Grineer",  "CrewBattleNode530": "Grineer",
    "CrewBattleNode531": "Grineer",  "CrewBattleNode532": "Grineer",
    "CrewBattleNode533": "Grineer",  "CrewBattleNode534": "Grineer",
}

ITEM_NAMES: dict[str, str] = {
    # Warframes
    "/Lotus/StoreItems/Powersuits/AntiMatter/NovaPrime":                                                              "Nova Prime",
    "/Lotus/StoreItems/Powersuits/DemonFrame/DemonFrame":                                                             "Uriel",
    "/Lotus/StoreItems/Powersuits/Inkblot/Inkblot":                                                                   "Follie",
    "/Lotus/StoreItems/Powersuits/MonkeyKing/MonkeyKing":                                                             "Wukong",
    "/Lotus/StoreItems/Powersuits/Rhino/Rhino":                                                                       "Rhino",
    "/Lotus/StoreItems/Powersuits/Trinity/TrinityPrime":                                                              "Trinity Prime",
    "/Lotus/StoreItems/Powersuits/Wisp/Wisp":                                                                         "Wisp",
    # Weapons
    "/Lotus/StoreItems/Weapons/Tenno/Bows/PrimeBow2/PrimeBow2":                                                       "Paris Prime",
    "/Lotus/StoreItems/Weapons/Tenno/Melee/Dagger/FangPrimeDagger":                                                   "Fang Prime",
    "/Lotus/StoreItems/Weapons/Tenno/Melee/PrimeDualKamas/PrimeDualKamas":                                            "Dual Kamas Prime",
    "/Lotus/StoreItems/Weapons/Tenno/Melee/SwordsAndBoards/MeleeContestWinnerOne/TennoSwordShield":                   "Silva & Aegis",
    "/Lotus/StoreItems/Weapons/Tenno/Pistol/HandShotGun":                                                             "Bronco",
    "/Lotus/StoreItems/Weapons/Tenno/Pistols/PrimeLex/PrimeLex":                                                      "Lex Prime",
    "/Lotus/StoreItems/Weapons/Tenno/Pistols/PrimeVasto/PrimeVastoPistol":                                            "Vasto Prime",
    "/Lotus/StoreItems/Weapons/Tenno/Rifle/BratonPrime":                                                              "Braton Prime",
    "/Lotus/StoreItems/Weapons/Tenno/Shotgun/Shotgun":                                                                "Strun",
    # Blueprints & recipes
    "/Lotus/StoreItems/Types/Recipes/Helmets/NyxPrimeHelmetBlueprint":                                               "Nyx Prime Neuroptics Blueprint",
    "/Lotus/StoreItems/Types/Recipes/Helmets/WukongPrimeHelmetBlueprint":                                             "Wukong Prime Neuroptics Blueprint",
    "/Lotus/StoreItems/Types/Recipes/WarframeRecipes/NovaPrimeBlueprintRecipe":                                       "Nova Prime Blueprint",
    "/Lotus/StoreItems/Types/Recipes/WarframeRecipes/NyxPrimeBlueprintRecipe":                                        "Nyx Prime Blueprint",
    "/Lotus/StoreItems/Types/Recipes/WarframeRecipes/TrinityPrimeBlueprintRecipe":                                    "Trinity Prime Blueprint",
    "/Lotus/StoreItems/Types/Recipes/WarframeRecipes/WukongPrimeBlueprintRecipe":                                     "Wukong Prime Blueprint",
    "/Lotus/StoreItems/Types/Recipes/Weapons/CrpScopePistolBlueprint":                                               "Arca Scisco Blueprint",
    "/Lotus/Types/Recipes/Weapons/WeaponParts/DeraVandalReceiver":                                                    "Dera Vandal Receiver",
    "/Lotus/Types/Recipes/Weapons/WeaponParts/GrineerCombatKnifeHilt":                                               "Sheev Hilt",
    "/Lotus/Types/Recipes/Weapons/WeaponParts/GrineerCombatKnifeBlade":                                              "Sheev Blade",
    # Relics
    "/Lotus/StoreItems/Types/Game/Projections/T1VoidProjectionNovaTrinityVaultABronze":                               "Lith K4 Relic",
    "/Lotus/StoreItems/Types/Game/Projections/T2VoidProjectionNovaTrinityVaultABronze":                               "Meso D5 Relic",
    "/Lotus/StoreItems/Types/Game/Projections/T3VoidProjectionNovaTrinityVaultABronze":                               "Neo N12 Relic",
    "/Lotus/StoreItems/Types/Game/Projections/T4VoidProjectionNovaTrinityVaultABronze":                               "Axi S7 Relic",
    # Resources & research
    "/Lotus/Types/Items/MiscItems/InfestedAladCoordinate":                                                            "Mutalist Alad V Nav Coordinate",
    "/Lotus/Types/Items/Research/BioComponent":                                                                       "Mutagen Mass",
    "/Lotus/Types/Items/Research/ChemComponent":                                                                      "Detonite Injector",
    "/Lotus/Types/Items/Research/EnergyComponent":                                                                    "Fieldron",
    # Mods & shards
    "/Lotus/StoreItems/Upgrades/Mods/FusionBundles/CircuitSilverSteelPathFusionBundle":                               "Silver Archon Shard",
    # Cosmetics — skins
    "/Lotus/StoreItems/Upgrades/Skins/Bows/BowPrime2TwitchSkin":                                                     "Paris Prime Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Dagger/FangPrimeTwitchSkin":                                                   "Fang Prime Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/DualKamas/DualKamasPrimeTwitchSkin":                                           "Dual Kamas Prime Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Glaives/GlaivePrimeTwitchSkin":                                                "Glaive Prime Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/LexPrime/LexPrimeTwitchSkin":                                                  "Lex Prime Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/MonkeyKing/WukongDeluxeBSkin":                                                 "Wukong Qitian Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Necramech/TefilahIridosSkin":                                                  "Iridos Voidrig Necramech Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Rifles/BratonPrimeTwitchSkin":                                                 "Braton Prime Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Shotguns/StrunTwitchSkin":                                                     "Strun Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Swords/SilvaAegisTwitchSkin":                                                  "Silva & Aegis Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/VastoPrime/VastoPrimeTwitchSkin":                                              "Vasto Prime Iridos Skin",
    # Cosmetics — Promo/Twitch skins
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/AkjagaraIridosSkin":                                              "Akjagara Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/ExcaliburTwitchSkin":                                             "Excalibur Prominence Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/LisetSkinTwitch":                                                 "Liset Verv Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/OgrisTwitchSkin":                                                 "Ogris Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/PyranaTwitchSkin":                                                "Pyrana Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/TigrisTwitchSkin":                                               "Tigris Prominence Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021AfurisSkin":                                            "Afuris Verv Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021LandinCraftSkin":                                       "Landing Craft Verv Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021LatronSkin":                                            "Latron Verv Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021NikanasSkin":                                           "Nikana Verv Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2023BoltoSkin":                                             "Bolto Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2023OdonataWingSkin":                                       "Odonata Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2023TrinityIridosSkin":                                     "Trinity Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2024DethcubeIridosSkin":                                    "Dethcube Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2024SomaTwitchSkin":                                        "Soma Iridos Skin",
    "/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2024ValkyrIridosSkin":                                      "Valkyr Iridos Skin",
    # Cosmetics — sugatras & sigils
    "/Lotus/StoreItems/Upgrades/Skins/MeleeDangles/ScrollingPrimeMeleeDangle":                                       "Naviga Prime Sugatra",
    "/Lotus/StoreItems/Upgrades/Skins/MeleeDangles/TwitchPrimeMeleeDangle":                                          "Spektaka Prime Sugatra",
    "/Lotus/StoreItems/Upgrades/Skins/Sigils/PromoTwitchEmblemB":                                                    "Iridos Emblem",
    "/Lotus/StoreItems/Upgrades/Skins/Sigils/PromoTwitchEmblemC":                                                    "Verv Emblem",
    "/Lotus/StoreItems/Upgrades/Skins/Sigils/PromoTwitchEmblemD":                                                    "Prominence Emblem",
    # Cosmetics — syandanas & colour pickers
    "/Lotus/StoreItems/Characters/Tenno/Accessory/Scarves/U17IntermScarf/IridosUdyatSkin/UdyatPrimeGamingSyandana":  "Udyat Iridos Syandana",
    "/Lotus/StoreItems/Types/StoreItems/SuitCustomizations/ColourPickerEmberHeirloom":                               "Ember Heirloom",
    "/Lotus/StoreItems/Types/StoreItems/SuitCustomizations/ColourPickerPrimeDayItemA":                               "Spektaka",
    "/Lotus/StoreItems/Types/StoreItems/SuitCustomizations/ColourPickerPrimeDayItemB":                               "Spektaka Prime",
    # Cosmetics — glyphs & heirlooms
    "/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomEmberGlyph":                                            "Ember Heirloom Glyph",
    "/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomRhinoGlyph":                                            "Rhino Heirloom Glyph",
    "/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomValkyrGlyph":                                           "Valkyr Heirloom Glyph",
    "/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomVaubanGlyph":                                           "Vauban Heirloom Glyph",
    "/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomVaubanGlyphSumo":                                       "Vauban Heirloom Tondo Glyph",
    # Cosmetics — ship decos & wallpapers
    "/Lotus/StoreItems/Types/Game/QuartersWallpapers/TwitchPrimeNovemberWallpaper":                                  "Iridos Quarters Wallpaper",
    "/Lotus/StoreItems/Types/Items/ShipDecos/TwitchPrimeOctoberDisplay":                                             "Voidshell Decoration",
    "/Lotus/StoreItems/Types/Items/ShipDecos/TwitchPrimeOctoberNoggles/NogglesDisplayTwitchPrime":                   "Noggle Statue - Grendel Iridos",
    # Store packages
    "/Lotus/StoreItems/Types/StoreItems/Packages/MegaPrimeVault/LastChanceItemA":                                    "Last Chance Offerings",
    "/Lotus/StoreItems/Types/StoreItems/Packages/MegaPrimeVault/LastChanceItemB":                                    "Varzia's Offerings - Part 2",
    "/Lotus/StoreItems/Types/StoreItems/Packages/MegaPrimeVault/LastChanceItemC":                                    "Varzia's Offerings",
}

# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def _parse_date(val: Any) -> datetime | None:
    """
    Parse Warframe's BSON-style date:
      {"$date": {"$numberLong": "1234567890000"}}   — milliseconds
      {"$date": 1234567890000}                      — milliseconds int
      1234567890                                    — seconds int
    Returns UTC datetime or None.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        # Assume seconds if < 1e11, else milliseconds
        ts = val / 1000 if val > 1e11 else val
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    if isinstance(val, dict):
        inner = val.get("$date")
        if isinstance(inner, dict):
            ms = int(inner.get("$numberLong", 0))
        elif isinstance(inner, (int, float)):
            ms = int(inner)
        else:
            return None
        return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return None


def _eta(expiry: datetime | None) -> str:
    """Human-readable time-until from now (UTC)."""
    if expiry is None:
        return "?"
    now = datetime.now(tz=timezone.utc)
    delta = expiry - now
    total = int(delta.total_seconds())
    if total <= 0:
        return "Expired"
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    mins = rem // 60
    if days:
        return f"{days}d {hours}h"
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


# ---------------------------------------------------------------------------
# Node name lookup
# ---------------------------------------------------------------------------

def _load_solnode_map() -> dict[str, dict]:
    p = DATA_DIR / "solnode_map.json"
    if p.exists():
        return json.loads(p.read_text())
    return {}


def _item_name(path: str) -> str:
    """Resolve a /Lotus/... item path to a display name, falling back to the last path segment."""
    if path in ITEM_NAMES:
        return ITEM_NAMES[path]
    return path.rstrip("/").rsplit("/", 1)[-1]


def _node_display(node_key: str, solnode_map: dict[str, dict]) -> str:
    """
    Convert a node key to human-readable 'Name (Planet)'.
    node_key may be:
      - 'SolNode1' → look up in ALL_NODES, then solnode_map
      - '/Lotus/Levels/.../MercuryCapture' → strip path, look up last segment
      - 'MercuryCapture' → look up directly
    """
    key = node_key.rstrip("/").rsplit("/", 1)[-1] if "/" in node_key else node_key

    if key in ALL_NODES:
        return ALL_NODES[key]
    if node_key in ALL_NODES:
        return ALL_NODES[node_key]

    info = solnode_map.get(key) or solnode_map.get(node_key) or {}
    name = info.get("name", "")
    planet = info.get("planet", "")

    if name and planet:
        return f"{name} ({planet})"
    if name:
        return name

    # Fallback: humanise the key itself (e.g. 'SolNode1' stays as-is; 'MercuryCapture' → 'Capture (Mercury)')
    # Try to split CamelCase planet prefix
    match = re.match(r"([A-Z][a-z]+)(.+)", key)
    if match:
        planet_hint, rest = match.groups()
        # un-camel the mission
        mission = re.sub(r"([A-Z])", r" \1", rest).strip()
        return f"{mission} ({planet_hint})"
    return key


def _mission_type(type_key: str) -> str:
    """Strip Lotus path and look up human name. Handles both MT_RESCUE and path-suffix styles."""
    suffix = type_key.rstrip("/").rsplit("/", 1)[-1] if "/" in type_key else type_key
    if suffix in MT_MISSION_TYPES:
        return MT_MISSION_TYPES[suffix]
    return MISSION_TYPES.get(suffix, suffix)


def _faction(faction_key: str) -> str:
    return FACTION_NAMES.get(faction_key, faction_key)


# ---------------------------------------------------------------------------
# Section parsers
# ---------------------------------------------------------------------------

def _parse_fissures(raw: list, solnode_map: dict) -> list[dict]:
    out = []
    for f in raw:
        expiry = _parse_date(f.get("Expiry"))
        if expiry and expiry < datetime.now(tz=timezone.utc):
            continue  # skip expired

        modifier = f.get("Modifier", "")
        tier = FISSURE_TIERS.get(modifier, modifier)

        mission_key = f.get("MissionType", "")
        is_storm = "VoidStorm" in mission_key or "VoidArmageddon" in mission_key or "VoidCascade" in mission_key or "VoidFlood" in mission_key
        is_hard = f.get("Hard", False)

        out.append({
            "node":         _node_display(f.get("Node", ""), solnode_map),
            "mission_type": _mission_type(mission_key),
            "enemy":        _faction(f.get("Faction", "")) or NODE_FACTION.get(f.get("Node", ""), ""),
            "tier":         tier,
            "eta":          _eta(expiry),
            "expiry_ts":    expiry.timestamp() if expiry else 0,
            "is_storm":     is_storm,
            "is_steel_path": is_hard,
        })

    # Sort: Lith → Meso → Neo → Axi → others
    tier_order = {"Lith": 0, "Meso": 1, "Neo": 2, "Axi": 3, "Requiem": 4, "Omnia": 5}
    out.sort(key=lambda x: tier_order.get(x["tier"], 99))
    return out


def _parse_alerts(raw: list, solnode_map: dict) -> list[dict]:
    out = []
    for a in raw:
        expiry = _parse_date(a.get("Expiry"))
        if expiry and expiry < datetime.now(tz=timezone.utc):
            continue

        mission = a.get("MissionInfo", {})
        reward = mission.get("missionReward", {})
        items = reward.get("items", []) or []
        counted = reward.get("countedItems", []) or []
        credits = reward.get("credits", 0)

        reward_parts = []
        for ci in counted:
            ct = ci.get("ItemCount", 1)
            nm = _item_name(ci.get("ItemType", ""))
            reward_parts.append(f"{ct}× {nm}" if ct > 1 else nm)
        for it in items:
            reward_parts.append(_item_name(it))
        if credits:
            reward_parts.append(f"{credits:,} Credits")

        out.append({
            "node":         _node_display(mission.get("location", ""), solnode_map),
            "mission_type": _mission_type(mission.get("missionType", "")),
            "faction":      _faction(mission.get("faction", "")),
            "reward":       ", ".join(reward_parts) or "Unknown",
            "eta":          _eta(expiry),
        })
    return out


def _parse_sortie(raw: list, solnode_map: dict) -> dict | None:
    if not raw:
        return None
    s = raw[0]
    expiry = _parse_date(s.get("Expiry"))
    variants = s.get("Variants", [])
    missions = []
    for v in variants:
        mod_key = v.get("modifierType", "")
        missions.append({
            "node":         _node_display(v.get("node", ""), solnode_map),
            "mission_type": _mission_type(v.get("missionType", "")),
            "modifier":     SORTIE_MODIFIERS.get(mod_key, mod_key),
        })
    boss_key = s.get("Boss", "")
    boss = SORTIE_BOSSES.get(boss_key, boss_key.rstrip("/").rsplit("/", 1)[-1].replace("Boss", "").strip())
    faction_key = s.get("Faction", "")
    faction = _faction(faction_key) or BOSS_FACTION.get(boss_key, "")
    return {
        "boss":     boss or "Unknown",
        "faction":  faction,
        "eta":      _eta(expiry),
        "missions": missions,
    }


def _parse_archon_hunt(raw: list, solnode_map: dict) -> dict | None:
    # LiteSorties[0] — uses Missions[] with missionType + node, no Variants, no modifier
    if not raw:
        return None
    s = raw[0]
    expiry = _parse_date(s.get("Expiry"))
    missions_raw = s.get("Missions", [])
    missions = []
    for m in missions_raw:
        missions.append({
            "node":         _node_display(m.get("node", ""), solnode_map),
            "mission_type": _mission_type(m.get("missionType", "")),
            "modifier":     "",
        })
    boss_key = s.get("Boss", "")
    boss = SORTIE_BOSSES.get(boss_key, boss_key.rstrip("/").rsplit("/", 1)[-1])
    faction_key = s.get("Faction", "")
    faction = _faction(faction_key) or BOSS_FACTION.get(boss_key, "")
    return {
        "boss":     boss or "Unknown",
        "faction":  faction,
        "eta":      _eta(expiry),
        "missions": missions,
    }


def _parse_void_trader(raw: list, solnode_map: dict) -> dict:
    if not raw:
        return {"active": False, "eta": "Unknown", "node": "", "inventory": []}

    trader = raw[0]
    activation = _parse_date(trader.get("Activation"))
    expiry = _parse_date(trader.get("Expiry"))
    now = datetime.now(tz=timezone.utc)

    active = activation is not None and activation <= now and (expiry is None or expiry > now)

    inventory = []
    for item in trader.get("Manifest", []):
        item_path = item.get("ItemType", "")
        item_name = _item_name(item_path)
        inventory.append({
            "item":    item_name,
            "ducats":  item.get("PrimePrice", 0),
            "credits": item.get("RegularPrice", 0),
        })

    return {
        "active":    active,
        "node":      _node_display(trader.get("Node", ""), solnode_map),
        "eta":       _eta(expiry if active else activation),
        "arrives":   activation.isoformat() if activation else None,
        "departs":   expiry.isoformat() if expiry else None,
        "inventory": inventory,
    }


def _parse_nightwave(raw: list) -> dict | None:
    # Nightwave is a syndicate; look for the RadioLegion tag
    nw = next((s for s in raw if "RadioLegion" in s.get("Tag", "")), None)
    if not nw:
        return None

    expiry = _parse_date(nw.get("Expiry"))
    challenges = []
    for ch in nw.get("ActiveChallenges", []):
        ch_expiry = _parse_date(ch.get("Expiry"))
        info = ch.get("Challenge", "")
        # Challenge path like /Lotus/Types/Challenges/...
        title = info.rstrip("/").rsplit("/", 1)[-1] if "/" in info else info
        challenges.append({
            "title":      title,
            "reputation": ch.get("xpAmount", 0),
            "is_daily":   ch.get("isDaily", False),
            "is_elite":   ch.get("isElite", False),
            "eta":        _eta(ch_expiry),
        })

    return {
        "season": nw.get("Season", 0),
        "phase":  nw.get("Phase", 0),
        "eta":    _eta(expiry),
        "active_challenges": challenges,
    }


def _parse_cycles(raw: dict) -> list[dict]:
    from datetime import timedelta
    cycles: list[dict] = []
    now = datetime.now(tz=timezone.utc)
    ts  = now.timestamp()

    try:  # Cetus — epoch=1510444800, cycle=8998s, day=5998s, night=3000s
        epoch_s, cycle_s, day_s = 1510444800, 8998, 5998
        elapsed   = int(ts - epoch_s) % cycle_s
        is_night  = elapsed >= day_s
        secs_left = (cycle_s - elapsed) if is_night else (day_s - elapsed)
        cycles.append({"location": "Cetus", "state": "Night" if is_night else "Day", "eta": _eta(now + timedelta(seconds=secs_left))})
    except Exception: pass

    try:  # Orb Vallis — epoch=1542318000, cycle=1600s, warm=400s
        epoch_s, cycle_s, warm_s = 1542318000, 1600, 400
        elapsed   = int(ts - epoch_s) % cycle_s
        is_warm   = elapsed < warm_s
        secs_left = (warm_s - elapsed) if is_warm else (cycle_s - elapsed)
        cycles.append({"location": "Orb Vallis", "state": "Warm" if is_warm else "Cold", "eta": _eta(now + timedelta(seconds=secs_left))})
    except Exception: pass

    try:  # Cambion Drift — epoch=1604085600, cycle=8998s, fass=4499s
        epoch_s, cycle_s, fass_s = 1604085600, 8998, 4499
        elapsed   = int(ts - epoch_s) % cycle_s
        is_fass   = elapsed < fass_s
        secs_left = (fass_s - elapsed) if is_fass else (cycle_s - elapsed)
        cycles.append({"location": "Cambion Drift", "state": "Fass" if is_fass else "Vome", "eta": _eta(now + timedelta(seconds=secs_left))})
    except Exception: pass

    try:  # Earth — epoch=0, cycle=14400s, day=10800s, night=3600s
        elapsed   = int(ts) % 14400
        is_day    = elapsed < 10800
        secs_left = (10800 - elapsed) if is_day else (14400 - elapsed)
        cycles.append({"location": "Earth", "state": "Day" if is_day else "Night", "eta": _eta(now + timedelta(seconds=secs_left))})
    except Exception: pass

    try:  # Duviri — server-authoritative, reads DuviriCycle from worldstate API
        d = raw.get("DuviriCycle")
        if isinstance(d, dict):
            expiry_dt = _parse_date(d.get("expiry") or d.get("Expiry"))
            state = str(d.get("state", "")).strip().capitalize() or "Unknown"
            cycles.append({"location": "Duviri", "state": state, "eta": _eta(expiry_dt)})
    except Exception: pass

    try:  # Zariman — from raw API
        z = raw.get("ZarimanCycle")
        if isinstance(z, dict):
            expiry_dt = _parse_date(z.get("expiry") or z.get("Expiry"))
            is_corpus = str(z.get("state", "grineer")).lower() in ("corpus", "true")
            cycles.append({"location": "Zariman Ten Zero", "state": "Corpus" if is_corpus else "Grineer", "eta": _eta(expiry_dt)})
    except Exception: pass

    return cycles


_NEWS_GENERIC_MESSAGES = {
    "check out the official warframe wiki",
    "visit the official warframe forums",
}


def _parse_news(raw: dict) -> list[dict]:
    """Parse news/announcement entries from Events[].

    Keeps only entries that:
    - Have an English Message (len > 20, not a /Lotus/ path, not a known generic string)
    - Have an image (blank card otherwise)
    - Link to forums.warframe.com, www.warframe.com/news, or warframe.com/updates
    Results are sorted newest-first by Date.
    """
    out: list[dict] = []
    for ev in raw.get("Events", []):
        try:
            messages = ev.get("Messages")
            if not messages:
                continue
            msg_en = ""
            for m in messages:
                if not isinstance(m, dict):
                    continue
                if m.get("LanguageCode", "").lower() in ("en", ""):
                    msg_en = m.get("Message", "")
                    break
            if not msg_en or msg_en.startswith("/Lotus/") or len(msg_en) <= 20:
                continue
            if msg_en.lower().strip() in _NEWS_GENERIC_MESSAGES:
                continue
            url = ev.get("Prop") or ""
            if "warframe.com" not in url:
                continue
            image = ev.get("ImageUrl") or None
            dt = _parse_date(ev.get("Date"))
            out.append({
                "message": msg_en,
                "url":     url,
                "image":   image,
                "date":    dt.isoformat() if dt else None,
                "_dt":     dt,
            })
        except Exception:
            continue
    out.sort(key=lambda x: x["_dt"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    for item in out:
        del item["_dt"]
    return out[:10]


def _debug_news(raw: dict) -> dict:
    """Debug helper — same filter logic as _parse_news but returns accepted + rejected with reasons."""
    accepted: list[dict] = []
    rejected: list[dict] = []
    for ev in raw.get("Events", []):
        try:
            messages = ev.get("Messages")
            if not messages:
                rejected.append({"reason": "no Messages[]"})
                continue
            msg_en = ""
            for m in messages:
                if not isinstance(m, dict):
                    continue
                if m.get("LanguageCode", "").lower() in ("en", ""):
                    msg_en = m.get("Message", "")
                    break
            if not msg_en or msg_en.startswith("/Lotus/") or len(msg_en) <= 20:
                rejected.append({"reason": "message missing/short/Lotus", "message": msg_en})
                continue
            if msg_en.lower().strip() in _NEWS_GENERIC_MESSAGES:
                rejected.append({"reason": "generic message", "message": msg_en})
                continue
            url = ev.get("Prop") or ""
            if "warframe.com" not in url:
                rejected.append({"reason": "url mismatch", "message": msg_en, "url": url})
                continue
            image = ev.get("ImageUrl") or None
            accepted.append({"message": msg_en, "url": url, "image": image})
        except Exception as exc:
            rejected.append({"reason": f"exception: {exc}"})
    return {"accepted": accepted, "rejected": rejected}


def _parse_events(raw: dict) -> list[dict]:
    """Parse active, non-expired game events."""
    out: list[dict] = []
    now = datetime.now(tz=timezone.utc)
    for ev in raw.get("Events", []):
        try:
            expiry = _parse_date(ev.get("Expiry"))
            if expiry and expiry < now:
                continue

            # Name: try Description → Messages → Tag
            desc = ev.get("Description", {})
            name = (desc.get("value", "") if isinstance(desc, dict) else str(desc)) if desc else ""
            if not name:
                msgs = ev.get("Messages", [])
                if msgs and isinstance(msgs[0], dict):
                    name = msgs[0].get("message", "")
            if not name:
                name = ev.get("Tag", "")
            if not name:
                continue

            # Reward hint
            rewards = ev.get("Rewards", [])
            reward = ""
            if rewards and isinstance(rewards[0], dict):
                r = rewards[0]
                items = r.get("items") or r.get("Items") or []
                credits = r.get("credits", r.get("Credits", 0))
                if items:
                    first = items[0]
                    reward = first if isinstance(first, str) else first.get("ItemType", "").rsplit("/", 1)[-1]
                elif credits:
                    reward = f"{int(credits):,} Credits"

            out.append({
                "name":   name[:60],
                "eta":    _eta(expiry),
                "reward": reward[:50],
            })
        except Exception:
            continue
    return out[:10]


def _parse_invasions(raw: list, solnode_map: dict) -> list[dict]:
    out = []
    for inv in raw:
        if inv.get("Completed", False):
            continue
        expiry = _parse_date(inv.get("Expiry"))

        def _reward(reward: dict | list) -> str:
            if not isinstance(reward, dict):
                reward = {}
            counted = reward.get("countedItems", [])
            items = reward.get("items", [])
            parts = []
            for ci in counted:
                ct = ci.get("ItemCount", 1)
                nm = _item_name(ci.get("ItemType", ""))
                parts.append(f"{ct}× {nm}" if ct > 1 else nm)
            for it in items:
                parts.append(_item_name(it))
            cr = reward.get("credits", 0)
            if cr:
                parts.append(f"{cr:,} cr")
            return ", ".join(parts)

        attacker_faction = inv.get("Faction", "")
        defender_faction = inv.get("DefenderFaction", "")
        count = inv.get("Count", 0)
        required = inv.get("Goal", 1)
        progress = min(100.0, max(0.0, abs(count) / max(required, 1) * 100))

        out.append({
            "node":            _node_display(inv.get("Node", ""), solnode_map),
            "attacker":        _faction(attacker_faction),
            "defender":        _faction(defender_faction),
            "attacker_reward": _reward(inv.get("AttackerReward", {})),
            "defender_reward": _reward(inv.get("DefenderReward", {})),
            "progress":        round(progress, 1),
            "eta":             _eta(expiry),
            "vs_infestation":  attacker_faction == "FC_INFESTATION" or defender_faction == "FC_INFESTATION",
        })
    return out


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse(raw: dict) -> dict:
    """Parse a raw worldstate dict → clean structured dict."""
    solnode_map = _load_solnode_map()

    return {
        "fissures":    _parse_fissures(raw.get("ActiveMissions", []), solnode_map),
        "alerts":      _parse_alerts(raw.get("Alerts", []), solnode_map),
        "sortie":      _parse_sortie(raw.get("Sorties", []), solnode_map),
        "archon_hunt": _parse_archon_hunt(raw.get("LiteSorties", []), solnode_map),
        "void_trader": _parse_void_trader(raw.get("VoidTraders", []), solnode_map),
        "nightwave":   _parse_nightwave(raw.get("SyndicateMissions", [])),
        "invasions":   _parse_invasions(raw.get("Invasions", []), solnode_map),
        "cycles":      _parse_cycles(raw),
        "events":      _parse_events(raw),
        "news":        _parse_news(raw),
    }


def main() -> None:
    raw_path = DATA_DIR / "worldstate_raw.json"
    if not raw_path.exists():
        print(f"✗ {raw_path} not found.")
        print("  Run:  python scripts/fetch_worldstate.py")
        print("  Or download manually and save as data/worldstate_raw.json")
        return

    print(f"Parsing {raw_path} …")
    raw = json.loads(raw_path.read_text())
    result = parse(raw)

    out = DATA_DIR / "worldstate.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"✓ Saved → {out}")

    # Summary
    print(f"  Fissures:   {len(result['fissures'])}")
    print(f"  Alerts:     {len(result['alerts'])}")
    print(f"  Sortie:     {'yes' if result['sortie'] else 'no'}")
    print(f"  Archon Hunt:{'yes' if result['archon_hunt'] else 'no'}")
    print(f"  Void Trader: {'active' if result.get('void_trader', {}).get('active') else 'inactive'}")
    nw = result.get("nightwave")
    print(f"  Nightwave:  {len(nw['active_challenges']) if nw else 0} challenges")
    print(f"  Invasions:  {len(result['invasions'])}")


if __name__ == "__main__":
    main()
