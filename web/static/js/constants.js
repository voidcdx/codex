// ═══════════════════════════════════════════════════════
// Void Codex — Constants & Global State
// ═══════════════════════════════════════════════════════

// --- Global mutable state ---
let allWeapons = [];
let allMods = [];
let allEnemies = [];
let weaponCombo = null;
let enemyCombo = null;
let selectedAttack = null;
let modSlots = ['','','','','','','',''];
let _pickerSlot = -1;
let _sortableInstance = null;
let stanceSlot = '';
let exilusSlot = '';
let steelPathOn = false;
let eximusOn = false;
let lastScaledEnemy = null;
let rivenApplied = null;
let rivenDraft = [];
let alchSelected = null;
let buffRowId = 0;
let arcaneRowId = 0;
let _currentMultishot = 1.0;
let _modUpdateTimer = null;

// --- Warframe element colours ---
const ELEM_COLORS = {
  impact:      '#9090b0',
  puncture:    '#d0c080',
  slash:       '#e05050',
  heat:        '#ff7a30',
  cold:        '#60b0e0',
  electricity: '#f0e040',
  toxin:       '#60d030',
  blast:       '#ffd040',
  corrosive:   '#a0e040',
  gas:         '#00c8a0',
  magnetic:    '#c060f0',
  radiation:   '#f0a020',
  viral:       '#f060a0',
  true:        '#ffffff',
  void:        '#9060ff',
};

// --- Damage-type SVG icons ---
const DMG_ICONS = {
  impact:      '<path d="M3 8 A5 5 0 0 1 13 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" fill="none"/><path d="M5 8 A3 3 0 0 1 11 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" fill="none"/><path d="M7 8 A1 1 0 0 1 9 8" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" fill="none"/>',
  puncture:    '<polygon points="8,2 13,11 10,11 10,14 6,14 6,11 3,11" fill="currentColor"/>',
  slash:       '<path d="M4 12 L12 4" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/><path d="M6 13 L14 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.5"/>',
  heat:        '<path d="M8 1.5 L6 6 L3.5 9 C3 10 3 11.5 4.5 13 C5.5 14 7 14.5 8 14.5 C9 14.5 10.5 14 11.5 13 C13 11.5 13 10 12.5 9 L10 6 L8 1.5Z M5.5 7 L7 4 L8 6.5 L9.5 3.5 L10.5 7" stroke="currentColor" stroke-width="0.8" fill="currentColor" stroke-linejoin="round"/>',
  cold:        '<line x1="8" y1="2" x2="8" y2="14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><line x1="2.8" y1="5" x2="13.2" y2="11" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><line x1="2.8" y1="11" x2="13.2" y2="5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><line x1="8" y1="2" x2="6" y2="4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><line x1="8" y1="2" x2="10" y2="4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>',
  electricity: '<polygon points="9,1 5,7.5 7.5,7.5 6,15 12,7 9,7" fill="currentColor"/>',
  toxin:       '<path d="M8 2 C8 2 3 8 3 11 C3 13.2 5.2 15 8 15 C10.8 15 13 13.2 13 11 C13 8 8 2 8 2Z" fill="currentColor"/>',
  blast:       '<circle cx="8" cy="8" r="2" fill="currentColor"/><polygon points="8,0.5 9,5.5 14,5 10,7 14.5,8 10,9 14,11 9,10.5 8,15.5 7,10.5 2,11 6,9 1.5,8 6,7 2,5 7,5.5" fill="currentColor" opacity="0.85"/>',
  corrosive:   '<path d="M5.5 2 C5.5 2 2 7 2 9.5 C2 11.5 3.6 13 5.5 13 C7.4 13 9 11.5 9 9.5 C9 7 5.5 2 5.5 2Z" fill="currentColor"/><path d="M11 6 C11 6 8.5 9.5 8.5 11 C8.5 12.4 9.6 13.5 11 13.5 C12.4 13.5 13.5 12.4 13.5 11 C13.5 9.5 11 6 11 6Z" fill="currentColor" opacity="0.7"/>',
  gas:         '<circle cx="6" cy="9" r="3.5" fill="currentColor" opacity="0.7"/><circle cx="10.5" cy="7.5" r="3" fill="currentColor" opacity="0.55"/><circle cx="8.5" cy="11.5" r="2.5" fill="currentColor" opacity="0.45"/>',
  magnetic:    '<rect x="2" y="2" width="4" height="3.5" rx="0.5" fill="currentColor"/><rect x="10" y="2" width="4" height="3.5" rx="0.5" fill="currentColor"/><path d="M4 5.5 L4 7 C4 10.9 5.8 13 8 13 C10.2 13 12 10.9 12 7 L12 5.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>',
  radiation:   '<circle cx="8" cy="8" r="1.6" fill="currentColor"/><path d="M9.04 2.09 A6 6 0 0 1 13.64 10.05 L10.63 8.96 A2.8 2.8 0 0 0 8.49 5.24Z" fill="currentColor"/><path d="M12.6 11.86 A6 6 0 0 1 3.4 11.86 L5.86 9.8 A2.8 2.8 0 0 0 10.14 9.8Z" fill="currentColor"/><path d="M2.36 10.05 A6 6 0 0 1 6.96 2.09 L7.51 5.24 A2.8 2.8 0 0 0 5.37 8.96Z" fill="currentColor"/>',
  viral:       '<path d="M5 2 C5 5 11 6 11 9 C11 12 5 13 5 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/><path d="M11 2 C11 5 5 6 5 9 C5 12 11 13 11 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>',
  true:        '<circle cx="8" cy="8" r="5" stroke="currentColor" stroke-width="1.5" fill="none"/><line x1="8" y1="1" x2="8" y2="15" stroke="currentColor" stroke-width="1.2"/><line x1="1" y1="8" x2="15" y2="8" stroke="currentColor" stroke-width="1.2"/>',
  void:        '<path d="M8 3 C4 3 3 6 5 8 C7 10 5 13 8 13 C11 13 13 10 11 8 C9 6 12 3 8 3Z" stroke="currentColor" stroke-width="1.8" fill="none" stroke-linecap="round"/>',
};

