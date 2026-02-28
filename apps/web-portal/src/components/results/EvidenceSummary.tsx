import { motion } from 'framer-motion';

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
    <div className="glass-card p-6">
      <h3 className="text-sm uppercase tracking-widest font-bold text-slate-400 mb-4">Evidence Summary</h3>
      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-xs font-medium text-slate-500 mb-1">
            <span>Supporting</span>
            <span>{supporting} sources</span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-emerald-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${supportPct}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs font-medium text-slate-500 mb-1">
            <span>Contradicting</span>
            <span>{contradicting} sources</span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-red-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${contraPct}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        </div>
        <div>
          <div className="flex justify-between text-xs font-medium text-slate-500 mb-1">
            <span>Neutral</span>
            <span>{neutral} sources</span>
          </div>
          <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-slate-400 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${neutralPct}%` }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
