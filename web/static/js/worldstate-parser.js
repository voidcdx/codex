/**
 * Warframe World State Parser
 * All lookup data sourced exclusively from Digital Extremes' Public Export
 * (content.warframe.com/PublicExport/) and api.warframe.com
 *
 * Zero third-party dependencies.
 *
 * Usage:
 *   import { parseWorldState, resolveNode, resolveItem } from './worldstate-parser.js';
 *
 *   const raw = await fetch('https://api.warframe.com/cdn/worldState.php').then(r => r.json());
 *   const parsed = parseWorldState(raw);
 */

// ============================================================
// FACTION MAPPINGS (from DE's ExportRegions factionIndex values)
// ============================================================

const FACTION_INDEX = {
  0: "Grineer",
  1: "Corpus",
  2: "Infested",
  3: "Orokin",
  5: "Sentient",
  7: "Murmur",
  8: "Scaldra",
  9: "Techrot",
  10: "Duviri",
  11: "Neutral"
};

const FACTION_STRING = {
  "FC_GRINEER": "Grineer",
  "FC_CORPUS": "Corpus",
  "FC_INFESTATION": "Infested",
  "FC_CORRUPTED": "Corrupted",
  "FC_OROKIN": "Orokin",
  "FC_SENTIENT": "Sentient",
  "FC_MURMUR": "Murmur"
};

// ============================================================
// MISSION TYPE MAPPINGS (from DE's ExportRegions missionIndex values)
// ============================================================

const MISSION_INDEX = {
  0: "Assassination",
  1: "Exterminate",
  2: "Survival",
  3: "Spy",
  4: "Sabotage",
  5: "Capture",
  7: "Mobile Defense",
  8: "Defense",
  9: "Rescue",
  13: "Interception",
  14: "Hijack",
  15: "Hive",
  17: "Excavation",
  21: "Infested Salvage",
  22: "Arena",
  24: "Pursuit",
  25: "Rush",
  26: "Assault",
  27: "Defection",
  28: "Landscape",
  31: "Circuit",
  33: "Disruption",
  34: "Void Flood",
  35: "Void Cascade",
  36: "Void Armageddon",
  38: "Alchemy",
  40: "Legacyte Harvest",
  41: "Bounty",
  42: "Faceoff",
  43: "Descend",
  44: "Recall",
  45: "Netracell"
};

const MISSION_TYPE_STRING = {
  "MT_ASSASSINATION": "Assassination",
  "MT_EXTERMINATION": "Exterminate",
  "MT_SURVIVAL": "Survival",
  "MT_SPY": "Spy",
  "MT_SABOTAGE": "Sabotage",
  "MT_CAPTURE": "Capture",
  "MT_MOBILE_DEFENSE": "Mobile Defense",
  "MT_DEFENSE": "Defense",
  "MT_RESCUE": "Rescue",
  "MT_INTERCEPTION": "Interception",
  "MT_HIJACK": "Hijack",
  "MT_HIVE": "Hive",
  "MT_EXCAVATION": "Excavation",
  "MT_ARENA": "Arena",
  "MT_PURSUIT": "Pursuit",
  "MT_RUSH": "Rush",
  "MT_ASSAULT": "Assault",
  "MT_DEFECTION": "Defection",
  "MT_LANDSCAPE": "Landscape",
  "MT_DISRUPTION": "Disruption",
  "MT_VOID_FLOOD": "Void Flood",
  "MT_VOID_CASCADE": "Void Cascade",
  "MT_VOID_ARMAGEDDON": "Void Armageddon",
  "MT_ALCHEMY": "Alchemy",
  "MT_INFESTED_SALVAGE": "Infested Salvage",
  "MT_CIRCUIT": "Circuit"
};

// ============================================================
// SORTIE BOSS -> FACTION MAPPINGS
// ============================================================

const SORTIE_BOSSES = {
  "SORTIE_BOSS_VOR": { name: "Captain Vor", faction: "Grineer" },
  "SORTIE_BOSS_HEK": { name: "Councilor Vay Hek", faction: "Grineer" },
  "SORTIE_BOSS_RUK": { name: "General Sargas Ruk", faction: "Grineer" },
  "SORTIE_BOSS_KELA": { name: "Kela De Thaym", faction: "Grineer" },
  "SORTIE_BOSS_TUSK": { name: "Tusk Thumper", faction: "Grineer" },
  "SORTIE_BOSS_KRIL": { name: "Lieutenant Lech Kril", faction: "Grineer" },
  "SORTIE_BOSS_TYL": { name: "Tyl Regor", faction: "Grineer" },
  "SORTIE_BOSS_JACKAL": { name: "Jackal", faction: "Corpus" },
  "SORTIE_BOSS_ALAD": { name: "Alad V", faction: "Corpus" },
  "SORTIE_BOSS_AMBULAS": { name: "Ambulas", faction: "Corpus" },
  "SORTIE_BOSS_HYENA": { name: "Hyena Pack", faction: "Corpus" },
  "SORTIE_BOSS_NEF": { name: "Nef Anyo", faction: "Corpus" },
  "SORTIE_BOSS_RAPTOR": { name: "Raptor", faction: "Corpus" },
  "SORTIE_BOSS_LEPHANTIS": { name: "Lephantis", faction: "Infested" },
  "SORTIE_BOSS_PHORID": { name: "Phorid", faction: "Infested" },
  "SORTIE_BOSS_MUTALIST_ALAD": { name: "Mutalist Alad V", faction: "Infested" },
  "SORTIE_BOSS_CORRUPTED_VOR": { name: "Corrupted Vor", faction: "Corrupted" },
  "SORTIE_BOSS_INFALAD": { name: "Infested Alad V", faction: "Infested" },
  "SORTIE_BOSS_ROPALOLYST": { name: "Ropalolyst", faction: "Sentient" }
};

// ============================================================
// SORTIE MODIFIER MAPPINGS
// ============================================================

