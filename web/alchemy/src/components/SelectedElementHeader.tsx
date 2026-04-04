// Copyright (c) 2026 Void Codex. All rights reserved.

import React from 'react';
import { ElementData, ELEMENTS } from '../data/elements';
import * as LucideIcons from 'lucide-react';
import { motion } from 'framer-motion';

interface SelectedElementHeaderProps {
  element: ElementData;
}

export const SelectedElementHeader: React.FC<SelectedElementHeaderProps> = ({ element }) => {
  const getIcon = (name: string, color: string, size = 24, className = "") => {
    if (name === 'Explosion') {
      return (
        <svg 
          width={size} 
          height={size} 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke={color} 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          className={className}
        >
          <path d="M12 0l2 7 8-4-5 7 7 4-6 2 2 6-5-3-3 5-3-5-5 3 2-6-6-2 7-4-5-7 8 4 2-7z" />
        </svg>
      );
    }
    const Icon = (LucideIcons as any)[name];
    return Icon ? <Icon size={size} style={{ color }} className={className} /> : null;
  };

  const componentElements = element.components?.map(cId => 
    ELEMENTS.find(e => e.id === cId)
  );

  return (
    <div className="hardware-card p-6 bg-gradient-to-br from-warframe-card to-warframe-accent/30 shadow-2xl relative overflow-hidden">
      {/* Background Glow */}
      <div 
        className="absolute -right-20 -top-20 w-64 h-64 blur-[100px] opacity-20 pointer-events-none"
        style={{ backgroundColor: element.color }}
      />

      <div className="flex items-center justify-between relative z-10">
        <div className="flex items-center gap-6">
          <div 
            className="w-20 h-20 rounded-2xl flex items-center justify-center shadow-2xl relative group"
            style={{ backgroundColor: `${element.color}15`, border: `1px solid ${element.color}40` }}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent rounded-2xl" />
            {getIcon(element.icon, element.color, 40, "relative z-10 drop-shadow-[0_0_8px_rgba(0,0,0,0.5)]")}
          </div>
          
          <div className="flex flex-col">
            <h2 className="text-4xl font-black tracking-tighter uppercase text-white flex items-center gap-3">
              {element.name}
              {element.components && (
                <span className="text-gray-500 font-light text-2xl">+</span>
              )}
              {componentElements?.map((ce, i) => {
                return ce && (
                  <div key={i} className="drop-shadow-[0_0_5px_rgba(0,0,0,0.5)]">
                    {getIcon(ce.icon, ce.color, 28)}
                  </div>
                );
              })}
            </h2>
            
            {element.components && (
              <div className="flex items-center gap-2 text-[11px] font-bold mt-1 tracking-widest">
                <span className="text-gray-500 uppercase">({componentElements?.[0]?.name}</span>
                <span className="text-gray-600">+</span>
                <span className="text-gray-500 uppercase">{componentElements?.[1]?.name})</span>
              </div>
            )}
          </div>
        </div>
        
        <div className="flex flex-col items-end">
          <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10 mb-2">
            <span className="text-[10px] text-gray-400 uppercase tracking-[0.2em] font-black">Status Active</span>
          </div>
          <span className="text-sm font-medium text-gray-400 italic">
            {element.name === 'Corrosive' ? 'Reduces target armor permanently' : 
             element.name === 'Viral' ? 'Increases damage to health' : 
             element.name === 'Radiation' ? 'Causes enemies to attack each other' :
             element.name === 'Magnetic' ? 'Disrupts shields and energy' :
             element.name === 'Gas' ? 'Creates a cloud of toxin damage' :
             element.name === 'Blast' ? 'Knocks down enemies' :
             'Elemental damage type'}
          </span>
        </div>
      </div>
    </div>
  );
};
