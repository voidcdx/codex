import React from 'react';
import { Multiplier } from '../data/elements';
import * as LucideIcons from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

interface MultiplierCardProps {
  title: string;
  icon: string;
  multipliers: Multiplier[];
}

export const MultiplierCard: React.FC<MultiplierCardProps> = ({ title, icon, multipliers }) => {
  const Icon = (LucideIcons as any)[icon];

  const data = multipliers.map(m => ({
    name: m.type,
    value: m.value * 100,
    displayValue: m.value > 0 ? `+${m.value * 100}%` : `${m.value * 100}%`
  }));

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-warframe-card border border-warframe-accent p-3 rounded-lg shadow-2xl text-xs flex flex-col gap-1 min-w-[120px]">
          <div className="flex items-center justify-between gap-4">
            <span className="text-gray-400 font-bold uppercase tracking-wider">{data.name}</span>
            <span className={`font-mono font-black ${data.value > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {data.displayValue}
            </span>
          </div>
          <div className="h-px bg-warframe-accent/50 w-full my-1" />
          <div className="text-[10px] text-gray-500 flex justify-between">
            <span>MODIFIER</span>
            <span className="text-gray-300">{data.value > 0 ? 'BONUS' : 'PENALTY'}</span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="hardware-card p-4 flex flex-col gap-3 min-w-[240px] h-[220px]">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-gray-400 uppercase tracking-widest text-xs font-bold">
          {Icon && <Icon size={14} />}
          {title}:
        </div>
        <div className="text-[10px] text-gray-600 font-mono">DATA_STREAM_01</div>
      </div>
      
      <div className="flex-1 w-full">
        {multipliers.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <defs>
                <linearGradient id="barGradientPos" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#4ade80" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#4ade80" stopOpacity={1} />
                </linearGradient>
                <linearGradient id="barGradientNeg" x1="1" y1="0" x2="0" y2="0">
                  <stop offset="0%" stopColor="#f87171" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#f87171" stopOpacity={1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#3d4455" horizontal={false} />
              <XAxis 
                type="number" 
                domain={[-100, 100]} 
                hide 
              />
              <YAxis 
                dataKey="name" 
                type="category" 
                axisLine={false}
                tickLine={false}
                tick={{ fill: '#9ca3af', fontSize: 10, fontWeight: 'bold' }}
                width={70}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)' }} />
              <ReferenceLine x={0} stroke="#c5a059" strokeWidth={1} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={12}>
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.value > 0 ? 'url(#barGradientPos)' : 'url(#barGradientNeg)'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-gray-600 italic">
            NO_MULTIPLIERS_DETECTED
          </div>
        )}
      </div>
      
      <div className="flex justify-between items-center px-1 border-t border-warframe-accent/30 pt-2">
        <div className="flex gap-1">
          <div className="w-1 h-1 bg-warframe-gold/50 rounded-full" />
          <div className="w-1 h-1 bg-warframe-gold/50 rounded-full" />
          <div className="w-1 h-1 bg-warframe-gold/50 rounded-full" />
        </div>
        <span className="text-[8px] text-gray-500 font-mono tracking-tighter">ANALYSIS_COMPLETE</span>
      </div>
    </div>
  );
};