const SORTIE_MODIFIERS = {
  "SORTIE_MODIFIER_IMPACT": "Physical Enhancement: Impact",
  "SORTIE_MODIFIER_PUNCTURE": "Physical Enhancement: Puncture",
  "SORTIE_MODIFIER_SLASH": "Physical Enhancement: Slash",
  "SORTIE_MODIFIER_FIRE": "Elemental Enhancement: Heat",
  "SORTIE_MODIFIER_FREEZE": "Elemental Enhancement: Cold",
  "SORTIE_MODIFIER_ELECTRICITY": "Elemental Enhancement: Electricity",
  "SORTIE_MODIFIER_TOXIN": "Elemental Enhancement: Toxin",
  "SORTIE_MODIFIER_RADIATION": "Elemental Enhancement: Radiation",
  "SORTIE_MODIFIER_MAGNETIC": "Elemental Enhancement: Magnetic",
  "SORTIE_MODIFIER_GAS": "Elemental Enhancement: Gas",
  "SORTIE_MODIFIER_VIRAL": "Elemental Enhancement: Viral",
  "SORTIE_MODIFIER_CORROSIVE": "Elemental Enhancement: Corrosive",
  "SORTIE_MODIFIER_BLAST": "Elemental Enhancement: Blast",
  "SORTIE_MODIFIER_ARMOR": "Augmented Enemy Armor",
  "SORTIE_MODIFIER_SHIELDS": "Augmented Enemy Shields",
  "SORTIE_MODIFIER_LOW_ENERGY": "Energy Reduction",
  "SORTIE_MODIFIER_EXIMUS": "Eximus Stronghold",
  "SORTIE_MODIFIER_SECONDARY_ONLY": "Secondary Only",
  "SORTIE_MODIFIER_SHOTGUN_ONLY": "Shotgun Only",
  "SORTIE_MODIFIER_SNIPER_ONLY": "Sniper Only",
  "SORTIE_MODIFIER_MELEE_ONLY": "Melee Only",
  "SORTIE_MODIFIER_BOW_ONLY": "Bow Only",
  "SORTIE_MODIFIER_RIFLE_ONLY": "Assault Rifle Only",
  "SORTIE_MODIFIER_HAZARD_RADIATION": "Environmental Hazard: Radiation",
  "SORTIE_MODIFIER_HAZARD_MAGNETIC": "Environmental Hazard: Magnetic",
  "SORTIE_MODIFIER_HAZARD_FOG": "Environmental Hazard: Dense Fog",
  "SORTIE_MODIFIER_HAZARD_FIRE": "Environmental Hazard: Fire",
  "SORTIE_MODIFIER_HAZARD_ICE": "Environmental Hazard: Cryogenic",
  "SORTIE_MODIFIER_HAZARD_COLD": "Environmental Hazard: Cryogenic"
};

// ============================================================
// VOID STORM / RAILJACK ERA MAPPINGS
// ============================================================

const VOID_STORM_TIERS = {
  "VoidT1": "Lith",
  "VoidT2": "Meso",
  "VoidT3": "Neo",
  "VoidT4": "Axi"
};

// ============================================================
// NODE LOOKUP TABLE
// Format: [name, system, factionIndex, missionIndex, minLevel, maxLevel]
// All data from DE's ExportRegions (content.warframe.com/PublicExport/)
// ============================================================

