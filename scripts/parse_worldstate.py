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
    "SORTIE_MODIFIER_EXPLOSION":        "Environmental Hazard: Explosion",
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
    "SolNode128":   "E Gate (Venus)",
    "SolNode902":   "Montes (Venus)",
    "SolNode101":   "Kiliken (Venus)",
    "SolNode22":    "Tessera (Venus)",
    "SolNode123":   "V Prime (Venus)",
    "SolNode23":    "Cytherean (Venus)",
    "SolNode66":    "Unda (Venus)",
    "SolNode107":   "Venera (Venus)",
    "SolNode109":   "Linea (Venus)",
    "SolNode61":    "Ishtar (Venus)",
    "SolNode2":     "Aphrodite (Venus)",
    "SolNode104":   "Fossa (Venus)",
    "ClanNode1":    "Malva (Venus)",
    "ClanNode0":    "Romula (Venus)",
    "SolNode129":   "Orb Vallis (Venus)",
    "SolNode239":   "Vesper Relay (Venus)",
    # Earth
    "SolNode27":    "E Prime (Earth)",
    "SolNode89":    "Mariana (Earth)",
    "SolNode26":    "Lith (Earth)",
    "SolNode903":   "Erpo (Earth)",
    "SolNode85":    "Gaia (Earth)",
    "SolNode39":    "Everest (Earth)",
    "SolNode63":    "Mantle (Earth)",
    "SolNode79":    "Cambria (Earth)",
    "SolNode59":    "Eurasia (Earth)",
    "SolNode15":    "Pacific (Earth)",
    "SolNode75":    "Cervantes (Earth)",
    "SolNode451":   "Saya's Visions (Earth)",
    "ClanNode3":    "Tikal (Earth)",
    "ClanNode2":    "Coba (Earth)",
    "SolNode228":   "Plains of Eidolon (Earth)",
    "SolNode24":    "Oro (Earth)",
    "EarthHUB":     "Strata Relay (Earth)",
    # Mars
    "SolNode11":    "Tharsis (Mars)",
    "SolNode58":    "Hellas (Mars)",
    "SolNode106":   "Alator (Mars)",
    "SolNode46":    "Spear (Mars)",
    "SolNode904":   "Syrtis (Mars)",
    "SolNode113":   "Ares (Mars)",
    "SolNode41":    "Arval (Mars)",
    "SolNode65":    "Gradivus (Mars)",
    "SolNode16":    "Augustus (Mars)",
    "SolNode45":    "Ara (Mars)",
    "SolNode36":    "Martialis (Mars)",
    "ClanNode8":    "Kadesh (Mars)",
    "ClanNode9":    "Wahiba (Mars)",
    "SolNode99":    "War (Mars)",
    "SolNode68":    "Vallis (Mars)",
    "SolNode14":    "Ultor (Mars)",
    "SolNode30":    "Olympus (Mars)",
    "SolNode450":   "Tyana Pass (Mars)",
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
    # Ceres
    "SolNode132":   "Bode (Ceres)",
    "SolNode131":   "Pallas (Ceres)",
    "SolNode147":   "Cinxia (Ceres)",
    "SolNode149":   "Casta (Ceres)",
    "SolNode146":   "Draco (Ceres)",
    "SolNode137":   "Nuovo (Ceres)",
    "SolNode140":   "Kiste (Ceres)",
    "SolNode139":   "Lex (Ceres)",
    "SolNode144":   "Exta (Ceres)",
    "SolNode141":   "Ker (Ceres)",
    "SolNode138":   "Ludi (Ceres)",
    "SolNode135":   "Thon (Ceres)",
    "ClanNode22":   "Seimeni (Ceres)",
    "ClanNode23":   "Gabii (Ceres)",
    # Jupiter
    "SolNode10":    "Thebe (Jupiter)",
    "SolNode126":   "Metis (Jupiter)",
    "SolNode125":   "Io (Jupiter)",
    "SolNode25":    "Callisto (Jupiter)",
    "SolNode905":   "Galilea (Jupiter)",
    "SolNode100":   "Elara (Jupiter)",
    "SolNode73":    "Ananke (Jupiter)",
    "SolNode74":    "Carme (Jupiter)",
    "SolNode121":   "Carpo (Jupiter)",
    "SolNode97":    "Amalthea (Jupiter)",
    "SolNode53":    "Themisto (Jupiter)",
    "SolNode88":    "Adrastea (Jupiter)",
    "ClanNode4":    "Sinai (Jupiter)",
    "ClanNode5":    "Cameria (Jupiter)",
    "SolNode87":    "Ganymede (Jupiter)",
    "SolNode740":   "The Ropalolyst (Jupiter)",
    # Saturn
    "SolNode906":   "Pandora (Saturn)",
    "SolNode67":    "Dione (Saturn)",
    "SolNode70":    "Cassini (Saturn)",
    "SolNode96":    "Titan (Saturn)",
    "SolNode18":    "Rhea (Saturn)",
    "SolNode42":    "Helene (Saturn)",
    "SolNode20":    "Telesto (Saturn)",
    "SolNode31":    "Anthe (Saturn)",
    "SolNode50":    "Numa (Saturn)",
    "SolNode93":    "Keeler (Saturn)",
    "SolNode19":    "Enceladus (Saturn)",
    "SolNode32":    "Tethys (Saturn)",
    "SolNode82":    "Calypso (Saturn)",
    "ClanNode13":   "Piscinas (Saturn)",
    "ClanNode12":   "Caracol (Saturn)",
    "SaturnHUB":    "Kronia Relay (Saturn)",
    # Uranus
    "SolNode34":    "Sycorax (Uranus)",
    "SolNode122":   "Stephano (Uranus)",
    "SolNode907":   "Caelus (Uranus)",
    "SolNode64":    "Umbriel (Uranus)",
    "SolNode69":    "Ophelia (Uranus)",
    "SolNode60":    "Caliban (Uranus)",
    "SolNode33":    "Ariel (Uranus)",
    "ClanNode17":   "Assur (Uranus)",
    "SolNode98":    "Desdemona (Uranus)",
    "SolNode9":     "Rosalind (Uranus)",
    "SolNode83":    "Cressida (Uranus)",
    "SolNode114":   "Puck (Uranus)",
    "SolNode105":   "Titania (Uranus)",
    "ClanNode16":   "Ur (Uranus)",
    "SolNode723":   "Brutus (Uranus)",
    # Neptune
    "SolNode118":   "Laomedeia (Neptune)",
    "SolNode1":     "Galatea (Neptune)",
    "SolNode6":     "Despina (Neptune)",
    "SolNode17":    "Proteus (Neptune)",
    "SolNode908":   "Salacia (Neptune)",
    "SolNode78":    "Triton (Neptune)",
    "SolNode49":    "Larissa (Neptune)",
    "SolNode57":    "Sao (Neptune)",
    "SolNode62":    "Neso (Neptune)",
    "SolNode84":    "Nereid (Neptune)",
    "SolNode127":   "Psamathe (Neptune)",
    "ClanNode21":   "Kelashin (Neptune)",
    "ClanNode20":   "Yursa (Neptune)",
    # Pluto
    "SolNode38":    "Minthe (Pluto)",
    "SolNode76":    "Hydra (Pluto)",
    "SolNode43":    "Cerberus (Pluto)",
    "SolNode72":    "Outer Terminus (Pluto)",
    "SolNode81":    "Palus (Pluto)",
    "SolNode102":   "Oceanum (Pluto)",
    "SolNode21":    "Narcissus (Pluto)",
    "SolNode56":    "Cypress (Pluto)",
    "SolNode4":     "Acheron (Pluto)",
    "SolNode48":    "Regna (Pluto)",
    "ClanNode24":   "Sechura (Pluto)",
    "ClanNode25":   "Hieracon (Pluto)",
    "SolNode51":    "Hades (Pluto)",
    "PlutoHUB":     "Orcus Relay (Pluto)",
    # Sedna
    "SolNode189":   "Naga (Sedna)",
    "SolNode185":   "Berehynia (Sedna)",
    "SolNode195":   "Hydron (Sedna)",
    "SolNode187":   "Selkie (Sedna)",
    "SolNode184":   "Rusalka (Sedna)",
    "SolNode181":   "Adaro (Sedna)",
    "SolNode191":   "Marid (Sedna)",
    "SolNode196":   "Charybdis (Sedna)",
    "SolNode177":   "Kappa (Sedna)",
    "SolNode193":   "Merrow (Sedna)",
    "SolNode188":   "Kelpie (Sedna)",
    "ClanNode15":   "Sangeru (Sedna)",
    "ClanNode14":   "Amarna (Sedna)",
    "SolNode190":   "Nakki (Sedna)",
    "SolNode199":   "Yam (Sedna)",
    "SolNode183":   "Vodyanoi (Sedna)",
    # Europa
    "SolNode209":   "Morax (Europa)",
    "SolNode215":   "Valac (Europa)",
    "SolNode204":   "Armaros (Europa)",
    "SolNode211":   "Ose (Europa)",
    "SolNode212":   "Paimon (Europa)",
    "SolNode216":   "Valefor (Europa)",
    "SolNode214":   "Sorath (Europa)",
    "SolNode217":   "Orias (Europa)",
    "SolNode220":   "Kokabiel (Europa)",
    "SolNode203":   "Abaddon (Europa)",
    "SolNode205":   "Baal (Europa)",
    "SolNode210":   "Naamah (Europa)",
    "ClanNode7":    "Cholistan (Europa)",
    "ClanNode6":    "Larzac (Europa)",
    "EuropaHUB":    "Leonov Relay (Europa)",
    # Lua
    "SolNode309":   "Yuvarium (Lua)",
    "SolNode301":   "Grimaldi (Lua)",
    "SolNode307":   "Zeipel (Lua)",
    "SolNode306":   "Pavlov (Lua)",
    "SolNode305":   "Stöfler (Lua)",
    "SolNode300":   "Plato (Lua)",
    "SolNode302":   "Tycho (Lua)",
    "SolNode304":   "Copernicus (Lua)",
    "SolNode308":   "Apollo (Lua)",
    "SolNode310":   "Circulus (Lua)",
    # Eris
    "SolNode175":   "Naeglar (Eris)",
    "SolNode705":   "Mutalist Alad V Assassinate (Eris)",
    "SolNode172":   "Xini (Eris)",
    "SolNode166":   "Nimus (Eris)",
    "SolNode164":   "Kala-azar (Eris)",
    "SolNode701":   "Jordas Golem Assassinate (Eris)",
    "SolNode153":   "Brugia (Eris)",
    "SolNode162":   "Isos (Eris)",
    "SolNode173":   "Solium (Eris)",
    "SolNode171":   "Saxis (Eris)",
    "SolNode167":   "Oestrus (Eris)",
    "ClanNode18":   "Akkad (Eris)",
    "ClanNode19":   "Zabala (Eris)",
    "ErisHUB":      "Kuiper Relay (Eris)",
    # Void
    "SolNode400":   "Teshub (Void)",
    "SolNode401":   "Hepit (Void)",
    "SolNode402":   "Taranis (Void)",
    "SolNode403":   "Tiwaz (Void)",
    "SolNode404":   "Stribog (Void)",
    "SolNode405":   "Ani (Void)",
    "SolNode406":   "Ukko (Void)",
    "SolNode407":   "Oxomoco (Void)",
    "SolNode408":   "Belenus (Void)",
    "SolNode409":   "Mot (Void)",
    "SolNode410":   "Aten (Void)",
    "SolNode411":   "Marduk (Void)",
    "SolNode412":   "Mithra (Void)",
    # Kuva Fortress (741–747 current IDs; 500–507 kept as fallback)
    "SolNode741":   "Koro (Kuva Fortress)",
    "SolNode742":   "Nabuk (Kuva Fortress)",
    "SolNode743":   "Rotuma (Kuva Fortress)",
    "SolNode744":   "Taveuni (Kuva Fortress)",
    "SolNode745":   "Tamu (Kuva Fortress)",
    "SolNode746":   "Dakata (Kuva Fortress)",
    "SolNode747":   "Pago (Kuva Fortress)",
    "SolNode748":   "Garus (Kuva Fortress)",
    "SolNode500":   "Koro (Kuva Fortress)",
    "SolNode501":   "Nabuk (Kuva Fortress)",
    "SolNode502":   "Taveuni (Kuva Fortress)",
    "SolNode503":   "Pago (Kuva Fortress)",
    "SolNode504":   "Dakata (Kuva Fortress)",
    "SolNode505":   "Rotuma (Kuva Fortress)",
    "SolNode506":   "Tamu (Kuva Fortress)",
    "SolNode507":   "Kuva Survival (Kuva Fortress)",
    # Deimos
    "SolNode706":   "Horend (Deimos)",
    "SolNode707":   "Hyf (Deimos)",
    "SolNode708":   "Phlegyas (Deimos)",
    "SolNode709":   "Dirus (Deimos)",
    "SolNode710":   "Formido (Deimos)",
    "SolNode711":   "Terrorem (Deimos)",
    "SolNode712":   "Magnacidium (Deimos)",
    "SolNode713":   "Exequias (Deimos)",
    "SolNode715":   "Effervo (Deimos)",
    "SolNode716":   "Nex (Deimos)",
    "SolNode717":   "Persto (Deimos)",
    "SolNode718":   "Cambire (Deimos)",
    "SolNode719":   "Munio (Deimos)",
    "SolNode720":   "Testudo (Deimos)",
    "SolNode721":   "Armatus (Deimos)",
    "SolNode229":   "Cambion Drift (Deimos)",
    # Zariman (230–235 current IDs; 780–783 old fallback IDs)
    "SolNode230":   "Everview Arc (Zariman)",
    "SolNode231":   "Halako Perimeter (Zariman)",
    "SolNode232":   "Tuvul Commons (Zariman)",
    "SolNode233":   "Oro Works (Zariman)",
    "SolNode234":   "Dormizone (Zariman)",
    "SolNode235":   "The Greenway (Zariman)",
    "SolNode780":   "Everview Arc (Zariman)",
    "SolNode781":   "Tuvul Commons (Zariman)",
    "SolNode782":   "Oro Works (Zariman)",
    "SolNode783":   "Halako Perimeter (Zariman)",
    # Duviri
    "SolNode751":   "Duviri (Duviri)",
    "SolNode752":   "The Duviri Experience (Duviri)",
    "SolNode753":   "The Lone Story (Duviri)",
    "SolNode754":   "The Circuit (Duviri)",
    "SolNode755":   "The Steel Path Circuit (Duviri)",
    # Railjack Proxima — Earth
    "CrewBattleNode502": "Sover Strait (Earth Proxima)",
    "CrewBattleNode509": "Iota Temple (Earth Proxima)",
    "CrewBattleNode518": "Ogal Cluster (Earth Proxima)",
    "CrewBattleNode519": "Korm's Belt (Earth Proxima)",
    "CrewBattleNode522": "Bendar Cluster (Earth Proxima)",
    "CrewBattleNode556": "Free Flight (Earth Proxima)",
    "CrewBattleNode559": "Technocyte Coda Concert (Earth Proxima)",
    # Railjack Proxima — Venus
    "CrewBattleNode503": "Bifrost Echo (Venus Proxima)",
    "CrewBattleNode511": "Beacon Shield Ring (Venus Proxima)",
    "CrewBattleNode512": "Orvin-Haarc (Venus Proxima)",
    "CrewBattleNode513": "Vesper Strait (Venus Proxima)",
    "CrewBattleNode514": "Falling Glory (Venus Proxima)",
    "CrewBattleNode515": "Luckless Expanse (Venus Proxima)",
    # Railjack Proxima — Saturn
    "CrewBattleNode501": "Mordo Cluster (Saturn Proxima)",
    "CrewBattleNode530": "Kasio's Rest (Saturn Proxima)",
    "CrewBattleNode533": "Nodo Gap (Saturn Proxima)",
    "CrewBattleNode534": "Lupal Pass (Saturn Proxima)",
    "CrewBattleNode535": "Vand Cluster (Saturn Proxima)",
    "CrewBattleNode557": "Kuva Lich Confrontation (Saturn Proxima)",
    # Railjack Proxima — Neptune
    "CrewBattleNode504": "Arva Vector (Neptune Proxima)",
    "CrewBattleNode516": "Nu-gua Mines (Neptune Proxima)",
    "CrewBattleNode521": "Enkidu Ice Drifts (Neptune Proxima)",
    "CrewBattleNode523": "Mammon's Prospect (Neptune Proxima)",
    "CrewBattleNode524": "Sovereign Grasp (Neptune Proxima)",
    "CrewBattleNode525": "Brom Cluster (Neptune Proxima)",
    "CrewBattleNode558": "Sister of Parvos Confrontation (Neptune Proxima)",
    # Railjack Proxima — Pluto
    "CrewBattleNode526": "Khufu Envoy (Pluto Proxima)",
    "CrewBattleNode527": "Seven Sirens (Pluto Proxima)",
    "CrewBattleNode528": "Obol Crossing (Pluto Proxima)",
    "CrewBattleNode529": "Profit Margin (Pluto Proxima)",
    "CrewBattleNode531": "Fenton's Field (Pluto Proxima)",
    "CrewBattleNode536": "Peregrine Axis (Pluto Proxima)",
    # Railjack Proxima — Veil
    "CrewBattleNode538": "Calabash (Veil Proxima)",
    "CrewBattleNode539": "Numina (Veil Proxima)",
    "CrewBattleNode540": "Arc Silver (Veil Proxima)",
    "CrewBattleNode541": "Erato (Veil Proxima)",
    "CrewBattleNode542": "Lu-yan (Veil Proxima)",
    "CrewBattleNode543": "Sabmir Cloud (Veil Proxima)",
    "CrewBattleNode550": "Nsu Grid (Veil Proxima)",
    "CrewBattleNode553": "Flexa (Veil Proxima)",
    "CrewBattleNode554": "H-2 Cloud (Veil Proxima)",
    "CrewBattleNode555": "R-9 Cloud (Veil Proxima)",
}