// --- Faction effectiveness (Update 36.0+) ---
const FACTION_EFFECTIVENESS = {
  grineer:         { impact:1.5, corrosive:1.5 },
  kuva_grineer:    { impact:1.5, heat:0.5, corrosive:1.5 },
  corpus:          { puncture:1.5, magnetic:1.5 },
  corpus_amalgam:  { electricity:1.5, blast:0.5, magnetic:1.5 },
  infested:        { slash:1.5, heat:1.5 },
  infestation:     { slash:1.5, heat:1.5 },
  deimos_infested: { blast:1.5, gas:1.5, viral:0.5 },
  corrupted:       { puncture:1.5, radiation:0.5, viral:1.5 },
  orokin:          { puncture:1.5, radiation:0.5, viral:1.5 },
  sentient:        { cold:1.5, corrosive:0.5, radiation:1.5 },
  narmer:          { slash:1.5, toxin:1.5, magnetic:0.5 },
  themurmur:       { electricity:1.5, radiation:1.5, viral:0.5 },
  murmur:          { electricity:1.5, radiation:1.5, viral:0.5 },
  scaldra:         { impact:1.5, corrosive:1.5, gas:0.5 },
  techrot:         { cold:0.5, gas:1.5, magnetic:1.5 },
  anarchs:         { impact:1.5, electricity:1.5, radiation:0.5 },
};