const NODE_DATA = {"SolNode94":["Apollodorus","Mercury",2,2,6,11],"SolNode130":["Lares","Mercury",2,8,6,11],"SolNode119":["Caloris","Mercury",0,3,6,8],"SolNode12":["Elion","Mercury",0,5,7,9],"SolNode103":["M Prime","Mercury",0,1,7,9],"SolNode28":["Terminus","Mercury",2,4,8,10],"SolNode108":["Tolstoj","Mercury",0,0,8,10],"SolNode223":["Boethius","Mercury",2,9,8,10],"SolNode224":["Odin","Mercury",0,13,6,11],"SolNode225":["Suisei","Mercury",0,7,8,10],"SolNode226":["Pantheon","Mercury",0,1,6,8],"SolNode129":["Orb Vallis","Venus",1,28,10,30],"SolNode123":["V Prime","Venus",1,2,6,8],"SolNode61":["Ishtar","Venus",1,4,6,8],"SolNode2":["Aphrodite","Venus",1,9,5,8],"SolNode23":["Cytherean","Venus",1,13,6,8],"SolNode128":["E Gate","Venus",1,1,3,5],"SolNode109":["Linea","Venus",1,3,5,7],"SolNode104":["Fossa","Venus",1,0,6,8],"SolNode66":["Unda","Venus",1,7,6,8],"ClanNode1":["Malva","Venus",2,2,8,18],"SolNode107":["Venera","Venus",1,5,5,7],"SolNode22":["Tessera","Venus",1,8,3,7],"SolNode101":["Kiliken","Venus",1,17,3,7],"SolNode145":["Romula","Venus",1,8,4,7],"SolNode146":["Montes","Venus",1,1,6,8],"SolNode149":["Plains of Eidolon","Earth",0,28,1,60],"SolNode7":["Cervantes","Earth",0,4,1,6],"SolNode56":["Mantle","Earth",0,5,2,4],"SolNode63":["Cambria","Earth",0,7,2,4],"SolNode100":["Oro","Earth",0,0,4,6],"SolNode106":["Pacific","Earth",0,3,2,4],"SolNode96":["Eurasia","Earth",0,9,1,5],"SolNode87":["Everest","Earth",0,17,1,6],"SolNode57":["Sao","Neptune",1,4,30,32],"SolNode62":["Neso","Neptune",1,1,29,31],"SolNode908":["Salacia","Neptune",1,9,27,32],"SolNode127":["Psamathe","Neptune",1,0,30,32],"SolNode118":["Laomedeia","Neptune",1,33,25,30],"SolNode84":["Nereid","Neptune",1,7,30,32],"ClanNode20":["Yursa","Neptune",2,27,30,40],"ClanNode21":["Kelashin","Neptune",2,2,30,40],"SolNode89":["Mariana","Earth",0,1,1,3],"SolNode131":["Cetus","Earth",0,28,10,30],"SolNode76":["Lith","Earth",0,8,1,6],"SolNode132":["Stöfler","Lua",3,8,25,30],"SolNode133":["Tycho","Lua",3,2,25,30],"SolNode134":["Plato","Lua",3,1,25,30],"SolNode135":["Zeipel","Lua",3,9,25,30],"SolNode136":["Pavlov","Lua",3,3,25,30],"SolNode137":["Copernicus","Lua",3,5,25,30],"SolNode138":["Grimaldi","Lua",3,7,25,30],"SolNode139":["Apollo","Lua",3,33,25,30],"SolNode802":["Circulus","Lua",3,45,50,70],"SolNode38":["War","Mars",0,0,11,13],"SolNode64":["Alator","Mars",0,13,11,13],"SolNode85":["Kadesh","Mars",0,8,10,15],"SolNode11":["Gradivus","Mars",0,7,10,12],"SolNode67":["Olympus","Mars",0,33,10,12],"SolNode86":["Ara","Mars",0,5,10,12],"SolNode16":["Augustus","Mars",0,1,11,13],"SolNode50":["Arval","Mars",0,9,11,13],"SolNode15":["Spear","Mars",0,8,11,13],"SolNode216":["Hellas Basin","Mars",0,28,10,30],"SolNode82":["Martialis","Mars",0,4,11,13],"SolNode170":["Wahiba","Mars",0,2,10,15],"SolNode117":["Valle","Mars",0,3,12,14],"SolNode44":["Ultor","Mars",0,1,10,12],"SolNode79":["Ares","Mars",0,0,11,14],"SolNode157":["Draco","Ceres",0,2,15,20],"SolNode158":["Gabii","Ceres",2,2,15,25],"SolNode148":["Cinxia","Ceres",0,13,17,19],"SolNode147":["Seimeni","Ceres",2,8,15,25],"SolNode169":["Casta","Ceres",8,15,17],"SolNode140":["Nuovo","Ceres",0,3,16,18],"SolNode141":["Kiste","Ceres",0,7,16,18],"SolNode142":["Bode","Ceres",0,4,16,18],"SolNode144":["Lex","Ceres",0,5,17,19],"SolNode75":["Ludi","Ceres",0,14,16,18],"SolNode143":["Exta","Ceres",0,0,14,16],"SolNode29":["Paimon","Ceres",0,8,15,20],"SolNode39":["Olla","Ceres",0,9,15,17],"SolNode19":["Egeria","Ceres",0,1,15,17],"SolNode150":["Ker","Ceres",0,4,16,18],"SolNode151":["Thon","Ceres",0,7,16,18],"SolNode152":["Hapke","Ceres",0,1,15,17],"SolNode55":["Themisto","Jupiter",1,0,18,20],"SolNode65":["Adrastea","Jupiter",0,14,18,20],"SolNode46":["Amalthea","Jupiter",1,4,17,19],"SolNode164":["Elara","Jupiter",2,2,15,25],"SolNode167":["Io","Jupiter",2,8,15,25],"SolNode163":["Carpo","Jupiter",1,1,17,19],"SolNode177":["Metis","Jupiter",1,5,16,18],"SolNode183":["Callisto","Jupiter",1,13,18,20],"SolNode187":["Sinai","Jupiter",1,8,16,21],"SolNode188":["Ananke","Jupiter",1,5,16,18],"SolNode196":["Ganymede","Jupiter",1,33,15,20],"SolNode805":["The Ropalolyst","Jupiter",5,0,40,40],"SolNode173":["Europa","Jupiter",1,3,17,19],"SolNode31":["Carme","Jupiter",1,7,17,19],"SolNode195":["Io","Jupiter",1,8,15,20],"SolNode47":["Pandora","Saturn",0,24,21,23],"SolNode90":["Anthe","Saturn",0,9,21,23],"SolNode20":["Tethys","Saturn",0,0,24,26],"SolNode14":["Cassini","Saturn",0,5,21,23],"SolNode24":["Titan","Saturn",2,2,21,36],"SolNode91":["Telesto","Saturn",1,1,21,23],"SolNode92":["Calypso","Saturn",0,4,21,23],"SolNode93":["Dione","Saturn",1,4,21,23],"SolNode41":["Rhea","Saturn",0,13,21,26],"SolNode52":["Helene","Saturn",0,8,21,26],"SolNode53":["Caracol","Saturn",0,27,24,34],"SolNode54":["Pallene","Saturn",1,3,22,24],"SolNode110":["Mimas","Saturn",2,2,21,36],"SolNode111":["Enceladus","Saturn",1,8,21,26],"SolNode7":["Epimetheus","Saturn",0,1,22,24],"SolNode25":["Phoebe","Saturn",1,8,21,26],"SolNode49":["Larissa","Neptune",1,9,29,31],"SolNode1":["Galatea","Neptune",1,5,27,29],"SolNode17":["Proteus","Neptune",1,8,27,32],"SolNode78":["Triton","Neptune",1,3,28,30],"SolNode6":["Despina","Neptune",1,17,27,32],"SolNode120":["Ophelia","Uranus",0,2,24,29],"SolNode83":["Cressida","Uranus",0,9,27,29],"SolNode98":["Desdemona","Uranus",0,4,26,28],"SolNode9":["Rosalind","Uranus",0,7,27,29],"SolNode60":["Caliban","Uranus",0,3,25,27],"SolNode114":["Puck","Uranus",0,1,27,29],"ClanNode16":["Ur","Uranus",2,33,30,35],"SolNode34":["Sycorax","Uranus",0,1,24,26],"SolNode122":["Stephano","Uranus",0,8,24,29],"SolNode907":["Caelus","Uranus",0,13,24,29],"ClanNode17":["Assur","Uranus",2,2,25,35],"SolNode42":["Acheron","Pluto",1,1,34,38],"SolNode43":["Outer Terminus","Pluto",8,34,38],"SolNode102":["Hydra","Pluto",1,5,30,34],"SolNode37":["Oceanum","Pluto",1,3,32,36],"SolNode4":["Narcissus","Pluto",1,1,30,34],"SolNode35":["Regna","Pluto",2,2,30,44],"SolNode36":["Sechura","Pluto",2,8,30,40],"SolNode80":["Cypress","Pluto",1,4,32,36],"SolNode81":["Palus","Pluto",2,2,30,44],"SolNode112":["Minthe","Pluto",7,30,34],"SolNode113":["Hieracon","Pluto",2,17,35,45],"SolNode48":["Hades","Pluto",1,0,32,36],"SolNode73":["Cerberus","Pluto",13,30,34],"SolNode115":["Hydron","Sedna",0,8,30,40],"SolNode116":["Rusalka","Sedna",0,5,30,32],"SolNode40":["Tikoloshe","Sedna",0,5,30,32],"SolNode8":["Merrow","Sedna",0,0,32,34],"SolNode51":["Kelpie","Sedna",0,3,30,32],"SolNode77":["Charybdis","Sedna",0,7,32,34],"SolNode70":["Berehynia","Sedna",0,13,30,40],"SolNode69":["Selkie","Sedna",2,2,30,40],"SolNode71":["Vodyanoi","Sedna",0,22,30,40],"SolNode72":["Nakki","Sedna",0,22,30,40],"SolNode68":["Marid","Sedna",0,14,30,40],"SolNode74":["Adaro","Sedna",0,1,32,36],"SolNode88":["Yam","Sedna",0,1,30,32],"SolNode500":["Koro","Kuva Fortress",0,26,28,30],"SolNode501":["Nabuk","Kuva Fortress",0,5,28,30],"SolNode502":["Taveuni","Kuva Fortress",2,2,25,35],"SolNode503":["Pago","Kuva Fortress",0,3,28,30],"SolNode504":["Dakata","Kuva Fortress",0,1,28,30],"SolNode505":["Rotuma","Kuva Fortress",0,7,28,30],"SolNode506":["Tamu","Kuva Fortress",0,8,28,32],"SolNode507":["Kuva Survival","Kuva Fortress",0,2,80,100],"SolNode300":["Cervantes","Europa",1,4,18,20],"SolNode301":["Morax","Europa",1,7,19,21],"SolNode302":["Armaros","Europa",1,1,19,21],"SolNode303":["Abaddon","Europa",1,5,18,20],"SolNode304":["Valac","Europa",1,3,19,21],"SolNode305":["Baal","Europa",1,1,20,22],"SolNode306":["Paimon","Europa",1,0,21,23],"SolNode307":["Valefor","Europa",1,1,18,20],"SolNode308":["Ose","Europa",13,18,22],"SolNode309":["Naamah","Europa",1,9,18,20],"SolNode310":["Kokabiel","Europa",1,4,20,22],"SolNode311":["Sorath","Europa",1,14,20,22],"SolNode312":["Orias","Europa",1,8,20,25],"SolNode313":["Lillith","Europa",1,1,18,20],"SolNode314":["Larzac","Europa",1,3,19,21],"ClanNode14":["Cholistan","Europa",2,2,20,30],"ClanNode15":["Viver","Europa",2,13,25,30],"SolNode99":["Manics","Mars",0,2,11,14],"SolNode125":["Zabala","Eris",2,2,30,40],"SolNode126":["Akkad","Eris",2,8,35,45],"SolNode121":["Xini","Eris",2,13,30,40],"SolNode105":["Naeglar","Eris",2,15,30,40],"SolNode97":["Brugia","Eris",9,30,34],"SolNode95":["Kala-azar","Eris",2,8,30,40],"SolNode27":["Histo","Eris",2,1,30,34],"SolNode26":["Isos","Eris",2,5,30,34],"SolNode33":["Nimus","Eris",2,7,32,36],"SolNode32":["Saxis","Eris",2,1,30,34],"SolNode30":["Oestrus","Eris",2,21,34,38],"SolNode400":["Teshub","Void",3,1,10,15],"SolNode401":["Hepit","Void",3,5,10,15],"SolNode402":["Taranis","Void",3,8,10,15],"SolNode403":["Tiwaz","Void",3,9,20,25],"SolNode404":["Stribog","Void",3,4,20,25],"SolNode405":["Ani","Void",3,2,20,25],"SolNode406":["Ukko","Void",3,5,30,35],"SolNode407":["Oxomoco","Void",3,1,30,35],"SolNode408":["Belenus","Void",3,8,30,35],"SolNode409":["Mot","Void",3,2,40,45],"SolNode410":["Aten","Void",3,9,40,45],"SolNode411":["Marduk","Void",3,4,40,45],"SolNode412":["Mithra","Void",3,13,40,45],"SettlementNode1":["Roche","Phobos",1,1,10,12],"SettlementNode3":["Stickney","Phobos",1,2,10,15],"SettlementNode2":["Skyresh","Phobos",1,5,12,14],"SettlementNode12":["Monolith","Phobos",1,3,13,15],"SettlementNode10":["Kepler","Phobos",1,25,12,14],"SettlementNode15":["Sharpless","Phobos",1,9,11,13],"SettlementNode11":["Gulliver","Phobos",1,8,10,15],"SettlementNode14":["Shklovsky","Phobos",1,7,11,13],"ClanNode10":["Memphis","Phobos",2,27,15,25],"SettlementNode20":["Iliad","Phobos",1,0,13,15],"ClanNode11":["Zeugma","Phobos",2,2,15,25],"SolNode706":["Horend","Deimos",2,5,12,14],"SolNode707":["Hyf","Deimos",2,8,12,14],"SolNode708":["Phlegyas","Deimos",2,2,12,14],"SolNode709":["Magnacidium","Deimos",2,0,12,14],"SolNode710":["Terrorem","Deimos",2,2,12,14],"SolNode711":["Formido","Deimos",2,1,12,14],"SolNode712":["Persto","Deimos",2,4,12,14],"SolNode713":["Effervo","Deimos",7,38,35,45],"SolNode714":["Nex","Deimos",7,8,35,45],"SolNode715":["Munio","Deimos",7,2,30,40],"SolNode716":["Cambire","Deimos",7,38,35,45],"SolNode717":["Sanctum Anatomica","Deimos",7,28,35,60],"SolNode751":["Duviri","Duviri",10,28,1,999],"SolNode752":["The Duviri Experience","Duviri",10,28,1,999],"SolNode753":["The Lone Story","Duviri",10,28,1,999],"SolNode754":["The Circuit","Duviri",10,31,1,100],"SolNode755":["The Steel Path Circuit","Duviri",10,31,1,100],"SolNode780":["Everview Arc","Zariman",1,34,50,55],"SolNode781":["Tuvul Commons","Zariman",1,35,50,55],"SolNode782":["Oro Works","Zariman",1,36,50,55],"SolNode783":["Halako Perimeter","Zariman",1,1,50,55]};