# Node key → faction name. Used as fallback when worldstate Faction field is absent.
NODE_FACTION: dict[str, str] = {
    # Mercury
    "SolNode94":  "Infested",  "SolNode130": "Infested",  "SolNode119": "Grineer",
    "SolNode12":  "Grineer",   "SolNode103": "Grineer",   "SolNode28":  "Infested",
    "SolNode108": "Grineer",   "SolNode223": "Infested",  "SolNode224": "Grineer",
    "SolNode225": "Grineer",   "SolNode226": "Grineer",   "MercuryHUB": "Neutral",
    # Venus
    "SolNode128": "Corpus",    "SolNode902": "Corpus",    "SolNode101": "Corpus",
    "SolNode22":  "Corpus",    "SolNode123": "Corpus",    "SolNode23":  "Corpus",
    "SolNode66":  "Corpus",    "SolNode107": "Corpus",    "SolNode109": "Corpus",
    "SolNode61":  "Corpus",    "SolNode2":   "Corpus",    "SolNode104": "Corpus",
    "ClanNode1":  "Infested",  "ClanNode0":  "Infested",  "SolNode129": "Corpus",
    "SolNode239": "Neutral",   "VenusHUB":   "Neutral",
    # Earth
    "SolNode27":  "Grineer",   "SolNode89":  "Grineer",   "SolNode26":  "Grineer",
    "SolNode903": "Grineer",   "SolNode85":  "Grineer",   "SolNode39":  "Grineer",
    "SolNode63":  "Grineer",   "SolNode79":  "Grineer",   "SolNode59":  "Grineer",
    "SolNode15":  "Grineer",   "SolNode75":  "Grineer",   "SolNode451": "Grineer",
    "ClanNode3":  "Infested",  "ClanNode2":  "Infested",  "SolNode228": "Neutral",
    "SolNode24":  "Grineer",   "EarthHUB":   "Neutral",
    # Mars
    "SolNode11":  "Grineer",   "SolNode58":  "Grineer",   "SolNode106": "Grineer",
    "SolNode46":  "Grineer",   "SolNode904": "Grineer",   "SolNode113": "Grineer",
    "SolNode41":  "Grineer",   "SolNode65":  "Grineer",   "SolNode16":  "Grineer",
    "SolNode45":  "Grineer",   "SolNode36":  "Grineer",   "ClanNode8":  "Infested",
    "ClanNode9":  "Infested",  "SolNode99":  "Grineer",   "SolNode68":  "Grineer",
    "SolNode14":  "Grineer",   "SolNode30":  "Grineer",   "SolNode450": "Grineer",
    # Phobos
    "SettlementNode1":  "Corpus",  "SettlementNode3":  "Corpus",
    "SettlementNode2":  "Corpus",  "SettlementNode12": "Corpus",
    "SettlementNode10": "Corpus",  "SettlementNode15": "Corpus",
    "SettlementNode11": "Corpus",  "SettlementNode14": "Corpus",
    "ClanNode10":       "Infested","SettlementNode20": "Corpus",
    "ClanNode11":       "Infested",
    # Ceres
    "SolNode132": "Grineer",   "SolNode131": "Grineer",   "SolNode147": "Grineer",
    "SolNode149": "Grineer",   "SolNode146": "Grineer",   "SolNode137": "Grineer",
    "SolNode140": "Grineer",   "SolNode139": "Grineer",   "SolNode144": "Grineer",
    "SolNode141": "Grineer",   "SolNode138": "Grineer",   "SolNode135": "Grineer",
    "ClanNode22": "Infested",  "ClanNode23": "Infested",
    # Jupiter
    "SolNode10":  "Corpus",    "SolNode126": "Corpus",    "SolNode125": "Corpus",
    "SolNode25":  "Corpus",    "SolNode905": "Corpus",    "SolNode100": "Infested",
    "SolNode73":  "Corpus",    "SolNode74":  "Corpus",    "SolNode121": "Corpus",
    "SolNode97":  "Corpus",    "SolNode53":  "Corpus",    "SolNode88":  "Corpus",
    "ClanNode4":  "Infested",  "ClanNode5":  "Infested",  "SolNode87":  "Corpus",
    "SolNode740": "Sentient",
    # Saturn
    "SolNode906": "Corpus",    "SolNode67":  "Infested",  "SolNode70":  "Corpus",
    "SolNode96":  "Grineer",   "SolNode18":  "Grineer",   "SolNode42":  "Grineer",
    "SolNode20":  "Grineer",   "SolNode31":  "Grineer",   "SolNode50":  "Grineer",
    "SolNode93":  "Corpus",    "SolNode19":  "Corpus",    "SolNode32":  "Grineer",
    "SolNode82":  "Grineer",   "ClanNode13": "Infested",  "ClanNode12": "Infested",
    "SaturnHUB":  "Neutral",
    # Uranus
    "SolNode34":  "Grineer",   "SolNode122": "Grineer",   "SolNode907": "Grineer",
    "SolNode64":  "Grineer",   "SolNode69":  "Grineer",   "SolNode60":  "Grineer",
    "SolNode33":  "Grineer",   "ClanNode17": "Infested",  "SolNode98":  "Grineer",
    "SolNode9":   "Grineer",   "SolNode83":  "Grineer",   "SolNode114": "Grineer",
    "SolNode105": "Grineer",   "ClanNode16": "Infested",  "SolNode723": "Grineer",
    # Neptune
    "SolNode118": "Corpus",    "SolNode1":   "Corpus",    "SolNode6":   "Corpus",
    "SolNode17":  "Corpus",    "SolNode908": "Corpus",    "SolNode78":  "Corpus",
    "SolNode49":  "Corpus",    "SolNode57":  "Corpus",    "SolNode62":  "Corpus",
    "SolNode84":  "Corpus",    "SolNode127": "Corpus",    "ClanNode21": "Infested",
    "ClanNode20": "Infested",
    # Pluto
    "SolNode38":  "Corpus",    "SolNode76":  "Corpus",    "SolNode43":  "Corpus",
    "SolNode72":  "Corpus",    "SolNode81":  "Infested",  "SolNode102": "Corpus",
    "SolNode21":  "Corpus",    "SolNode56":  "Corpus",    "SolNode4":   "Corpus",
    "SolNode48":  "Corpus",    "ClanNode24": "Infested",  "ClanNode25": "Infested",
    "SolNode51":  "Corpus",    "PlutoHUB":   "Neutral",
    # Sedna
    "SolNode189": "Grineer",   "SolNode185": "Grineer",   "SolNode195": "Grineer",
    "SolNode187": "Grineer",   "SolNode184": "Grineer",   "SolNode181": "Grineer",
    "SolNode191": "Grineer",   "SolNode196": "Grineer",   "SolNode177": "Grineer",
    "SolNode193": "Grineer",   "SolNode188": "Grineer",   "ClanNode15": "Infested",
    "ClanNode14": "Infested",  "SolNode190": "Grineer",   "SolNode199": "Grineer",
    "SolNode183": "Grineer",
    # Europa
    "SolNode209": "Corpus",    "SolNode215": "Corpus",    "SolNode204": "Corpus",
    "SolNode211": "Corpus",    "SolNode212": "Corpus",    "SolNode216": "Corpus",
    "SolNode214": "Corpus",    "SolNode217": "Corpus",    "SolNode220": "Corpus",
    "SolNode203": "Corpus",    "SolNode205": "Corpus",    "SolNode210": "Corpus",
    "ClanNode7":  "Infested",  "ClanNode6":  "Infested",  "EuropaHUB":  "Neutral",
    # Lua
    "SolNode309": "Orokin",    "SolNode301": "Orokin",    "SolNode307": "Orokin",
    "SolNode306": "Orokin",    "SolNode305": "Orokin",    "SolNode300": "Orokin",
    "SolNode302": "Orokin",    "SolNode304": "Orokin",    "SolNode308": "Orokin",
    "SolNode310": "Orokin",
    # Eris
    "SolNode175": "Infested",  "SolNode705": "Infested",  "SolNode172": "Infested",
    "SolNode166": "Infested",  "SolNode164": "Infested",  "SolNode701": "Infested",
    "SolNode153": "Infested",  "SolNode162": "Infested",  "SolNode173": "Infested",
    "SolNode171": "Infested",  "SolNode167": "Infested",  "ClanNode18": "Infested",
    "ClanNode19": "Infested",  "ErisHUB":    "Neutral",
    # Void
    "SolNode400": "Orokin",    "SolNode401": "Orokin",    "SolNode402": "Orokin",
    "SolNode403": "Orokin",    "SolNode404": "Orokin",    "SolNode405": "Orokin",
    "SolNode406": "Orokin",    "SolNode407": "Orokin",    "SolNode408": "Orokin",
    "SolNode409": "Orokin",    "SolNode410": "Orokin",    "SolNode411": "Orokin",
    "SolNode412": "Orokin",
    # Kuva Fortress
    "SolNode741": "Grineer",   "SolNode742": "Grineer",   "SolNode743": "Grineer",
    "SolNode744": "Grineer",   "SolNode745": "Grineer",   "SolNode746": "Grineer",
    "SolNode747": "Grineer",   "SolNode748": "Grineer",
    "SolNode500": "Grineer",   "SolNode501": "Grineer",   "SolNode502": "Grineer",
    "SolNode503": "Grineer",   "SolNode504": "Grineer",   "SolNode505": "Grineer",
    "SolNode506": "Grineer",   "SolNode507": "Grineer",
    # Deimos
    "SolNode706": "Infested",  "SolNode707": "Infested",  "SolNode708": "Infested",
    "SolNode709": "Infested",  "SolNode710": "Infested",  "SolNode711": "Infested",
    "SolNode712": "Infested",  "SolNode713": "Murmur",    "SolNode715": "Murmur",
    "SolNode716": "Murmur",    "SolNode717": "Murmur",    "SolNode718": "Murmur",
    "SolNode719": "Murmur",    "SolNode720": "Murmur",    "SolNode721": "Murmur",
    "SolNode229": "Neutral",
    # Zariman
    "SolNode230": "Sentient",  "SolNode231": "Sentient",  "SolNode232": "Sentient",
    "SolNode233": "Sentient",  "SolNode234": "Sentient",  "SolNode235": "Sentient",
    "SolNode780": "Sentient",  "SolNode781": "Sentient",  "SolNode782": "Sentient",
    "SolNode783": "Sentient",
    # Duviri
    "SolNode751": "Duviri",    "SolNode752": "Duviri",    "SolNode753": "Duviri",
    "SolNode754": "Duviri",    "SolNode755": "Duviri",
    # Railjack Proxima — Earth (Grineer)
    "CrewBattleNode502": "Grineer",  "CrewBattleNode509": "Grineer",
    "CrewBattleNode518": "Grineer",  "CrewBattleNode519": "Grineer",
    "CrewBattleNode522": "Grineer",  "CrewBattleNode556": "Grineer",
    "CrewBattleNode559": "Infested",
    # Railjack Proxima — Venus (Corpus)
    "CrewBattleNode503": "Corpus",   "CrewBattleNode511": "Corpus",
    "CrewBattleNode512": "Corpus",   "CrewBattleNode513": "Corpus",
    "CrewBattleNode514": "Corpus",   "CrewBattleNode515": "Corpus",
    # Railjack Proxima — Saturn (Grineer)
    "CrewBattleNode501": "Grineer",  "CrewBattleNode530": "Grineer",
    "CrewBattleNode533": "Grineer",  "CrewBattleNode534": "Grineer",
    "CrewBattleNode535": "Grineer",  "CrewBattleNode557": "Grineer",
    # Railjack Proxima — Neptune (Corpus)
    "CrewBattleNode504": "Corpus",   "CrewBattleNode516": "Corpus",
    "CrewBattleNode521": "Corpus",   "CrewBattleNode523": "Corpus",
    "CrewBattleNode524": "Corpus",   "CrewBattleNode525": "Corpus",
    "CrewBattleNode558": "Corpus",
    # Railjack Proxima — Pluto (Corpus)
    "CrewBattleNode526": "Corpus",   "CrewBattleNode527": "Corpus",
    "CrewBattleNode528": "Corpus",   "CrewBattleNode529": "Corpus",
    "CrewBattleNode531": "Corpus",   "CrewBattleNode536": "Corpus",
    # Railjack Proxima — Veil (mixed; Grineer default)
    "CrewBattleNode538": "Grineer",  "CrewBattleNode539": "Grineer",
    "CrewBattleNode540": "Grineer",  "CrewBattleNode541": "Grineer",
    "CrewBattleNode542": "Grineer",  "CrewBattleNode543": "Grineer",
    "CrewBattleNode550": "Grineer",  "CrewBattleNode553": "Corpus",
    "CrewBattleNode554": "Grineer",  "CrewBattleNode555": "Corpus",
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
    raw = path.rstrip("/").rsplit("/", 1)[-1]
    # Split CamelCase into words: "OrokinCatalystBlueprint" → "Orokin Catalyst Blueprint"
    import re
    return re.sub(r'([A-Z])', r' \1', raw).strip()


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

        node_key = f.get("Node", "")
        raw_node = node_key.rsplit("/", 1)[-1] if "/" in node_key else node_key
        mission_key = f.get("MissionType", "")
        mission_display = _mission_type(mission_key)
        # is_storm = display tag only (Void Storm badge); Zariman shares these types
        is_storm = mission_display in {"Void Cascade", "Void Flood", "Void Armageddon"}
        # is_railjack = drives Railjack tab; Proxima nodes OR railjack mission type
        is_railjack = raw_node.startswith("CrewBattleNode") or mission_display in {"Railjack", "Skirmish"}
        is_hard = f.get("Hard", False)

        out.append({
            "node":         _node_display(node_key, solnode_map),
            "mission_type": mission_display,
            "enemy":        _faction(f.get("Faction", "")) or NODE_FACTION.get(node_key, ""),
            "tier":         tier,
            "eta":          _eta(expiry),
            "expiry_ts":    expiry.timestamp() if expiry else 0,
            "is_storm":     is_storm,
            "is_railjack":  is_railjack,
            "is_steel_path": is_hard,
        })

    # Sort: Lith → Meso → Neo → Axi → others
    tier_order = {"Lith": 0, "Meso": 1, "Neo": 2, "Axi": 3, "Requiem": 4, "Omnia": 5}
    out.sort(key=lambda x: tier_order.get(x["tier"], 99))
    return out


def _parse_goals(raw: list) -> list[dict]:
    """Parse anniversary/gift tactical alerts from the Goals array."""
    out: list[dict] = []
    now = datetime.now(tz=timezone.utc)
    for g in raw:
        try:
            tag = g.get("Tag", "")
            # Only process anniversary tactical alert goals
            if "TacAlert" not in tag and "Anniversary" not in tag:
                continue
            expiry = _parse_date(g.get("Expiry"))
            if expiry and expiry < now:
                continue
            reward_obj = g.get("Reward", {})
            items = reward_obj.get("items", []) if isinstance(reward_obj, dict) else []
            reward = _item_name(items[0]) if items else ""
            # Determine display name: ChallengeMode variants are "Elite", others are "Stolen!"
            mission_key = g.get("MissionKeyName", "")
            if "ChallengeMode" in tag or "ChallengeMode" in mission_key or tag.endswith("CMA"):
                name = "Gifts of the Lotus \u2013 Elite"
            else:
                name = "Gifts of the Lotus \u2013 Stolen!"
            out.append({
                "node":         "",
                "mission_type": "",
                "faction":      "",
                "reward":       reward,
                "eta":          _eta(expiry),
                "expiry_ts":    expiry.timestamp() if expiry else 0,
                "is_gift":      True,
                "name":         name,
            })
        except Exception:
            continue
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
            reward_parts.append(f"{credits:,}c")

        node    = _node_display(mission.get("location", ""), solnode_map)
        mtype   = _mission_type(mission.get("missionType", ""))
        faction = _faction(mission.get("faction", ""))
        out.append({
            "node":         node,
            "mission_type": mtype,
            "faction":      faction,
            "reward":       ", ".join(reward_parts) or "Unknown",
            "eta":          _eta(expiry),
            "expiry_ts":    expiry.timestamp() if expiry else 0,
            "is_gift":      False,
            "name":         f"{mtype} \u2014 {node}" if mtype and node else (mtype or node or "Alert"),
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
        "boss":      boss or "Unknown",
        "faction":   faction,
        "eta":       _eta(expiry),
        "expiry_ts": expiry.timestamp() if expiry else 0,
        "missions":  missions,
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
        "boss":      boss or "Unknown",
        "faction":   faction,
        "eta":       _eta(expiry),
        "expiry_ts": expiry.timestamp() if expiry else 0,
        "missions":  missions,
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

    eta_dt = expiry if active else activation
    return {
        "active":    active,
        "node":      _node_display(trader.get("Node", ""), solnode_map),
        "eta":       _eta(eta_dt),
        "expiry_ts": eta_dt.timestamp() if eta_dt else 0,
        "arrives":   activation.isoformat() if activation else None,
        "departs":   expiry.isoformat() if expiry else None,
        "inventory": inventory,
    }


_NW_PREFIX   = re.compile(r"^Season(EliteWeekly|Daily|Weekly)(Permanent|Hard)?")
_NW_TRAIL_NUM = re.compile(r"\d+$")
_NW_NAMES = {
    # Daily
    "Accelerator":            "Accelerator",
    "Agent":                  "Agent",
    "VisitFeaturedDojo":      "Just Visiting",
    "DeployAirSupport":       "Air It Out",
    "DonateLeverian":         "Patron",
    "KillWithMelee":          "Sword Dance",
    "MeleeOnly":              "Swordsman",
    "PrimaryOnly":            "Hands Full",
    "SecondaryOnly":          "Sidearm",
    "KillWithPrimary":        "Mow Them Down",
    "KillWithMagnetic":       "Attractive",
    "KillWithExplosive":      "Detonator",
    "KillWithViral":          "Go Viral",
    "KillWithToxin":          "Poisoner",
    "KillWithCold":           "Deep Freeze",
    "KillWithHeat":           "Arsonist",
    "KillWithElectricity":    "Short Circuit",
    "KillWithGas":            "Biohazard",
    "KillWithCorrosive":      "Meltdown",
    "KillWithRadiation":      "Reactor",
    "KillWithSecondary":      "Smaller is Bigger",
    "KillWithFinisher":       "Executioner",
    "GroundSlam":             "Comet Impact",
    "DeepImpact":             "Deep Impact",
    "AimGlideKills":          "Glider",
    "Headshots":              "Marksman",
    "PlayMinigame":           "Child at Heart",
    "PickupCredits":          "Saver",
    "Shiny":                  "Shiny",
    "Energizing":             "Energizing",
    "Doppelganger":           "Doppelganger",
    "Expressive":             "Expressive",
    "Graffiti":               "Graffiti",
    "Liquidation":            "Liquidation",
    "Loyalty":                "Loyalty",
    "BuildersTouch":          "Builder's Touch",
    "PersonalTouch":          "The Personal Touch",
    "ThrillRider":            "Thrill Rider",
    "ToppingOffTheTank":      "Topping Off the Tank",
    "Trampoline":             "Trampoline",
    "TwoForOne":              "Two For One",
    "WarningShot":            "Warning Shot",
    "Swatter":                "Swatter",
    "PowerTrip":              "Power Trip",
    "Reactor":                "Reactor",
    "Researcher":             "Researcher",
    "Transmutation":          "Everything Old is New Again",
    "AFirmShake":             "A Firm Shake",
    # Weekly / Permanent
    "CompleteMissions":       "Mission Complete",
    "KillEximus":             "Eximus Eliminator",
    "KillEnemies":            "Not a Warning Shot",
    "CompleteTreasures":      "Animator",
    "NightmareMissions":      "Sound Sleeper",
    "SanctuaryOnslaught":     "Test Subject",
    "Conservation":           "Conservationist",
    "CacheSabotage":          "Cache Hunter",
    "MineRare":               "Miner",
    "FishRare":               "Fisher",
    "CompleteBounties":       "Bounty Hunter",
    "EarthBounties":          "Earth Bounty Hunter",
    "VenusBounties":          "Venus Bounty Hunter",
    "ZarimanBounties":        "Zariman Bounty Hunter",
    "VoidArmageddon":         "Eternal Guardian",
    "VoidFlood":              "High Ground",
    "PickupMedallions":       "The Hunt is On",
    "HijackCrewship":         "Confiscated",
    "MarkResource":           "Communicator",
    "KuvaSiphon":             "Don't Fear the Reaper",
    "SilverGroveSpecters":    "Grove Guardian",
    "LuaAscension":           "Ascendant",
    "UnlockDragonVaults":     "Vault Looter",
    "AncientObelisks":        "Ancient Obelisks",
    "BeastSlayer":            "Beast Slayer",
    "Bloodthirsty":           "Bloodthirsty",
    "Collector":              "Collector",
    "DontBlowIt":             "Don't Blow It",
    "EarthFisher":            "Earth Fisher",
    "EarthMiner":             "Earth Miner",
    "Eliminator":             "Eliminator",
    "Explorer":               "Explorer",
    "FeedBeast":              "Feed the Beast",
    "FinellyTuned":           "Finely Tuned",
    "Flawless":               "Flawless",
    "ForwardThinking":        "Forward Thinking",
    "FriendlyFire":           "Friendly Fire",
    "Gatherer":               "Gatherer",
    "GoodFriend":             "Good Friend",
    "Hacker":                 "Hacker",
    "HeavyOrdnance":          "Heavy Ordnance",
    "HorsingAround":          "Horsing Around",
    "IDecree":                "I Decree",
    "Invader":                "Invader",
    "Jailer":                 "Jailer",
    "Kleptomaniac":           "Kleptomaniac",
    "Necralizer":             "Necralizer",
    "NightAndDay":            "Night and Day",
    "NowBoarding":            "Now Boarding",
    "OllieOop":               "Ollie Oop!",
    "Operative":              "Operative",
    "Polarized":              "Polarized",
    "Protector":              "Protector",
    "Rescuer":                "Rescuer",
    "Saboteur":               "Saboteur",
    "SanctuaryResearcher":    "Sanctuary Researcher",
    "SkeletonsInTheCloset":   "Skeletons in the Closet",
    "SortieSpecialist":       "Sortie Specialist",
    "Supporter":              "Supporter",
    "OldWays":                "The Old Ways",
    "TuskThumper":            "Tusk Thumpin'",
    "UnlockRelics":           "Unlock Relics",
    "VaultRaider":            "Vault Raider",
    "VenusFisher":            "Venus Fisher",
    "VenusMiner":             "Venus Miner",
    # Hard / Elite
    "KillOrCaptureRainalyst": "Hydrolyst Hunter",
    "Arbitration":            "Vital Arbiter",
    "CompleteSortie":         "Sortie Expert",
    "NightmareMission":       "Night Terror",
    "SteelPath":              "Cold Steel",
    "ProfitTaker":            "Profit-Taker",
    "EliteSanctuaryOnslaught":"Elite Test Subject",
    "NecramechMissions":      "Rise of the Machine",
    "VoidAngels":             "Fallen Angel",
    "Antiquarian":            "Antiquarian",
    "ArchonHunter":           "Archon Hunter",
    "CeremonialEvolution":    "Ceremonial Evolution",
    "DayTrader":              "Day Trader",
    "Defense":                "Defense",
    "EliteBeastSlayer":       "Elite Beast Slayer",
    "EliteExplorer":          "Elite Explorer",
    "EximusExecutioner":      "Eximus Executioner",
    "HoldYourBreath":         "Hold Your Breath",
    "KillShot":               "Kill Shot",
    "MirrorMirror":           "Mirror, Mirror",
    "NothingButProfit":       "Nothing but Profit",
    "Perplexed":              "Perplexed",
    "ResourceScavenger":      "Resource Scavenger",
    "Speedster":              "Speedster",
    "Survival":               "Survival",
    "Tanked":                 "Tanked",
    "Terminated":             "Terminated",
    "VoluntarySpecimen":      "Voluntary Specimen",
    "ManyMadeWhole":          "The Many Made Whole",
    "PathLessTravelled":      "The Path Less Travelled",
    "PriceOfFreedom":         "The Price of Freedom",
    "WalkWithoutRhythm":      "Walk Without Rhythm",
    "ChooseWisely":           "Choose Wisely",
    "MachineInterference":    "Machine Interference",
    # Keys confirmed from live worldstate (actual path segment differs from assumed)
    "KillEnemiesWithPoison":  "Poisoner",
    "SolveCiphers":           "Hacker",
    "KillEnemiesInMech":      "Necralizer",
    "FriendsSurvival":        "Survival with Friends",
    "Assassin":               "Assassin",
    "Gilded":                 "Gilded",
}

_NW_DESCRIPTIONS = {
    # Daily
    "Accelerator":            "Kill 10 Enemies while Sliding",
    "Agent":                  "Complete a Mission",
    "VisitFeaturedDojo":      "Visit a Featured Dojo",
    "DeployAirSupport":       "Deploy an Air Support Charge in a Mission",
    "DonateLeverian":         "Donate to the Leverian",
    "KillWithMelee":          "Kill 150 Enemies with a Melee Weapon",
    "MeleeOnly":              "Complete a Mission with only a Melee Weapon equipped",
    "PrimaryOnly":            "Complete a Mission with only a Primary Weapon equipped",
    "SecondaryOnly":          "Complete a Mission with only a Secondary Weapon equipped",
    "KillWithPrimary":        "Kill 150 Enemies with a Primary Weapon",
    "KillWithMagnetic":       "Kill 150 Enemies with Magnetic Damage",
    "KillWithExplosive":      "Kill 150 Enemies with Blast Damage",
    "KillWithViral":          "Kill 150 Enemies with Viral Damage",
    "KillWithToxin":          "Kill 150 Enemies with Toxin Damage",
    "KillWithCold":           "Kill 150 Enemies with Cold Damage",
    "KillWithHeat":           "Kill 150 Enemies with Heat Damage",
    "KillWithElectricity":    "Kill 150 Enemies with Electricity Damage",
    "KillWithGas":            "Kill 150 Enemies with Gas Damage",
    "KillWithCorrosive":      "Kill 150 Enemies with Corrosive Damage",
    "KillWithRadiation":      "Kill 150 Enemies with Radiation Damage",
    "KillWithSecondary":      "Kill 150 Enemies with a Secondary Weapon",
    "KillWithFinisher":       "Kill 10 Enemies with Finishers",
    "GroundSlam":             "Kill 20 Enemies with Ground Slams",
    "DeepImpact":             "Suspend 5 or more enemies in the air at once with a Heavy Slam",
    "AimGlideKills":          "Kill 15 Enemies while Aim Gliding",
    "Headshots":              "Kill 40 Enemies with Headshots",
    "PlayMinigame":           "Play a game of Frame Fighter, Happy Zephyr, or Wyrmius",
    "PickupCredits":          "Pick up 15,000 Credits",
    "Shiny":                  "Pick up 8 Mods",
    "Energizing":             "Pick up 20 Energy Orbs",
    "Doppelganger":           "Deploy a Specter",
    "Expressive":             "Play 1 Emote",
    "Graffiti":               "Deploy a Glyph while on a Mission",
    "Liquidation":            "Sell any item in your Inventory for Credits",
    "Loyalty":                "Interact with your Kubrow or Kavat",
    "BuildersTouch":          "Claim an item from your Foundry",
    "PersonalTouch":          "Place 1 decoration in your Orbiter",
    "ThrillRider":            "Kill 20 Enemies while riding a K-Drive, Kaithe, or Merulina",
    "ToppingOffTheTank":      "Defend an Excavator without letting it run out of power",
    "Trampoline":             "Bullet Jump 150 times",
    "TwoForOne":              "Pierce and kill 2 or more enemies in a single Bow shot",
    "WarningShot":            "Kill 200 Enemies",
    "Swatter":                "Kill 3 Drones or Ospreys with your Melee Weapon",
    "PowerTrip":              "Kill 150 Enemies with Abilities",
    "Reactor":                "Kill 150 Enemies with Radiation Damage",
    "Researcher":             "Scan 15 Objects or Enemies",
    "Transmutation":          "Complete 1 Transmutation",
    "AFirmShake":             "Shake the hand of a fellow Tenno using the Handshake Emote",
    # Weekly / Permanent
    "CompleteMissions":       "Complete any 15 Missions",
    "KillEximus":             "Kill 30 Eximus",
    "KillEnemies":            "Kill 500 Enemies",
    "CompleteTreasures":      "Retrieve the Ayatan Statue for Maroo in Maroo's Bazaar",
    "NightmareMissions":      "Complete 3 Nightmare Missions of any type",
    "SanctuaryOnslaught":     "Complete 8 Waves of Sanctuary Onslaught",
    "Conservation":           "Complete 3 different Perfect Animal Captures in Orb Vallis",
    "CacheSabotage":          "Find 6 Caches across any Sabotage Missions",
    "MineRare":               "Mine 3 Rare Gems or Ore in the Plains of Eidolon",
    "FishRare":               "Catch 3 Rare Fish in the Plains of Eidolon",
    "CompleteBounties":       "Complete 3 different Bounties in the Plains of Eidolon",
    "EarthBounties":          "Complete 3 different Bounties in the Plains of Eidolon",
    "VenusBounties":          "Complete 3 different Bounties in the Orb Vallis",
    "ZarimanBounties":        "Complete 4 different Bounties in the Zariman",
    "VoidArmageddon":         "Complete 2 Void Armageddon Missions",
    "VoidFlood":              "Complete 3 Void Flood Missions",
    "PickupMedallions":       "Find 5 Syndicate Medallions",
    "HijackCrewship":         "Hijack a Crewship from the enemy",
    "MarkResource":           "Mark 5 Mods or Resources",
    "KuvaSiphon":             "Complete 3 Kuva Siphon Missions",
    "SilverGroveSpecters":    "Kill 1 Silver Grove Specter",
    "LuaAscension":           "Complete 4 Halls of Ascension on Lua",
    "UnlockDragonVaults":     "Unlock 4 Dragon Key Vaults on Deimos",
    "AncientObelisks":        "Activate 3 Requiem Obelisks on Deimos",
    "BeastSlayer":            "Defeat the Orowyrm",
    "Bloodthirsty":           "Kill 20 enemies in 5 seconds",
    "Collector":              "Collect 100 resources from Duviri",
    "DontBlowIt":             "Complete 12 Conduits in Disruption",
    "EarthFisher":            "Catch 3 Rare Fish in the Plains of Eidolon",
    "EarthMiner":             "Mine 3 Rare Gems or Ore in the Plains of Eidolon",
    "Eliminator":             "Complete 3 Exterminate Missions",
    "Explorer":               "Complete 3 Railjack Missions",
    "FeedBeast":              "Feed the Helminth any Resource",
    "FinellyTuned":           "Play 2 different Shawzin songs in Duviri",
    "Flawless":               "Clear a Railjack Boarding Party without taking damage",
    "ForwardThinking":        "Destroy a Crewship with Forward Artillery",
    "FriendlyFire":           "While piloting a hijacked Crewship, destroy 3 enemy Fighters",
    "Gatherer":               "Collect 4,000 Resources",
    "GoodFriend":             "Help Clem with his weekly mission",
    "Hacker":                 "Hack 10 Consoles",
    "HeavyOrdnance":          "Kill 500 enemies with an Arch Gun",
    "HorsingAround":          "Fly your Kaithe for 1000 meters",
    "IDecree":                "Collect 15 Decrees in a single Duviri session",
    "Invader":                "Complete 6 Invasion Missions of any type",
    "Jailer":                 "Complete 3 Capture Missions",
    "Kleptomaniac":           "Open 30 Lockers",
    "Necralizer":             "Kill 100 enemies with a Necramech",
    "NightAndDay":            "Collect 10 Vome or Fass Residue in the Cambion Drift",
    "NowBoarding":            "Complete 3 different K-Drive Races in Orb Vallis or Cambion Drift",
    "OllieOop":               "Play Ollie's Crash Course and complete a race",
    "Operative":              "Complete 3 Spy Missions",
    "Polarized":              "Polarize with Forma 1 time",
    "Protector":              "Complete 3 Mobile Defense Missions",
    "Rescuer":                "Complete 3 Rescue Missions",
    "Saboteur":               "Complete 3 Sabotage Missions",
    "SanctuaryResearcher":    "Complete 3 Scans for Cephalon Simaris",
    "SkeletonsInTheCloset":   "Kill 50 Dax enemies in Duviri",
    "SortieSpecialist":       "Complete 1 Sortie",
    "Supporter":              "Complete 5 Syndicate Missions",
    "OldWays":                "Complete 1 mission with only a single pistol and a glaive equipped",
    "TuskThumper":            "Kill a Tusk Thumper in the Plains of Eidolon",
    "UnlockRelics":           "Unlock 3 Relics",
    "VaultRaider":            "Complete an Isolation Vault Bounty in the Cambion Drift",
    "VenusFisher":            "Catch 3 Rare Servofish in the Orb Vallis",
    "VenusMiner":             "Mine 3 Rare Gems or Ore in the Orb Vallis",
    # Hard / Elite
    "KillOrCaptureRainalyst": "Kill or Capture an Eidolon Hydrolyst",
    "Arbitration":            "Complete an Arbitration Mission",
    "CompleteSortie":         "Complete 3 Sorties",
    "NightmareMission":       "Complete 5 Nightmare Missions of any type",
    "SteelPath":              "Kill 1000 Enemies on The Steel Path",
    "ProfitTaker":            "Kill the Profit-Taker",
    "EliteSanctuaryOnslaught":"Complete 8 Zones of Elite Sanctuary Onslaught",
    "NecramechMissions":      "Kill 300 enemies using a Necramech without getting destroyed",
    "VoidAngels":             "Defeat 5 Void Angels in the Zariman",
    "Antiquarian":            "Open one of each era of Relic (Lith, Meso, Neo, Axi)",
    "ArchonHunter":           "Complete an Archon Hunt",
    "CeremonialEvolution":    "Evolve any Incarnon weapon in-mission 5 times",
    "DayTrader":              "Win 3 wagers in a row without letting the enemy score in The Index",
    "Defense":                "Complete a Defense mission reaching at least wave 12",
    "EliteBeastSlayer":       "Defeat the Orowyrm in Steel Path",
    "EliteExplorer":          "Complete 8 Railjack Missions",
    "EximusExecutioner":      "Kill 100 Eximus",
    "HoldYourBreath":         "Survive for over 20 minutes in Kuva Survival",
    "KillShot":               "Kill 1,500 Enemies",
    "MirrorMirror":           "Complete 3 waves of Mirror Defense",
    "NothingButProfit":       "Kill The Exploiter Orb",
    "Perplexed":              "Complete 3 puzzles in Duviri",
    "ResourceScavenger":      "Collect 20 different types of Resources",
    "Speedster":              "Finish a Capture mission in less than 90 seconds",
    "Survival":               "Complete a Survival mission reaching at least 20 minutes",
    "Tanked":                 "Defeat an H-09 Efervon Tank",
    "Terminated":             "Destroy 3 Necramech Isolation Vault guardians",
    "VoluntarySpecimen":      "Complete a run of Deep Archimedea or Temporal Archimedea",
    "ManyMadeWhole":          "Exchange 10 Riven Slivers for a Riven Mod",
    "PathLessTravelled":      "Complete 5 Steel Path Missions",
    "PriceOfFreedom":         "Free one Captured Solaris using a Granum Crown",
    "WalkWithoutRhythm":      "Kill a Tusk Thumper Doma in the Plains of Eidolon",
    "ChooseWisely":           "Kill or Convert a Kuva Lich",
    "MachineInterference":    "Complete a Spy mission with 3 manual console hacks and no alarms",
    # Keys confirmed from live worldstate (actual path segment differs from assumed)
    "KillEnemiesWithPoison":  "Kill 150 Enemies with Toxin Damage",
    "SolveCiphers":           "Hack 10 Consoles",
    "KillEnemiesInMech":      "Kill 100 enemies with a Necramech",
    "FriendsSurvival":        "Complete a Survival mission reaching at least 20 minutes with a friend or clanmate",
}

# Elite-specific overrides — for keys shared between weekly and elite tiers
# where the two challenges have different names/descriptions despite the same path segment.
_NW_ELITE_NAMES: dict[str, str] = {
    "KillEximus": "Eximus Executioner",
}

_NW_ELITE_DESCRIPTIONS: dict[str, str] = {
    "KillEximus": "Kill 100 Eximus",
}


def _nw_key(path: str) -> str:
    segment = path.rstrip("/").rsplit("/", 1)[-1] if "/" in path else path
    key = _NW_PREFIX.sub("", segment)
    return _NW_TRAIL_NUM.sub("", key)


def _nw_title(path: str, is_elite: bool = False) -> str:
    key = _nw_key(path)
    if is_elite and key in _NW_ELITE_NAMES:
        return _NW_ELITE_NAMES[key]
    if key in _NW_NAMES:
        return _NW_NAMES[key]
    return re.sub(r"([A-Z])", r" \1", key).strip()


def _nw_description(path: str, is_elite: bool = False) -> str:
    key = _nw_key(path)
    if is_elite and key in _NW_ELITE_DESCRIPTIONS:
        return _NW_ELITE_DESCRIPTIONS[key]
    return _NW_DESCRIPTIONS.get(key, "")


def _parse_nightwave(raw: dict) -> dict | None:
    # Nightwave data lives in top-level SeasonInfo (not SyndicateMissions)
    nw = raw.get("SeasonInfo")
    if not nw:
        return None

    expiry = _parse_date(nw.get("Expiry"))
    challenges = []
    seen_paths: set[str] = set()
    for ch in nw.get("ActiveChallenges", []):
        ch_expiry = _parse_date(ch.get("Expiry"))
        path = ch.get("Challenge", "")
        if path in seen_paths:
            continue
        seen_paths.add(path)
        is_daily = bool(ch.get("Daily", False))
        segment  = path.rstrip("/").rsplit("/", 1)[-1] if "/" in path else path
        is_elite = bool(re.search(r"Season(Weekly|EliteWeekly)?Hard|EliteWeekly", segment)) or bool(ch.get("isElite", False))
        rep = ch.get("xpAmount", 7000 if is_elite else 1000 if is_daily else 4500)

        challenges.append({
            "title":       _nw_title(path, is_elite),
            "description": _nw_description(path, is_elite),
            "reputation":  rep,
            "is_daily":    is_daily,
            "is_elite":    is_elite,
            "eta":         _eta(ch_expiry),
            "expiry_ts":   ch_expiry.timestamp() if ch_expiry else 0,
        })

    return {
        "season":    nw.get("Season", 0),
        "phase":     nw.get("Phase", 0),
        "eta":       _eta(expiry),
        "expiry_ts": expiry.timestamp() if expiry else 0,
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
        cycles.append({"location": "Cetus", "state": "Night" if is_night else "Day", "eta": _eta(now + timedelta(seconds=secs_left)), "expiry_ts": ts + secs_left})
    except Exception: pass

    try:  # Orb Vallis — epoch=1542318000, cycle=1600s, warm=400s
        epoch_s, cycle_s, warm_s = 1542318000, 1600, 400
        elapsed   = int(ts - epoch_s) % cycle_s
        is_warm   = elapsed < warm_s
        secs_left = (warm_s - elapsed) if is_warm else (cycle_s - elapsed)
        cycles.append({"location": "Orb Vallis", "state": "Warm" if is_warm else "Cold", "eta": _eta(now + timedelta(seconds=secs_left)), "expiry_ts": ts + secs_left})
    except Exception: pass

    try:  # Cambion Drift — epoch=1604085600, cycle=8998s, fass=4499s
        epoch_s, cycle_s, fass_s = 1604085600, 8998, 4499
        elapsed   = int(ts - epoch_s) % cycle_s
        is_fass   = elapsed < fass_s
        secs_left = (fass_s - elapsed) if is_fass else (cycle_s - elapsed)
        cycles.append({"location": "Cambion Drift", "state": "Fass" if is_fass else "Vome", "eta": _eta(now + timedelta(seconds=secs_left)), "expiry_ts": ts + secs_left})
    except Exception: pass

    try:  # Earth — epoch=0, cycle=14400s, day=10800s, night=3600s
        elapsed   = int(ts) % 14400
        is_day    = elapsed < 10800
        secs_left = (10800 - elapsed) if is_day else (14400 - elapsed)
        cycles.append({"location": "Earth", "state": "Day" if is_day else "Night", "eta": _eta(now + timedelta(seconds=secs_left)), "expiry_ts": ts + secs_left})
    except Exception: pass

    # ── Zariman Ten Zero ──────────────────────────────────────────────────────
    try:
        epoch_s, cycle_s, corpus_s = 1651018740, 18000, 9000
        elapsed   = int(ts - epoch_s) % cycle_s
        is_corpus = elapsed < corpus_s
        secs_left = (corpus_s - elapsed) if is_corpus else (cycle_s - elapsed)
        cycles.append({
            "location":  "Zariman Ten Zero",
            "state":     "Corpus" if is_corpus else "Grineer",
            "eta":       _eta(now + timedelta(seconds=secs_left)),
            "expiry_ts": ts + secs_left,
        })
    except Exception:
        pass

    # ── Duviri ────────────────────────────────────────────────────────────────
    try:
        _DUVIRI = ["Joy", "Anger", "Envy", "Sorrow", "Fear"]
        epoch_s, cycle_s, phase_s = 1685498400, 36000, 7200
        elapsed   = int(ts - epoch_s) % cycle_s
        idx       = elapsed // phase_s
        secs_left = phase_s - (elapsed % phase_s)
        cycles.append({
            "location":  "Duviri",
            "state":     _DUVIRI[idx],
            "eta":       _eta(now + timedelta(seconds=secs_left)),
            "expiry_ts": ts + secs_left,
        })
    except Exception:
        pass

    return cycles


_NEWS_GENERIC_MESSAGES = {
    "check out the official warframe wiki",
    "visit the official warframe forums",
    "visit the official warframe forums!",
}


def _parse_news(raw: dict) -> list[dict]:
    """Parse news/announcement entries from Events[].

    Keeps only entries that:
    - Have an English Message (len > 20, not a /Lotus/ path, not a known generic string)
    - Message is not in the generic messages set
    Results are sorted newest-first by Date. URL and image are optional.
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

            tag = ev.get("Tag", "")
            is_gift = "LotusGift" in tag or "gift" in name.lower()

            # Reward hint
            rewards = ev.get("Rewards", [])
            reward = ""
            if rewards and isinstance(rewards[0], dict):
                r = rewards[0]
                items = r.get("items") or r.get("Items") or []
                credits = r.get("credits", r.get("Credits", 0))
                if items:
                    first = items[0]
                    reward = first if isinstance(first, str) else _item_name(first.get("ItemType", ""))
                elif credits:
                    reward = f"{int(credits):,}c"

            out.append({
                "name":      name[:60],
                "eta":       _eta(expiry),
                "expiry_ts": expiry.timestamp() if expiry else 0,
                "reward":    reward[:50],
                "is_gift":   is_gift,
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
        "fissures":    _parse_fissures(raw.get("ActiveMissions", []) + raw.get("VoidStorms", []), solnode_map),
        "alerts":      _parse_alerts(raw.get("Alerts", []), solnode_map) + _parse_goals(raw.get("Goals", [])),
        "sortie":      _parse_sortie(raw.get("Sorties", []), solnode_map),
        "archon_hunt": _parse_archon_hunt(raw.get("LiteSorties", []), solnode_map),
        "void_trader": _parse_void_trader(raw.get("VoidTraders", []), solnode_map),
        "nightwave":   _parse_nightwave(raw),
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