// --- Tooltip text ---
const TOOLTIPS = {
  'crit-chance':  'Chance per hit to deal a critical strike. 100\u2013200% = guaranteed Tier 1 + chance at Tier 2, etc.',
  'crit-mult':    'Damage multiplier on a critical hit.',
  'status':       'Chance per hit to apply a status proc \u2014 Slash bleed, Heat burn, Viral debuff, etc.',
  'fire-rate':    'Shots (or attacks) per second. Affects DPS but not per-hit damage.',
  'magazine':     'Rounds before a reload is required.',
  'max-ammo':     'Maximum ammo reserve (excludes magazine).',
  'reload':       'Time in seconds to reload the weapon.',
  'multishot':    'Projectiles fired per trigger pull. Each projectile deals full damage and independently rolls status/crit. Base is 1.0 for all weapons.',
  'impact':       'Strong vs. Machinery, Robotic. Weak vs. Infested Sinew.',
  'puncture':     'Strong vs. Corpus, Corrupted/Orokin. No DoT.',
  'slash':        'Strong vs. Infested, Narmer. Procs a bleed DoT that bypasses armor.',
  'heat':         'Strong vs. Infested. Resistant: Kuva Grineer. Procs a burn DoT.',
  'cold':         'Strong vs. Sentient. Resistant: Techrot. Procs a slow.',
  'electricity':  'Strong vs. Corpus Amalgam, Murmur, Anarchs. Procs a chain stun.',
  'toxin':        'Strong vs. Narmer. Procs a poison DoT that bypasses shields.',
  'blast':        'Heat + Cold. Strong vs. Deimos Infested. Resistant: Corpus Amalgam. Procs a knockback.',
  'corrosive':    'Electricity + Toxin. Strong vs. Grineer, Scaldra. Resistant: Sentient. Permanently strips armor stacks.',
  'gas':          'Heat + Toxin. Strong vs. Deimos Infested, Techrot. Resistant: Scaldra. Procs a toxic cloud AoE.',
  'magnetic':     'Cold + Electricity. Strong vs. Corpus, Techrot. Resistant: Narmer. Procs a shield drain.',
  'radiation':    'Heat + Electricity. Strong vs. Sentient, Murmur. Resistant: Corrupted, Anarchs. Procs confusion (enemies attack each other).',
  'viral':        'Cold + Toxin. Strong vs. Cloned Flesh, Flesh. Weak vs. Robotic, Machinery. Procs a health debuff (\u00d74.25 damage to health at 10 stacks).',
  'void':         'Dealt by Operator amps and select weapons. No special armor/health interactions.',
};

// --- Element combination ---
const ELEM_COMBOS = {
  'heat+cold': 'Blast', 'cold+heat': 'Blast',
  'electricity+toxin': 'Corrosive', 'toxin+electricity': 'Corrosive',
  'heat+toxin': 'Gas', 'toxin+heat': 'Gas',
  'cold+electricity': 'Magnetic', 'electricity+cold': 'Magnetic',
  'heat+electricity': 'Radiation', 'electricity+heat': 'Radiation',
  'cold+toxin': 'Viral', 'toxin+cold': 'Viral',
};
const PRIMARY_ELEMENTS = new Set(['heat', 'cold', 'electricity', 'toxin']);

// --- Riven stat options ---
const RIVEN_STAT_OPTIONS = [
  {value: '',              label: '\u2014 Select stat \u2014'},
  {value: 'damage',        label: 'Damage'},
  {value: 'multishot',     label: 'Multishot'},
  {value: 'crit_chance',   label: 'Critical Chance'},
  {value: 'crit_damage',   label: 'Critical Multiplier'},
  {value: 'status_chance', label: 'Status Chance'},
  {value: 'fire_rate',     label: 'Fire Rate'},
  {value: 'heat',          label: 'Heat'},
  {value: 'cold',          label: 'Cold'},
  {value: 'electricity',   label: 'Electricity'},
  {value: 'toxin',         label: 'Toxin'},
  {value: 'impact',        label: 'Impact'},
  {value: 'puncture',      label: 'Puncture'},
  {value: 'slash',         label: 'Slash'},
];

