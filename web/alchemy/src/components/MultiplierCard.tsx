// Copyright (c) 2026 Void Codex. All rights reserved.

import React, { useState } from 'react';
import { Multiplier } from '../data/elements';
import * as LucideIcons from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MultiplierCardProps {
  title: string;
  icon: string;
  multipliers: Multiplier[];
  accentColor?: string;
}

interface BarTooltipProps {
  entry: { name: string; value: number; displayValue: string };
  x: number;
  y: number;
}

const BarTooltip: React.FC<BarTooltipProps> = ({ entry, x, y }) => (
  <motion.div
    initial={{ opacity: 0, y: 4 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: 4 }}
    transition={{ duration: 0.12 }}
    className="fixed z-50 pointer-events-none"
    style={{ left: x, top: y - 48 }}
  >
    <div className="bg-[#1a1c24] border border-[#3d4455] px-3 py-1.5 rounded text-[10px] font-mono shadow-xl whitespace-nowrap">
      <span className="text-gray-400 uppercase tracking-wider">{entry.name}</span>
      <span className="mx-2 text-gray-600">|</span>
      <span className={entry.value > 0 ? 'text-green-400' : 'text-red-400'}>
        {entry.displayValue}
      </span>
    </div>
  </motion.div>
);

export const MultiplierCard: React.FC<MultiplierCardProps> = ({ title, icon, multipliers, accentColor }) => {
  const Icon = (LucideIcons as any)[icon];
  const [hovered, setHovered] = useState<number | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  const data = multipliers.map(m => ({
    name: m.type,
    value: m.value * 100,
    displayValue: m.value > 0 ? `+${Math.round(m.value * 100)}%` : `${Math.round(m.value * 100)}%`,
    raw: m.value
  }));

  // Max absolute value for scaling bars (cap at 100)
  const maxAbs = Math.max(100, ...data.map(d => Math.abs(d.value)));

  const handleMouseMove = (e: React.MouseEvent) => {
    setTooltipPos({ x: e.clientX, y: e.clientY });
  };

  return (
    <div className="hardware-card p-4 flex flex-col gap-3 min-w-[240px]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-400 uppercase tracking-widest text-xs font-bold">
          {Icon && <Icon size={14} />}
          {title}
        </div>
        <div className="text-[10px] text-gray-600 font-mono tracking-tight">
          {multipliers.length > 0 ? `${multipliers.length} MATCH` : 'NEUTRAL'}
        </div>
      </div>

      {/* Bars */}
      <div className="flex flex-col gap-2">
        {data.length > 0 ? (
          data.map((entry, i) => {
            const isPositive = entry.value > 0;
            const widthPct = Math.abs(entry.value) / maxAbs * 100;
            const barColor = isPositive ? '#4ade80' : '#f87171';
            const glowColor = isPositive ? 'rgba(74, 222, 128, 0.4)' : 'rgba(248, 113, 113, 0.4)';

            return (
              <div
                key={entry.name}
                className="group relative"
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                onMouseMove={handleMouseMove}
              >
                {/* Label row */}
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] text-gray-400 font-semibold uppercase tracking-wide">
                    {entry.name}
                  </span>
                  <motion.span
                    className={`text-xs font-mono font-black tabular-nums ${isPositive ? 'text-green-400' : 'text-red-400'}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.15 + i * 0.08 }}
                  >
                    {entry.displayValue}
                  </motion.span>
                </div>

                {/* Bar track */}
                <div className="relative h-[10px] bg-[#1a1c24] rounded-sm overflow-hidden border border-[#2a2d38]">
                  {/* Filled bar */}
                  <motion.div
                    className="absolute top-0 h-full rounded-sm"
                    style={{
                      left: isPositive ? 0 : undefined,
                      right: isPositive ? undefined : 0,
                      background: `linear-gradient(${isPositive ? '90deg' : '270deg'}, ${barColor}22, ${barColor})`,
                    }}
                    initial={{ width: 0 }}
                    animate={{ width: `${widthPct}%` }}
                    transition={{ duration: 0.5, delay: 0.1 + i * 0.08, ease: [0.25, 0.46, 0.45, 0.94] }}
                  />

                  {/* Glow tip */}
                  <motion.div
                    className="absolute top-0 h-full w-[3px] rounded-full"
                    style={{
                      background: barColor,
                      boxShadow: `0 0 8px ${glowColor}, 0 0 16px ${glowColor}`,
                      ...(isPositive
                        ? { left: `${widthPct}%`, transform: 'translateX(-100%)' }
                        : { right: `${widthPct}%`, transform: 'translateX(100%)' }
                      ),
                    }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3, delay: 0.5 + i * 0.08 }}
                  />

                  {/* Hover pulse overlay */}
                  <motion.div
                    className="absolute inset-0 rounded-sm"
                    style={{ background: `${barColor}08` }}
                    animate={{ opacity: hovered === i ? 1 : 0 }}
                    transition={{ duration: 0.15 }}
                  />
                </div>
              </div>
            );
          })
        ) : (
          <div className="h-16 flex items-center justify-center text-[11px] text-gray-600 font-mono tracking-wider">
            NO MODIFIER
          </div>
        )}
      </div>

      {/* Footer line */}
      <div className="h-px bg-gradient-to-r from-transparent via-[#3d4455] to-transparent mt-1" />

      {/* Tooltip */}
      <AnimatePresence>
        {hovered !== null && data[hovered] && (
          <BarTooltip
            entry={data[hovered]}
            x={tooltipPos.x + 12}
            y={tooltipPos.y}
          />
        )}
      </AnimatePresence>
    </div>
  );
};