// ============================================================
// EXTRA NODES (Relays, Railjack Proxima, special nodes not in ExportRegions)
// ============================================================

const EXTRA_NODES = {
  // Relays
  "EarthHUB": ["Strata Relay", "Earth", 11, -1, 0, 0],
  "VenusHUB": ["Vesper Relay", "Venus", 11, -1, 0, 0],
  "MercuryHUB": ["Larunda Relay", "Mercury", 11, -1, 0, 0],
  "EuropaHUB": ["Leonov Relay", "Europa", 11, -1, 0, 0],
  "SaturnHUB": ["Kronia Relay", "Saturn", 11, -1, 0, 0],
  "ErisHUB": ["Kuiper Relay", "Eris", 11, -1, 0, 0],
  "PlutoHUB": ["Orcus Relay", "Pluto", 11, -1, 0, 0],
  // Railjack Proxima nodes (CrewBattleNode)
  "CrewBattleNode500": ["Sover Strait", "Earth Proxima", 0, 1, 20, 30],
  "CrewBattleNode501": ["Ogal Cluster", "Earth Proxima", 0, 1, 20, 30],
  "CrewBattleNode502": ["Ganalen's Grave", "Earth Proxima", 0, 8, 20, 30],
  "CrewBattleNode503": ["Rempei Cluster", "Earth Proxima", 0, 1, 20, 30],
  "CrewBattleNode504": ["Iota Temple", "Earth Proxima", 0, 4, 20, 30],
  "CrewBattleNode505": ["Korms Belt", "Earth Proxima", 0, 2, 20, 30],
  "CrewBattleNode510": ["Kasio's Rest", "Venus Proxima", 1, 1, 25, 35],
  "CrewBattleNode511": ["Falling Glory", "Venus Proxima", 1, 1, 25, 35],
  "CrewBattleNode512": ["Luckless Expanse", "Venus Proxima", 1, 8, 25, 35],
  "CrewBattleNode513": ["Beacon of Affliction", "Venus Proxima", 1, 4, 25, 35],
  "CrewBattleNode514": ["Vesper Strait", "Venus Proxima", 1, 2, 25, 35],
  "CrewBattleNode515": ["Calabash Depot", "Venus Proxima", 1, 1, 25, 35],
  "CrewBattleNode516": ["Enkidu Ice Drifts", "Venus Proxima", 1, 1, 25, 35],
  "CrewBattleNode520": ["Lu-Yan Station", "Neptune Proxima", 1, 1, 30, 40],
  "CrewBattleNode521": ["Nu-Gua Mines", "Neptune Proxima", 1, 8, 30, 40],
  "CrewBattleNode522": ["Mammon's Prospect", "Neptune Proxima", 1, 4, 30, 40],
  "CrewBattleNode523": ["Sovereign Grasp", "Neptune Proxima", 1, 1, 30, 40],
  "CrewBattleNode524": ["Arva Vector", "Neptune Proxima", 1, 2, 30, 40],
  "CrewBattleNode525": ["Brom Cluster", "Pluto Proxima", 1, 1, 35, 45],
  "CrewBattleNode526": ["Peregrine Axis", "Pluto Proxima", 1, 4, 35, 45],
  "CrewBattleNode527": ["Obol Crossing", "Pluto Proxima", 1, 8, 35, 45],
  "CrewBattleNode528": ["Fenton's Field", "Pluto Proxima", 1, 1, 35, 45],
  "CrewBattleNode529": ["Flexa", "Veil Proxima", 0, 1, 40, 50],
  "CrewBattleNode530": ["H-2 Cloud", "Veil Proxima", 0, 8, 40, 50],
  "CrewBattleNode531": ["R-9 Cloud", "Veil Proxima", 0, 4, 40, 50],
  "CrewBattleNode532": ["Nsu Grid", "Veil Proxima", 0, 1, 40, 50],
  "CrewBattleNode533": ["Gian Point", "Veil Proxima", 0, 1, 40, 50],
  "CrewBattleNode534": ["Arc Silver", "Veil Proxima", 0, 2, 40, 50]
};