// --- Exilus mod sets ---
const EXILUS_PRIMARY = new Set([
  'Ammo Drum','Shell Compression','Rifle Ammo Mutation','Primed Rifle Ammo Mutation',
  'Shotgun Ammo Mutation','Primed Shotgun Ammo Mutation','Arrow Mutation',
  'Sniper Ammo Mutation','Vigilante Supplies','Eagle Eye','Broad Eye','Overview',
  'Aero Periphery','Agile Aim','Snap Shot','Aerial Ace',
  'Gun Glide','Double-Barrel Drift','Stabilizer','Primed Stabilizer','Vile Precision',
  'Guided Ordnance','Narrow Barrel','Hush','Silent Battery','Twitch','Soft Hands',
  'Lock and Load','Tactical Reload','Terminal Velocity','Fatal Acceleration',
  'Galvanized Acceleration','Mending Shot','Sinister Reach',
]);
const EXILUS_SECONDARY = new Set([
  'Trick Mag','Pistol Ammo Mutation','Primed Pistol Ammo Mutation','Air Recon',
  'Hawk Eye','Spry Sights','Strafing Slide','Steady Hands','Primed Steady Hands',
  'Targeting Subsystem','Suppress','Reflex Draw','Eject Magazine','Lethal Momentum',
  'Energizing Shot','Ruinous Extension','Fass Canticle','Jahu Canticle',
  'Khra Canticle','Lohk Canticle',
]);
const EXILUS_MELEE = new Set([
  'Dispatch Overdrive','Electromagnetic Shielding','Focused Defense','Guardian Derision',
  'Parry','Whirlwind',"Condition's Perfection","Discipline's Merit","Dreamer's Wrath",
  "Master's Edge","Mentor's Legacy","Opportunity's Reach",
]);
const WEAPON_SPECIFIC_EXILUS = {
  'Ambush Optics': ['Rubico','Rubico Prime'],
  'Bhisaj-Bal': ['Paris Prime'],
  'Adhesive Blast': [
    'Ogris','Penta','Secura Penta','Carmine Penta','Tenet Ferrox',
    'Tenet Envoy','Tonkor','Torid','Zarr',
  ],
  'Cautious Shot': [
    'Acceltra','Acceltra Prime','Aeolak','Afentis','Alternox','Ambassador',
    'Battacor','Basmu','Evensong','Ferrox','Tenet Ferrox','Javlok','Komorex',
    'Kuva Bramma','Kuva Chakkhurr','Lenz','Mutalist Quanta','Ogris','Kuva Ogris',
    'Opticor','Opticor Vandal','Panthera Prime','Penta','Secura Penta',
    'Proboscis Cernos','Scourge','Scourge Prime','Shedu','Simulor','Synoid Simulor',
    'Sporothrix','Stahlta','Tenet Envoy','Tonkor','Kuva Tonkor',
    'Torid','Trumna','Trumna Prime','Zarr','Kuva Zarr','Zhuge Prime',
  ],
  'Directed Convergence': ['Supra','Supra Vandal'],
  'Fomorian Accelerant': ['Drakgoon'],
  'Kinetic Ricochet': ['Prisma Tetra','Tenet Tetra'],
  'Tether Grenades': ['Secura Penta','Carmine Penta'],
};

// --- Alchemy Guide ---
const ALCH_PRIMARY = ['heat', 'cold', 'electricity', 'toxin'];
const ALCH_COMBINED = ['blast', 'corrosive', 'gas', 'magnetic', 'radiation', 'viral'];
const ALCH_RECIPES = {
  blast: ['heat', 'cold'],       corrosive: ['electricity', 'toxin'],
  gas: ['heat', 'toxin'],        magnetic: ['cold', 'electricity'],
  radiation: ['heat', 'electricity'], viral: ['cold', 'toxin'],
};
const ALCH_ELEM_PCT_FIELD = {
  heat: 'heat_pct', cold: 'cold_pct', electricity: 'electricity_pct', toxin: 'toxin_pct',
  blast: 'blast_pct', corrosive: 'corrosive_pct', gas: 'gas_pct',
  magnetic: 'magnetic_pct', radiation: 'radiation_pct', viral: 'viral_pct',
};

