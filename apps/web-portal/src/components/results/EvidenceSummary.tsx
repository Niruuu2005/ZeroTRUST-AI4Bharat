import { motion } from 'framer-motion';
import { Layers } from 'lucide-react';

interface EvidenceSummaryProps {
  evidence_summary: { supporting: number; contradicting: number; neutral: number };
}

export function EvidenceSummary({ evidence_summary }: EvidenceSummaryProps) {
  const { supporting = 0, contradicting = 0, neutral = 0 } = evidence_summary;
  const total = supporting + contradicting + neutral || 1;
  const supportPct = Math.round((supporting / total) * 100);
  const contraPct = Math.round((contradicting / total) * 100);
  const neutralPct = 100 - supportPct - contraPct;

  return (
    <div className="glass-card-heavy p-8 border-white/5 bg-gradient-to-br from-white/[0.02] to-transparent">
      <h3 className="text-xs uppercase tracking-[0.2em] font-black text-slate-500 mb-6 flex items-center gap-2">
        <Layers size={14} className="text-blue-500" /> Statistical Weight
      </h3>

      <div className="space-y-6">
        <div className="space-y-2">
          <div className="flex justify-between items-end">
            <span className="text-xs font-black uppercase tracking-widest text-emerald-400">Supporting Evidence</span>
            <span className="text-xl font-black text-white">{supportPct}<span className="text-[10px] text-slate-500 ml-1">%</span></span>
          </div>
          <div className="h-3 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/5">
            <motion.div
              className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full shadow-[0_0_15px_rgba(52,211,153,0.3)]"
              initial={{ width: 0 }}
              animate={{ width: `${supportPct}%` }}
              transition={{ duration: 1.2, ease: 'circOut' }}
            />
          </div>
          <div className="text-[10px] font-black text-slate-600 text-right uppercase tracking-widest">{supporting} Citations Found</div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-end">
            <span className="text-xs font-black uppercase tracking-widest text-red-400">Conflicting Evidence</span>
            <span className="text-xl font-black text-white">{contraPct}<span className="text-[10px] text-slate-500 ml-1">%</span></span>
          </div>
          <div className="h-3 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/5">
            <motion.div
              className="h-full bg-gradient-to-r from-red-600 to-red-400 rounded-full shadow-[0_0_15px_rgba(248,113,113,0.3)]"
              initial={{ width: 0 }}
              animate={{ width: `${contraPct}%` }}
              transition={{ duration: 1.2, ease: 'circOut' }}
            />
          </div>
          <div className="text-[10px] font-black text-slate-600 text-right uppercase tracking-widest">{contradicting} Contradictions Cited</div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between items-end">
            <span className="text-xs font-black uppercase tracking-widest text-slate-400">Ambiguous / Neutral</span>
            <span className="text-xl font-black text-white">{neutralPct}<span className="text-[10px] text-slate-500 ml-1">%</span></span>
          </div>
          <div className="h-3 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/5">
            <motion.div
              className="h-full bg-gradient-to-r from-slate-600 to-slate-400 rounded-full shadow-[0_0_15px_rgba(148,163,184,0.2)]"
              initial={{ width: 0 }}
              animate={{ width: `${neutralPct}%` }}
              transition={{ duration: 1.2, ease: 'circOut' }}
            />
          </div>
          <div className="text-[10px] font-black text-slate-600 text-right uppercase tracking-widest">{neutral} Unverifiable Points</div>
        </div>
      </div>
    </div>
  );
}
