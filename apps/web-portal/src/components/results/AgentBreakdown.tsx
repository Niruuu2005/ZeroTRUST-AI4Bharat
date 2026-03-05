import { motion } from 'framer-motion';
import { BrainCircuit, Activity, ShieldCheck, ShieldAlert, Binary } from 'lucide-react';

export function AgentBreakdown({ verdicts }: { verdicts: Record<string, any> }) {
  const agents = Object.entries(verdicts || {});

  if (agents.length === 0) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 px-2">
        <div>
          <h3 className="text-2xl font-black text-white tracking-tight flex items-center gap-3">
            <BrainCircuit className="text-blue-500" /> Cognitive Consensus
          </h3>
          <p className="text-sm text-slate-500 font-medium">Distributed analysis from 6 specialized AI neural networks</p>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-slate-600 bg-white/5 py-1 px-3 rounded-full">
          <Activity size={12} className="text-blue-500 animate-pulse" /> Scanning Active
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map(([name, data], i) => {
          const v = data.verdict;
          const isPositive = v === 'supports';
          const isNegative = v === 'contradicts';
          const isMixed = v === 'mixed';

          const glowClass = isPositive ? 'shadow-emerald-500/10' :
            isNegative ? 'shadow-red-500/10' :
              isMixed ? 'shadow-amber-500/10' : '';

          const borderClass = isPositive ? 'border-emerald-500/20' :
            isNegative ? 'border-red-500/20' :
              isMixed ? 'border-amber-500/20' : 'border-white/5';

          const textClass = isPositive ? 'text-emerald-400' :
            isNegative ? 'text-red-400' :
              isMixed ? 'text-amber-400' : 'text-slate-400';

          return (
            <motion.div
              key={name}
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: i * 0.05 + 0.5 }}
              whileHover={{ y: -5, borderColor: 'rgba(255,255,255,0.1)' }}
              className={`glass-card p-6 border relative overflow-hidden group ${borderClass} ${glowClass}`}
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-white/5 to-transparent blur-2xl -z-10" />

              <div className="flex justify-between items-start mb-6">
                <div className="flex flex-col">
                  <span className="font-black text-[10px] uppercase tracking-[0.2em] text-slate-500 mb-1">
                    Intelligence Core
                  </span>
                  <span className="font-black text-sm text-white uppercase group-hover:text-blue-400 transition-colors">
                    {name.replace('_', ' ')}
                  </span>
                </div>
                {isPositive ? <ShieldCheck size={18} className="text-emerald-500" /> : <Binary size={18} className="text-slate-600" />}
              </div>

              <div className="flex items-center gap-2 mb-4">
                <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${data.confidence * 100}%` }}
                    transition={{ duration: 1, delay: 1 }}
                    className={`h-full bg-gradient-to-r from-blue-600 to-indigo-600 shadow-[0_0_10px_rgba(37,99,235,0.5)]`}
                  />
                </div>
                <span className="text-[10px] font-black text-slate-400 tracking-tighter w-8 text-right">
                  {Math.round(data.confidence * 100)}%
                </span>
              </div>

              <div className={`text-base font-black uppercase tracking-widest mb-3 ${textClass}`}>
                {v}
              </div>

              <p className="text-xs text-slate-400 leading-relaxed font-medium">
                {data.summary}
              </p>

              {name === 'sentiment' && data.manipulation_score !== undefined && (
                <div className="mt-6 pt-5 border-t border-white/5">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-[10px] font-black uppercase text-slate-500 tracking-widest">Manipulation Risk</span>
                    <span className={`text-[10px] font-black ${data.manipulation_score > 0.5 ? 'text-red-400' : 'text-emerald-400'}`}>
                      {(data.manipulation_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full h-1 bg-black/20 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${data.manipulation_score > 0.5 ? 'bg-red-500' : 'bg-blue-500'}`}
                      style={{ width: `${data.manipulation_score * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
