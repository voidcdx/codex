// Copyright (c) 2026 Void Codex. All rights reserved.

import { useState } from 'react';
import { ELEMENTS, ElementData } from './data/elements';
import { ElementalWheel } from './components/ElementalWheel';
import { MultiplierCard } from './components/MultiplierCard';
import { SelectedElementHeader } from './components/SelectedElementHeader';
import { ElementalCombiner } from './components/ElementalCombiner';
import { Activity } from 'lucide-react';

export default function AlchemyPage() {
  const [selectedElement, setSelectedElement] = useState<ElementData>(
    ELEMENTS.find(e => e.id === 'corrosive') || ELEMENTS[0]
  );

  return (
    <div className="w-full p-4 sm:p-8 grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-start text-gray-100">
      {/* Left Side: Visualizers */}
      <div className="flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center hardware-card p-8 bg-black/20 rounded-2xl border border-warframe-accent/30 shadow-2xl">
          <ElementalWheel
            selectedElement={selectedElement}
            onSelect={setSelectedElement}
          />
          <div className="mt-8 text-center max-w-md">
            <p className="text-gray-500 text-[10px] italic uppercase tracking-[0.3em] font-black">
              Interactive Elemental Matrix
            </p>
          </div>
        </div>

        <ElementalCombiner onResultSelect={setSelectedElement} />
      </div>

      {/* Right Side: Analysis */}
      <div className="flex flex-col gap-8 lg:sticky lg:top-8">
        <div className="flex flex-col gap-4">
          <h2 className="text-2xl font-black tracking-tight text-white uppercase flex items-center gap-3">
            Damage Analysis
            <div className="h-px flex-1 bg-gradient-to-r from-warframe-gold/50 to-transparent" />
          </h2>

          <SelectedElementHeader element={selectedElement} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <MultiplierCard
            title="Armor"
            icon="ShieldAlert"
            multipliers={selectedElement.multipliers.armor}
          />
          <MultiplierCard
            title="Flesh"
            icon="User"
            multipliers={selectedElement.multipliers.flesh}
          />
          <MultiplierCard
            title="Shields"
            icon="ShieldCheck"
            multipliers={selectedElement.multipliers.shields}
          />
          <MultiplierCard
            title="Machinery"
            icon="Settings"
            multipliers={selectedElement.multipliers.machinery}
          />
        </div>

        {/* Tactical Tip */}
        <div className="hardware-card p-6 bg-warframe-gold/5 border-warframe-gold/20 flex items-start gap-4 relative overflow-hidden rounded-xl border">
          <div className="absolute right-0 top-0 w-32 h-32 bg-warframe-gold/5 blur-3xl rounded-full -mr-16 -mt-16" />
          <div className="p-3 bg-warframe-gold/20 rounded-xl relative z-10">
            <Activity className="text-warframe-gold" size={24} />
          </div>
          <div className="relative z-10">
            <h4 className="text-warframe-gold font-black text-sm uppercase tracking-widest">Tactical Optimization</h4>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed max-w-md">
              {selectedElement.id === 'corrosive'
                ? 'Corrosive damage is essential for stripping Ferrite Armor. It provides a permanent 80% armor reduction on the first stack, increasing with subsequent procs.'
                : selectedElement.id === 'viral'
                ? 'Viral damage increases damage dealt to health. It is the meta choice for high-level content when paired with Slash procs.'
                : 'Elemental damage types have unique status effects. Analyze the enemy faction and health type to maximize your combat efficiency.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