// Merge extra nodes into main lookup
const ALL_NODES = { ...NODE_DATA, ...EXTRA_NODES };

// ============================================================
// ITEM NAME LOOKUP
// All data from DE's PublicExport (ExportWeapons, ExportResources,
// ExportRecipes, ExportWarframes, ExportSentinels, ExportGear, etc.)
// Only items that appear in world state rewards/sales are included.
// ============================================================

const ITEM_NAMES = {"/Lotus/StoreItems/Characters/Tenno/Accessory/Scarves/U17IntermScarf/IridosUdyatSkin/UdyatPrimeGamingSyandana":"Udyat Iridos Syandana","/Lotus/StoreItems/Powersuits/AntiMatter/NovaPrime":"Nova Prime","/Lotus/StoreItems/Powersuits/DemonFrame/DemonFrame":"Uriel","/Lotus/StoreItems/Powersuits/Inkblot/Inkblot":"Follie","/Lotus/StoreItems/Powersuits/MonkeyKing/MonkeyKing":"Wukong","/Lotus/StoreItems/Powersuits/Rhino/Rhino":"Rhino","/Lotus/StoreItems/Powersuits/Trinity/TrinityPrime":"Trinity Prime","/Lotus/StoreItems/Powersuits/Wisp/Wisp":"Wisp","/Lotus/StoreItems/Types/Game/Projections/T1VoidProjectionNovaTrinityVaultABronze":"Lith K4 Relic","/Lotus/StoreItems/Types/Game/Projections/T2VoidProjectionNovaTrinityVaultABronze":"Meso D5 Relic","/Lotus/StoreItems/Types/Game/Projections/T3VoidProjectionNovaTrinityVaultABronze":"Neo N12 Relic","/Lotus/StoreItems/Types/Game/Projections/T4VoidProjectionNovaTrinityVaultABronze":"Axi S7 Relic","/Lotus/StoreItems/Types/Game/QuartersWallpapers/TwitchPrimeNovemberWallpaper":"Iridos Quarters Wallpaper","/Lotus/StoreItems/Types/Items/ShipDecos/TwitchPrimeOctoberDisplay":"Voidshell Decoration","/Lotus/StoreItems/Types/Items/ShipDecos/TwitchPrimeOctoberNoggles/NogglesDisplayTwitchPrime":"Noggle Statue - Grendel Iridos","/Lotus/StoreItems/Types/Recipes/Helmets/NyxPrimeHelmetBlueprint":"Nyx Prime Neuroptics Blueprint","/Lotus/StoreItems/Types/Recipes/Helmets/WukongPrimeHelmetBlueprint":"Wukong Prime Neuroptics Blueprint","/Lotus/StoreItems/Types/Recipes/WarframeRecipes/NovaPrimeBlueprintRecipe":"Nova Prime Blueprint","/Lotus/StoreItems/Types/Recipes/WarframeRecipes/NyxPrimeBlueprintRecipe":"Nyx Prime Blueprint","/Lotus/StoreItems/Types/Recipes/WarframeRecipes/TrinityPrimeBlueprintRecipe":"Trinity Prime Blueprint","/Lotus/StoreItems/Types/Recipes/WarframeRecipes/WukongPrimeBlueprintRecipe":"Wukong Prime Blueprint","/Lotus/StoreItems/Types/Recipes/Weapons/CrpScopePistolBlueprint":"Arca Scisco Blueprint","/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomEmberGlyph":"Ember Heirloom Glyph","/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomRhinoGlyph":"Rhino Heirloom Glyph","/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomValkyrGlyph":"Valkyr Heirloom Glyph","/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomVaubanGlyph":"Vauban Heirloom Glyph","/Lotus/StoreItems/Types/StoreItems/AvatarImages/HeirloomVaubanGlyphSumo":"Vauban Heirloom Tondo Glyph","/Lotus/StoreItems/Types/StoreItems/Packages/MegaPrimeVault/LastChanceItemA":"Last Chance Offerings","/Lotus/StoreItems/Types/StoreItems/Packages/MegaPrimeVault/LastChanceItemB":"Varzia's Offerings - Part 2","/Lotus/StoreItems/Types/StoreItems/Packages/MegaPrimeVault/LastChanceItemC":"Varzia's Offerings","/Lotus/StoreItems/Types/StoreItems/SuitCustomizations/ColourPickerEmberHeirloom":"Ember Heirloom","/Lotus/StoreItems/Types/StoreItems/SuitCustomizations/ColourPickerPrimeDayItemA":"Spektaka","/Lotus/StoreItems/Types/StoreItems/SuitCustomizations/ColourPickerPrimeDayItemB":"Spektaka Prime","/Lotus/StoreItems/Upgrades/Mods/FusionBundles/CircuitSilverSteelPathFusionBundle":"Silver Archon Shard","/Lotus/StoreItems/Upgrades/Skins/Bows/BowPrime2TwitchSkin":"Paris Prime Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Dagger/FangPrimeTwitchSkin":"Fang Prime Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/DualKamas/DualKamasPrimeTwitchSkin":"Dual Kamas Prime Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Glaives/GlaivePrimeTwitchSkin":"Glaive Prime Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/LexPrime/LexPrimeTwitchSkin":"Lex Prime Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/MeleeDangles/ScrollingPrimeMeleeDangle":"Naviga Prime Sugatra","/Lotus/StoreItems/Upgrades/Skins/MeleeDangles/TwitchPrimeMeleeDangle":"Spektaka Prime Sugatra","/Lotus/StoreItems/Upgrades/Skins/MonkeyKing/WukongDeluxeBSkin":"Wukong Qitian Skin","/Lotus/StoreItems/Upgrades/Skins/Necramech/TefilahIridosSkin":"Iridos Voidrig Necramech Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/AkjagaraIridosSkin":"Akjagara Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/ExcaliburTwitchSkin":"Excalibur Prominence Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/LisetSkinTwitch":"Liset Verv Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/OgrisTwitchSkin":"Ogris Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/PyranaTwitchSkin":"Pyrana Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/TigrisTwitchSkin":"Tigris Prominence Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021AfurisSkin":"Afuris Verv Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021LandinCraftSkin":"Landing Craft Verv Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021LatronSkin":"Latron Verv Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2021NikanasSkin":"Nikana Verv Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2023BoltoSkin":"Bolto Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2023OdonataWingSkin":"Odonata Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2023TrinityIridosSkin":"Trinity Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2024DethcubeIridosSkin":"Dethcube Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2024SomaTwitchSkin":"Soma Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Promo/Twitch/Twitch2024ValkyrIridosSkin":"Valkyr Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Rifles/BratonPrimeTwitchSkin":"Braton Prime Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Shotguns/StrunTwitchSkin":"Strun Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/Sigils/PromoTwitchEmblemB":"Iridos Emblem","/Lotus/StoreItems/Upgrades/Skins/Sigils/PromoTwitchEmblemC":"Verv Emblem","/Lotus/StoreItems/Upgrades/Skins/Sigils/PromoTwitchEmblemD":"Prominence Emblem","/Lotus/StoreItems/Upgrades/Skins/Swords/SilvaAegisTwitchSkin":"Silva & Aegis Iridos Skin","/Lotus/StoreItems/Upgrades/Skins/VastoPrime/VastoPrimeTwitchSkin":"Vasto Prime Iridos Skin","/Lotus/StoreItems/Weapons/Tenno/Bows/PrimeBow2/PrimeBow2":"Paris Prime","/Lotus/StoreItems/Weapons/Tenno/Melee/Dagger/FangPrimeDagger":"Fang Prime","/Lotus/StoreItems/Weapons/Tenno/Melee/PrimeDualKamas/PrimeDualKamas":"Dual Kamas Prime","/Lotus/StoreItems/Weapons/Tenno/Melee/SwordsAndBoards/MeleeContestWinnerOne/TennoSwordShield":"Silva & Aegis","/Lotus/StoreItems/Weapons/Tenno/Pistol/HandShotGun":"Bronco","/Lotus/StoreItems/Weapons/Tenno/Pistols/PrimeLex/PrimeLex":"Lex Prime","/Lotus/StoreItems/Weapons/Tenno/Pistols/PrimeVasto/PrimeVastoPistol":"Vasto Prime","/Lotus/StoreItems/Weapons/Tenno/Rifle/BratonPrime":"Braton Prime","/Lotus/StoreItems/Weapons/Tenno/Shotgun/Shotgun":"Strun","/Lotus/Types/Items/MiscItems/InfestedAladCoordinate":"Mutalist Alad V Nav Coordinate","/Lotus/Types/Items/Research/BioComponent":"Mutagen Mass","/Lotus/Types/Items/Research/ChemComponent":"Detonite Injector","/Lotus/Types/Items/Research/EnergyComponent":"Fieldron","/Lotus/Types/Recipes/Weapons/WeaponParts/DeraVandalReceiver":"Dera Vandal Receiver","/Lotus/Types/Recipes/Weapons/WeaponParts/GrineerCombatKnifeHilt":"Sheev Hilt","/Lotus/Types/Recipes/Weapons/WeaponParts/GrineerCombatKnifeBlade":"Sheev Blade"};