// --- Changelog ---
const CHANGELOG_ENTRIES = [
  {
    version: '0.5.3',
    date: '2026-03-26',
    sections: [
      { heading: 'Added', items: [
        'Armor Strip panel \u2014 models ability strip %, Corrosive Projection aura %, and Shattering Impact flat removal; shows remaining armor and DR% live',
        'Panel help (?) buttons on all panels \u2014 click to expand inline explanation of mechanics for each section',
        'CDM quantization \u2014 critical damage multiplier snapped to game\u2019s internal precision grid',
      ]},
    ],
  },
  {
    version: '0.5.2',
    date: '2026-03-26',
    sections: [
      { heading: 'Fixed', items: [
        'Hit Type / Body Part / Bonus Element dropdowns styled to match the rest of the UI',
        'Stack inputs (Viral, Corrosive, Cold) clamped to 0\u201310',
      ]},
    ],
  },
  {
    version: '0.5.1',
    date: '2026-03-26',
    sections: [
      { heading: 'Fixed', items: [
        'Mod family exclusivity \u2014 Primed/Umbral/Archon variants no longer stack with base version',
        'Crit chance formula corrected to multiplicative (base \u00d7 (1 + mods))',
        'Blood Rush now scales with combo tiers; contributed 0 at \u00d71, not flat +40%',
        'Multishot result floored to integer per in-game behaviour',
        'Torid attack stats corrected; Mutalist Quanta + Synoid Simulor crit multipliers fixed',
      ]},
      { heading: 'Added', items: [
        'Cold proc stacks (+0.1 flat CDM each, max 10) in Hit Options',
        'Weapon data validation script (scripts/validate_weapons.py)',
      ]},
    ],
  },
  {
    version: '0.5.0',
    date: '2026-03-25',
    sections: [
      { heading: 'Changed', items: [
        'Major UI layout overhaul \u2014 Weapon+Enemy merged side-by-side, Arcanes into Mods, Hit Options+Buffs merged',
        'Options panel moved to right column, collapsible; Calculate button repositioned below Options',
        'Sidebar widened, right column expanded, Builds panel hidden, layout centered at 1440px',
        'Removed header Guide/Changelog buttons; sidebar footer now shows copyright + data attribution',
        'All hardcoded inline styles extracted to CSS classes; scan-line overlay removed',
        'Sharp edges (border-radius: 0) and hidden scrollbars throughout',
      ]},
    ],
  },
  {
    version: '0.4.2',
    date: '2026-03-25',
    sections: [
      { heading: 'Changed', items: [
        'Design tweaks \u2014 modal theme consistency, CSS variable cleanup, mobile viewport fix',
      ]},
    ],
  },
  {
    version: '0.4.1',
    date: '2026-03-25',
    sections: [
      { heading: 'Changed', items: [
        'Calculator page redesigned to match Stalker/Shadow Acolyte theme \u2014 dark crimson palette, Orbitron/Rajdhani fonts, glass panels with crimson glow, right sidebar with brand icon and nav',
        'UI optimizations \u2014 layout, panel structure, and stylesheet organization',
      ]},
    ],
  },
  {
    version: '0.4.0',
    date: '2026-03-25',
    sections: [
      { heading: 'Changed', items: [
        'Full graphical redesign of the Web UI',
      ]},
    ],
  },
  {
    version: '0.3.1',
    date: '2026-03-24',
    sections: [
      { heading: 'Added', items: [
        'Condition Overload scaling curve in calculation results \u2014 shows damage at 0\u201310 unique statuses with bar chart and % increase',
      ]},
    ],
  },
  {
    version: '0.3.0',
    date: '2026-03-24',
    sections: [
      { heading: 'Added', items: [
        'Weapon Arcane support — 11 presets (Merciless, Deadhead, Dexterity, Cascadia) with per-arcane stacks and full pipeline integration',
        'Arcane panel in Web UI with weapon-type filtering, stacks input, and max 2 slots',
        '--arcane CLI flag and GET /api/arcanes endpoint',
        'Deadhead headshot multiplier bonus and Cascadia Overcharge flat damage',
      ]},
    ],
  },
  {
    version: '0.2.2',
    date: '2026-03-24',
    sections: [
      { heading: 'Improved', items: [
        'Visual cleanup and mobile fixes',
      ]},
    ],
  },
  {
    version: '0.2.1',
    date: '2026-03-23',
    sections: [
      { heading: 'Improved', items: [
        'Web interface JavaScript reorganised into separate, focused modules for improved maintainability and long-term reliability',
      ]},
    ],
  },
  {
    version: '0.2.0',
    date: '2026-03-23',
    sections: [
      { heading: 'Added', items: [
        'Redesigned Alchemy Guide with a glassmorphism modal, detailed mod rows with stat pills, and an equip/unequip toggle',
        'Element effect data now included in the mods API for richer mod information display',
      ]},
      { heading: 'Improved', items: [
        'Alchemy Guide responsiveness: mobile centering, scroll containment, and a dedicated \u201cClear Mods\u201d action',
        'Gas element colour updated to teal for improved visual clarity',
      ]},
      { heading: 'Fixed', items: [
        'Text overflow in the damage breakdown table on narrow screens',
      ]},
    ],
  },
  {
    version: '0.1.0',
    date: 'Initial Release',
    sections: [
      { heading: 'Added', items: [
        'Full damage calculation pipeline with quantization, critical hits, armor mitigation, faction modifiers, and Viral stack scaling',
        'Elemental combination system respecting mod slot order',
        'Status proc modeling: damage-over-time and crowd-control/debuff effects',
        'Multi-attack weapon support with per-attack stat selection',
        'Galvanized mod stack scaling',
        'Warframe ability buff integration (Roar, Eclipse, Xata\u2019s Whisper, Nourish)',
        'Per-faction enemy level scaling for health, shields, armor, and overguard',
        'Web interface, command-line tool, and API backend',
        'Launch dataset: 588 weapons, 1,405 mods, 983 enemies',
      ]},
    ],
  },
];

