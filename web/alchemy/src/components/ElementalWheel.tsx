import React from 'react';
import { motion } from 'motion/react';
import * as LucideIcons from 'lucide-react';
import { ElementData, ELEMENTS } from '../data/elements';

interface ElementalWheelProps {
  selectedElement: ElementData;
  onSelect: (element: ElementData) => void;
}

export const ElementalWheel: React.FC<ElementalWheelProps> = ({ selectedElement, onSelect }) => {
  const innerElements = ELEMENTS.filter(e => !e.components);
  const outerElements = ELEMENTS.filter(e => e.components);

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

  return (
    <div className="relative w-[500px] h-[500px] flex items-center justify-center">
      {/* Background Decorative Rings */}
      <div className="absolute inset-0 border-[1px] border-warframe-accent/20 rounded-full" />
      <div className="absolute inset-4 border-[1px] border-warframe-accent/10 rounded-full" />
      <div className="absolute inset-12 border-[8px] border-warframe-accent/10 rounded-full" />
      <div className="absolute inset-12 border-[1px] border-warframe-gold/20 rounded-full" />
      
      {/* Rotating Ring Effect */}
      <motion.div 
        animate={{ rotate: 360 }}
        transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
        className="absolute inset-12 border-t-2 border-b-2 border-warframe-gold/10 rounded-full"
      />

      {/* Inner Ring */}
      <div className="absolute inset-[100px] border-[1px] border-warframe-accent/40 rounded-full" />
      
      {/* Decorative lines/glows */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(197,160,89,0.05)_0%,transparent_70%)] rounded-full pointer-events-none" />

      {/* Center Logo */}
      <div className="absolute z-10 w-28 h-28 bg-warframe-card border-2 border-warframe-gold/50 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(197,160,89,0.2)] overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-tr from-warframe-gold/10 to-transparent" />
        <LucideIcons.Atom className="text-warframe-gold relative z-10" size={56} />
      </div>

      {/* Inner Elements (4) */}
      {innerElements.map((element, index) => {
        // Cold: -135, Electricity: -45, Heat: 135, Toxin: 45
        const angles = [-135, -45, 135, 45];
        const angle = angles[index];
        const radius = 110;
        const x = Math.cos((angle * Math.PI) / 180) * radius;
        const y = Math.sin((angle * Math.PI) / 180) * radius;

        return (
          <motion.button
            key={element.id}
            onClick={() => onSelect(element)}
            className={`absolute z-20 w-16 h-16 rounded-full flex flex-col items-center justify-center transition-all duration-300 ${
              selectedElement.id === element.id 
                ? 'bg-white/10 scale-110 shadow-[0_0_20px_rgba(255,255,255,0.15)]' 
                : 'hover:bg-white/5'
            }`}
            style={{ x, y }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="relative overflow-hidden rounded-full">
              {getIcon(element.icon, element.color, 24, "relative z-10")}
              {selectedElement.id === element.id && (
                <>
                  <motion.div 
                    layoutId="inner-glow"
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ 
                      scale: [1, 1.2, 1],
                      opacity: [0.3, 0.5, 0.3]
                    }}
                    transition={{ 
                      duration: 2, 
                      repeat: Infinity,
                      ease: "easeInOut"
                    }}
                    className="absolute inset-0 blur-lg"
                    style={{ backgroundColor: element.color }}
                  />
                  <motion.div
                    initial={{ x: '-100%' }}
                    animate={{ x: '100%' }}
                    transition={{ duration: 0.5, ease: "easeInOut" }}
                    className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-12 pointer-events-none"
                  />
                </>
              )}
            </div>
            <span className="text-[9px] mt-1 font-bold text-gray-400 uppercase tracking-tighter">
              {element.name}
            </span>
          </motion.button>
        );
      })}

      {/* Outer Elements (6) */}
      {outerElements.map((element, index) => {
        // Top: -90, Top-Right: -30, Bottom-Right: 30, Bottom: 90, Bottom-Left: 150, Top-Left: 210
        const angles = [-90, -30, 30, 90, 150, 210];
        const angle = angles[index];
        const radius = 200;
        const x = Math.cos((angle * Math.PI) / 180) * radius;
        const y = Math.sin((angle * Math.PI) / 180) * radius;

        return (
          <motion.button
            key={element.id}
            onClick={() => onSelect(element)}
            className={`absolute z-20 w-20 h-20 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
              selectedElement.id === element.id 
                ? 'border-warframe-gold bg-warframe-gold/10 scale-110 shadow-[0_0_30px_rgba(197,160,89,0.3)]' 
                : 'border-warframe-accent bg-warframe-card hover:border-gray-400'
            }`}
            style={{ x, y }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <div className="relative overflow-hidden rounded-full">
               {getIcon(element.icon, element.color, 24, "relative z-10")}
               {selectedElement.id === element.id && (
                 <>
                   <motion.div 
                     layoutId="outer-glow"
                     initial={{ scale: 0.8, opacity: 0 }}
                     animate={{ 
                       scale: [1, 1.3, 1],
                       opacity: [0.4, 0.6, 0.4]
                     }}
                     transition={{ 
                       duration: 2.5, 
                       repeat: Infinity,
                       ease: "easeInOut"
                     }}
                     className="absolute inset-0 blur-xl"
                     style={{ backgroundColor: element.color }}
                   />
                   <motion.div
                     initial={{ x: '-100%' }}
                     animate={{ x: '100%' }}
                     transition={{ duration: 0.6, ease: "easeInOut" }}
                     className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent skew-x-12 pointer-events-none"
                   />
                 </>
               )}
            </div>
          </motion.button>
        );
      })}
    </div>
  );
};