// ============================================================
// RESOLVER FUNCTIONS
// ============================================================

/**
 * Resolve a node ID to human-readable info
 * @param {string} nodeId - e.g. "SolNode216"
 * @returns {{ name: string, system: string, faction: string, missionType: string, minLevel: number, maxLevel: number, formatted: string }}
 */
export function resolveNode(nodeId) {
  const data = ALL_NODES[nodeId];
  if (!data) return { name: nodeId, system: "Unknown", faction: "Unknown", missionType: "Unknown", minLevel: 0, maxLevel: 0, formatted: nodeId };
  const [name, system, factionIdx, missionIdx, minLevel, maxLevel] = data;
  return {
    name,
    system,
    faction: FACTION_INDEX[factionIdx] || "Unknown",
    missionType: MISSION_INDEX[missionIdx] || "Unknown",
    minLevel,
    maxLevel,
    formatted: `${name} (${system})`
  };
}

/**
 * Resolve a faction string to human-readable name
 * @param {string} factionStr - e.g. "FC_GRINEER"
 * @returns {string}
 */
export function resolveFaction(factionStr) {
  return FACTION_STRING[factionStr] || factionStr;
}

/**
 * Resolve a mission type string to human-readable name
 * @param {string} missionStr - e.g. "MT_ASSASSINATION"
 * @returns {string}
 */
export function resolveMissionType(missionStr) {
  return MISSION_TYPE_STRING[missionStr] || missionStr;
}