// --- Warframe Buffs ---
const BUFF_OPTIONS = [
  {key:'roar',          label:'Roar (Rhino)'},
  {key:'eclipse',       label:'Eclipse (Mirage)'},
  {key:'xatas_whisper', label:"Xata's Whisper (Xaku)"},
  {key:'nourish',       label:'Nourish (Grendel)'},
];

const ARCANE_OPTIONS = [
  {key:'primary_merciless',   label:'Primary Merciless',   maxStacks:12, restriction:'primary'},
  {key:'secondary_merciless', label:'Secondary Merciless', maxStacks:12, restriction:'secondary'},
  {key:'shotgun_merciless',   label:'Shotgun Merciless',   maxStacks:12, restriction:'shotgun'},
  {key:'primary_deadhead',    label:'Primary Deadhead',    maxStacks:6,  restriction:'primary'},
  {key:'secondary_deadhead',  label:'Secondary Deadhead',  maxStacks:6,  restriction:'secondary'},
  {key:'shotgun_deadhead',    label:'Shotgun Deadhead',    maxStacks:6,  restriction:'shotgun'},
  {key:'primary_dexterity',   label:'Primary Dexterity',   maxStacks:6,  restriction:'primary'},
  {key:'secondary_dexterity', label:'Secondary Dexterity', maxStacks:6,  restriction:'secondary'},
  {key:'cascadia_flare',      label:'Cascadia Flare',      maxStacks:12, restriction:'secondary'},
  {key:'cascadia_empowered',  label:'Cascadia Empowered',  maxStacks:5,  restriction:'secondary'},
  {key:'cascadia_overcharge', label:'Cascadia Overcharge',  maxStacks:1,  restriction:'secondary'},
];
