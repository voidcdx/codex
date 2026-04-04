export type HealthType = 'Ferrite' | 'Alloy' | 'Cloned' | 'Infested' | 'Proto' | 'Shield' | 'Robotic';

export interface Multiplier {
  type: HealthType;
  value: number; // e.g., 0.75 for +75%, -0.5 for -50%
}

export interface ElementData {
  id: string;
  name: string;
  icon: string; // Lucide icon name or SVG path
  color: string;
  components?: string[]; // IDs of base elements
  multipliers: {
    armor: Multiplier[];
    flesh: Multiplier[];
    shields: Multiplier[];
    machinery: Multiplier[];
  };
}

export const ELEMENTS: ElementData[] = [
  {
    id: 'cold',
    name: 'Cold',
    icon: 'Snowflake',
    color: '#4FC3F7',
    multipliers: {
      armor: [{ type: 'Alloy', value: 0.25 }],
      flesh: [{ type: 'Infested', value: 0.25 }],
      shields: [{ type: 'Shield', value: 0.5 }],
      machinery: []
    }
  },
  {
    id: 'electricity',
    name: 'Electricity',
    icon: 'Zap',
    color: '#FFEB3B',
    multipliers: {
      armor: [],
      flesh: [],
      shields: [{ type: 'Shield', value: 0.5 }, { type: 'Proto', value: 0.5 }],
      machinery: [{ type: 'Robotic', value: 0.5 }]
    }
  },
  {
    id: 'heat',
    name: 'Heat',
    icon: 'Flame',
    color: '#FF7043',
    multipliers: {
      armor: [],
      flesh: [{ type: 'Cloned', value: 0.25 }, { type: 'Infested', value: 0.5 }],
      shields: [],
      machinery: [{ type: 'Robotic', value: 0.25 }]
    }
  },
  {
    id: 'toxin',
    name: 'Toxin',
    icon: 'Skull',
    color: '#66BB6A',
    multipliers: {
      armor: [{ type: 'Ferrite', value: 0.25 }],
      flesh: [{ type: 'Cloned', value: 0.25 }],
      shields: [],
      machinery: []
    }
  },
  {
    id: 'corrosive',
    name: 'Corrosive',
    icon: 'Biohazard',
    color: '#8BC34A',
    components: ['toxin', 'electricity'],
    multipliers: {
      armor: [{ type: 'Ferrite', value: 0.75 }, { type: 'Alloy', value: -0.5 }],
      flesh: [{ type: 'Cloned', value: 0.75 }, { type: 'Infested', value: 0.5 }],
      shields: [{ type: 'Proto', value: 0.5 }, { type: 'Shield', value: -0.5 }],
      machinery: [{ type: 'Robotic', value: 0.75 }]
    }
  },
  {
    id: 'radiation',
    name: 'Radiation',
    icon: 'Radiation',
    color: '#FFEE58',
    components: ['heat', 'electricity'],
    multipliers: {
      armor: [{ type: 'Alloy', value: 0.75 }],
      flesh: [{ type: 'Infested', value: -0.5 }],
      shields: [{ type: 'Shield', value: -0.25 }],
      machinery: [{ type: 'Robotic', value: 0.25 }]
    }
  },
  {
    id: 'viral',
    name: 'Viral',
    icon: 'Dna',
    color: '#BA68C8',
    components: ['cold', 'toxin'],
    multipliers: {
      armor: [],
      flesh: [{ type: 'Cloned', value: 0.75 }],
      shields: [],
      machinery: []
    }
  },
  {
    id: 'magnetic',
    name: 'Magnetic',
    icon: 'Magnet',
    color: '#42A5F5',
    components: ['cold', 'electricity'],
    multipliers: {
      armor: [],
      flesh: [],
      shields: [{ type: 'Shield', value: 0.75 }, { type: 'Proto', value: 0.75 }],
      machinery: []
    }
  },
  {
    id: 'gas',
    name: 'Gas',
    icon: 'Cloud',
    color: '#00BFA5',
    components: ['heat', 'toxin'],
    multipliers: {
      armor: [],
      flesh: [{ type: 'Infested', value: 0.75 }],
      shields: [],
      machinery: []
    }
  },
  {
    id: 'blast',
    name: 'Blast',
    icon: 'Explosion',
    color: '#EF5350',
    components: ['cold', 'heat'],
    multipliers: {
      armor: [{ type: 'Ferrite', value: 0.25 }],
      flesh: [],
      shields: [],
      machinery: [{ type: 'Robotic', value: 0.75 }]
    }
  }
];