/**
 * Resolve an item path to human-readable name
 * @param {string} itemPath - e.g. "/Lotus/Types/Items/Research/EnergyComponent"
 * @returns {string}
 */
export function resolveItem(itemPath) {
  if (ITEM_NAMES[itemPath]) return ITEM_NAMES[itemPath];
  // Try common path transformations
  const variants = [
    itemPath.replace('/Lotus/StoreItems/', '/Lotus/Types/'),
    itemPath.replace('/Lotus/StoreItems/', '/Lotus/'),
    itemPath.replace('/Lotus/Types/', '/Lotus/StoreItems/'),
    itemPath.replace('/Lotus/StoreItems/Weapons/', '/Lotus/Weapons/'),
  ];
  for (const v of variants) {
    if (ITEM_NAMES[v]) return ITEM_NAMES[v];
  }
  // Fallback: extract a readable name from the path
  const parts = itemPath.split('/');
  return parts[parts.length - 1].replace(/([A-Z])/g, ' $1').trim();
}

/**
 * Resolve a sortie boss string
 * @param {string} bossStr - e.g. "SORTIE_BOSS_JACKAL"
 * @returns {{ name: string, faction: string }}
 */
export function resolveSortieBoss(bossStr) {
  return SORTIE_BOSSES[bossStr] || { name: bossStr, faction: "Unknown" };
}

/**
 * Resolve a sortie modifier string
 * @param {string} modStr - e.g. "SORTIE_MODIFIER_LOW_ENERGY"
 * @returns {string}
 */
export function resolveSortieModifier(modStr) {
  return SORTIE_MODIFIERS[modStr] || modStr;
}

// ============================================================
// CYCLE CALCULATORS (Cetus, Fortuna, Cambion, etc.)
// These are calculated from timestamps, not from the world state
// ============================================================

function getCetusCycle(currentTimeMs) {
  const epoch = 1510444800000; // Known night start
  const cycleLength = 8998000; // ~150 minutes total
  const nightLength = 3000000; // 50 minutes night
  const elapsed = (currentTimeMs - epoch) % cycleLength;
  const isNight = elapsed >= (cycleLength - nightLength);
  const remaining = isNight
    ? cycleLength - elapsed
    : (cycleLength - nightLength) - elapsed;
  return { isNight, remaining, state: isNight ? "Night" : "Day" };
}

function getFortunaThermaCycle(currentTimeMs) {
  const epoch = 1542318000000;
  const cycleLength = 1600000; // ~26.67 minutes
  const warmLength = 400000; // ~6.67 minutes warm
  const elapsed = (currentTimeMs - epoch) % cycleLength;
  const isWarm = elapsed < warmLength;
  const remaining = isWarm ? warmLength - elapsed : cycleLength - elapsed;
  return { isWarm, remaining, state: isWarm ? "Warm" : "Cold" };
}

function getCambionCycle(currentTimeMs) {
  const epoch = 1604085600000;
  const cycleLength = 8998000;
  const elapsed = (currentTimeMs - epoch) % cycleLength;
  const fassLength = cycleLength / 2;
  const isFass = elapsed < fassLength;
  const remaining = isFass ? fassLength - elapsed : cycleLength - elapsed;
  return { isFass, remaining, state: isFass ? "Fass" : "Vome" };
}

function getEarthCycle(currentTimeMs) {
  const cycleLength = 14400000; // 4 hours
  const dayLength = 10800000; // 3 hours day
  const elapsed = currentTimeMs % cycleLength;
  const isDay = elapsed < dayLength;
  const remaining = isDay ? dayLength - elapsed : cycleLength - elapsed;
  return { isDay, remaining, state: isDay ? "Day" : "Night" };
}

