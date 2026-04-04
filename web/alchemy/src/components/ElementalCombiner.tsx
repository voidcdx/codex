import React, { useState, useEffect } from 'react';
import { ElementData, ELEMENTS } from '../data/elements';
import * as LucideIcons from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

interface ElementalCombinerProps {
  onResultSelect: (element: ElementData) => void;
}

export const ElementalCombiner: React.FC<ElementalCombinerProps> = ({ onResultSelect }) => {
  const [slot1, setSlot1] = useState<ElementData | null>(null);
  const [slot2, setSlot2] = useState<ElementData | null>(null);
  const [result, setResult] = useState<ElementData | null>(null);

  const baseElements = ELEMENTS.filter(e => !e.components);

  useEffect(() => {
    if (slot1 && slot2) {
      if (slot1.id === slot2.id) {
        setResult(slot1);
        return;
      }

      const combination = ELEMENTS.find(e => 
        e.components?.includes(slot1.id) && e.components?.includes(slot2.id)
      );
      
      setResult(combination || null);
    } else {
      setResult(null);
    }
  }, [slot1, slot2]);

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

  const handleSlotClick = (slot: 1 | 2) => {
    if (slot === 1) setSlot1(null);
    else setSlot2(null);
  };

  const handleBaseClick = (element: ElementData) => {
    if (!slot1) setSlot1(element);
    else if (!slot2) setSlot2(element);
    else {
      // If both full, replace slot 2
      setSlot2(element);
    }
  };

  return (
    <div className="hardware-card p-6 flex flex-col gap-6 bg-gradient-to-b from-warframe-card to-warframe-bg">
      <div className="flex items-center justify-between border-b border-warframe-accent/30 pb-4">
        <h3 className="text-sm font-bold uppercase tracking-[0.2em] text-warframe-gold flex items-center gap-2">
          <LucideIcons.FlaskConical size={16} />
          Elemental Combiner
        </h3>
        <div className="text-[10px] text-gray-600 font-mono">SYSTEM_READY</div>
      </div>

      <div className="flex items-center justify-center gap-8 py-4">
        {/* Slot 1 */}
        <div className="flex flex-col items-center gap-2">
          <button 
            onClick={() => handleSlotClick(1)}
            className={`w-20 h-20 rounded-2xl border-2 border-dashed flex items-center justify-center transition-all ${
              slot1 ? 'border-warframe-gold bg-warframe-gold/5' : 'border-warframe-accent hover:border-gray-500'
            }`}
          >
            {slot1 ? getIcon(slot1.icon, slot1.color, 32) : <LucideIcons.Plus className="text-gray-700" />}
          </button>
          <span className="text-[10px] font-bold text-gray-500 uppercase">{slot1?.name || 'Slot 1'}</span>
        </div>

        <LucideIcons.Plus className="text-warframe-accent" size={24} />

        {/* Slot 2 */}
        <div className="flex flex-col items-center gap-2">
          <button 
            onClick={() => handleSlotClick(2)}
            className={`w-20 h-20 rounded-2xl border-2 border-dashed flex items-center justify-center transition-all ${
              slot2 ? 'border-warframe-gold bg-warframe-gold/5' : 'border-warframe-accent hover:border-gray-500'
            }`}
          >
            {slot2 ? getIcon(slot2.icon, slot2.color, 32) : <LucideIcons.Plus className="text-gray-700" />}
          </button>
          <span className="text-[10px] font-bold text-gray-500 uppercase">{slot2?.name || 'Slot 2'}</span>
        </div>

        <LucideIcons.ArrowRight className="text-warframe-gold" size={24} />

        {/* Result */}
        <div className="flex flex-col items-center gap-2">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.button
                key={result.id}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                onClick={() => onResultSelect(result)}
                className="w-24 h-24 rounded-3xl border-2 border-warframe-gold bg-warframe-gold/10 flex items-center justify-center shadow-[0_0_30px_rgba(197,160,89,0.2)] group relative"
              >
                <div className="absolute inset-0 bg-radial-gradient from-warframe-gold/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                {getIcon(result.icon, result.color, 40)}
              </motion.button>
            ) : (
              <div className="w-24 h-24 rounded-3xl border-2 border-warframe-accent bg-black/20 flex items-center justify-center">
                <LucideIcons.ZapOff className="text-gray-800" size={32} />
              </div>
            )}
          </AnimatePresence>
          <span className="text-[10px] font-bold text-warframe-gold uppercase">{result?.name || 'Result'}</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 border-t border-warframe-accent/30 pt-6">
        {baseElements.map(element => (
          <button
            key={element.id}
            onClick={() => handleBaseClick(element)}
            className={`flex flex-col items-center gap-2 p-3 rounded-xl border transition-all ${
              slot1?.id === element.id || slot2?.id === element.id
                ? 'border-warframe-gold bg-warframe-gold/10'
                : 'border-warframe-accent bg-warframe-card hover:border-gray-400'
            }`}
          >
            {getIcon(element.icon, element.color, 20)}
            <span className="text-[9px] font-bold text-gray-400 uppercase">{element.name}</span>
          </button>
        ))}
      </div>

      <div className="mt-2 text-center">
        <p className="text-[9px] text-gray-600 italic">
          Click base elements to combine. Click slots to clear. 
          Resulting element can be clicked to view full analysis.
        </p>
      </div>
    </div>
  );
};