function formatTimeRemaining(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

// ============================================================
// MAIN PARSER
// ============================================================

/**
 * Parse a raw world state JSON object into human-readable data
 * @param {Object} raw - Raw JSON from api.warframe.com/cdn/worldState.php
 * @returns {Object} Parsed world state
 */
export function parseWorldState(raw) {
  const now = Date.now();

  return {
    timestamp: raw.Time ? raw.Time * 1000 : now,
    buildLabel: raw.BuildLabel || "Unknown",

    // World cycles
    cycles: {
      cetus: getCetusCycle(now),
      fortuna: getFortunaThermaCycle(now),
      cambion: getCambionCycle(now),
      earth: getEarthCycle(now)
    },

    // Sorties
    sorties: (raw.Sorties || []).map(sortie => {
      const boss = resolveSortieBoss(sortie.Boss);
      return {
        id: sortie._id?.$oid,
        boss: boss.name,
        faction: boss.faction,
        expiry: sortie.Expiry?.$date?.$numberLong ? parseInt(sortie.Expiry.$date.$numberLong) : null,
        variants: (sortie.Variants || []).map(v => {
          const node = resolveNode(v.node);
          return {
            node: node.formatted,
            missionType: resolveMissionType(v.missionType),
            modifier: resolveSortieModifier(v.modifierType),
            level: `${node.minLevel}-${node.maxLevel}`
          };
        })
      };
    }),

    // Invasions
    invasions: (raw.Invasions || []).filter(i => !i.Completed).map(invasion => {
      const node = resolveNode(invasion.Node);
      return {
        id: invasion._id?.$oid,
        node: node.formatted,
        planet: node.system,
        attackerFaction: resolveFaction(invasion.Faction),
        defenderFaction: resolveFaction(invasion.DefenderFaction),
        attackerReward: (invasion.AttackerReward?.countedItems || []).map(r => ({
          item: resolveItem(r.ItemType),
          count: r.ItemCount
        })),
        defenderReward: (invasion.DefenderReward?.countedItems || []).map(r => ({
          item: resolveItem(r.ItemType),
          count: r.ItemCount
        })),
        progress: invasion.Count / invasion.Goal,
        count: invasion.Count,
        goal: invasion.Goal,
        completed: invasion.Completed || false
      };
    }),

    // Void Fissures (Active Missions)
    fissures: (raw.ActiveMissions || []).map(mission => {
      const node = resolveNode(mission.Node);
      return {
        id: mission._id?.$oid,
        node: node.formatted,
        planet: node.system,
        missionType: node.missionType,
        faction: resolveFaction(mission.Faction) || node.faction,
        tier: VOID_STORM_TIERS[mission.Modifier] || mission.Modifier,
        expiry: mission.Expiry?.$date?.$numberLong ? parseInt(mission.Expiry.$date.$numberLong) : null,
        isStorm: false,
        isHard: mission.Hard || false
      };
    }),

    // Void Storms (Railjack fissures)
    voidStorms: (raw.VoidStorms || []).map(storm => {
      const node = resolveNode(storm.Node);
      return {
        id: storm._id?.$oid,
        node: node.formatted,
        planet: node.system,
        missionType: node.missionType,
        tier: VOID_STORM_TIERS[storm.ActiveMissionTier] || storm.ActiveMissionTier,
        expiry: storm.Expiry?.$date?.$numberLong ? parseInt(storm.Expiry.$date.$numberLong) : null,
        isStorm: true
      };
    }),

    // Baro Ki'Teer (Void Traders)
    voidTraders: (raw.VoidTraders || []).map(trader => {
      const node = resolveNode(trader.Node);
      const activation = trader.Activation?.$date?.$numberLong ? parseInt(trader.Activation.$date.$numberLong) : null;
      const expiry = trader.Expiry?.$date?.$numberLong ? parseInt(trader.Expiry.$date.$numberLong) : null;
      const isActive = activation && expiry && now >= activation && now < expiry;
      return {
        character: trader.Character || "Baro Ki'Teer",
        node: node.formatted,
        planet: node.system,
        activation,
        expiry,
        active: isActive,
        inventory: (trader.Manifest || []).map(item => ({
          item: resolveItem(item.ItemType),
          ducats: item.PrimePrice,
          credits: item.RegularPrice
        }))
      };
    }),

    // Alerts
    alerts: (raw.Alerts || []).map(alert => {
      const node = resolveNode(alert.MissionInfo?.location);
      return {
        id: alert._id?.$oid,
        node: node.formatted,
        missionType: MISSION_INDEX[alert.MissionInfo?.missionType] || "Unknown",
        faction: resolveFaction(alert.MissionInfo?.faction),
        minLevel: alert.MissionInfo?.minEnemyLevel,
        maxLevel: alert.MissionInfo?.maxEnemyLevel,
        rewards: (alert.MissionInfo?.missionReward?.countedItems || []).map(r => ({
          item: resolveItem(r.ItemType),
          count: r.ItemCount
        })),
        expiry: alert.Expiry?.$date?.$numberLong ? parseInt(alert.Expiry.$date.$numberLong) : null
      };
    }),

    // Daily Deals (Darvo)
    dailyDeals: (raw.DailyDeals || []).map(deal => ({
      item: resolveItem(deal.StoreItem),
      originalPrice: deal.OriginalPrice,
      salePrice: deal.SalePrice,
      discount: deal.Discount,
      amountTotal: deal.AmountTotal,
      amountSold: deal.AmountSold,
      expiry: deal.Expiry?.$date?.$numberLong ? parseInt(deal.Expiry.$date.$numberLong) : null
    })),

    // Construction Progress (Fomorian/Razorback)
    constructionProgress: {
      fomorian: parseFloat(raw.ProjectPct?.[0]) || 0,
      razorback: parseFloat(raw.ProjectPct?.[1]) || 0
    },

    // Nightwave / Season info
    nightwave: raw.SeasonInfo ? {
      id: raw.SeasonInfo._id?.$oid,
      season: raw.SeasonInfo.Season,
      phase: raw.SeasonInfo.Phase,
      activeChallenges: (raw.SeasonInfo.ActiveChallenges || []).map(c => ({
        id: c._id?.$oid,
        activation: c.Activation?.$date?.$numberLong ? parseInt(c.Activation.$date.$numberLong) : null,
        expiry: c.Expiry?.$date?.$numberLong ? parseInt(c.Expiry.$date.$numberLong) : null,
        challenge: c.Challenge
      }))
    } : null,

    // Syndicate missions
    syndicateMissions: (raw.SyndicateMissions || []).map(sm => ({
      tag: sm.Tag,
      nodes: (sm.Nodes || []).map(n => resolveNode(n).formatted),
      activation: sm.Activation?.$date?.$numberLong ? parseInt(sm.Activation.$date.$numberLong) : null,
      expiry: sm.Expiry?.$date?.$numberLong ? parseInt(sm.Expiry.$date.$numberLong) : null
    }))
  };
}

// ============================================================
// EXPORT DE MANIFEST PATHS (for refreshing lookup data)
// Current as of build 2026.03.26
// ============================================================

export const DE_EXPORT_MANIFEST = {
  baseUrl: "https://content.warframe.com/PublicExport/Manifest/",
  manifestUrl: "https://content.warframe.com/PublicExport/index_en.txt.lzma",
  worldStateUrl: "https://api.warframe.com/cdn/worldState.php",
  files: {
    customs: "ExportCustoms_en.json!00_5v+qNAtp27nU3liImRxgjQ",
    drones: "ExportDrones_en.json!00_-2N+QHfciQUZhljJlrdz-w",
    flavour: "ExportFlavour_en.json!00_aHLPia8i9t1a7vxGXuN-bA",
    fusionBundles: "ExportFusionBundles_en.json!00_hUiYYnklWYlkgXXWeNhmng",
    gear: "ExportGear_en.json!00_0iyrvsyYgdfeHrkLL5-ELw",
    keys: "ExportKeys_en.json!00_62Y3ErKLoGDOaTz5yneZOQ",
    recipes: "ExportRecipes_en.json!00_aqORxN0bLTQuPT65V-CLZw",
    regions: "ExportRegions_en.json!00_457BHCafc9wNaxtGHmvoOw",
    relicArcane: "ExportRelicArcane_en.json!00_Dw+x2njFfDl46UJt0uUAMQ",
    resources: "ExportResources_en.json!00_fN8RlOP7OxnLwcdFvTzO+g",
    sentinels: "ExportSentinels_en.json!00_8iGr2T9MTskXt5zeKEVNmQ",
    sortieRewards: "ExportSortieRewards_en.json!00_EjkJsz44ycXQ2ED1LDnqwA",
    upgrades: "ExportUpgrades_en.json!00_XJsZzeoNvlhroEpKkLVQJA",
    warframes: "ExportWarframes_en.json!00_4z2ijKyWeQitwtrlbz88nA",
    weapons: "ExportWeapons_en.json!00_m4jPUWBwuv+hSYoS5lVOrA",
    manifest: "ExportManifest.json!00_bX3VrfrYU9UIK5FF-bVpbg"
  }
};

// ============================================================
// UTILITY EXPORTS
// ============================================================

export { formatTimeRemaining, FACTION_INDEX, FACTION_STRING, MISSION_INDEX, MISSION_TYPE_STRING, SORTIE_BOSSES, SORTIE_MODIFIERS, VOID_STORM_TIERS, ALL_NODES, ITEM_NAMES };