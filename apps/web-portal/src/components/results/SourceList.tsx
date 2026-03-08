import { motion } from 'framer-motion';
import { ExternalLink, CheckCircle, XCircle, MinusCircle, Database, Search } from 'lucide-react';

export function SourceList({ sources }: { sources: any[] }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 px-2">
        <div>
          <h3 className="text-2xl font-black text-white tracking-tight flex items-center gap-3">
            <Database className="text-indigo-500" /> Evidence Archives
          </h3>
          <p className="text-sm text-slate-500 font-medium">Verified cross-references from the global data mesh</p>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400 bg-indigo-500/10 py-1.5 px-4 rounded-full border border-indigo-500/20">
          <Search size={12} /> {sources.length} Independent Citations
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar p-1">
        {sources.map((s, i) => {
          const StanceIcon =
            s.stance === 'supporting' ? CheckCircle :
              s.stance === 'contradicting' ? XCircle :
                MinusCircle;

          const stanceColor =
            s.stance === 'supporting' ? 'text-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.3)]' :
              s.stance === 'contradicting' ? 'text-red-400 shadow-[0_0_10px_rgba(248,113,113,0.3)]' :
                'text-slate-500';

          return (
            <motion.div
              key={i}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: (i % 10) * 0.05 + 0.8 }}
              className="group p-5 glass-card border-white/5 hover:border-blue-500/30 hover:bg-white/[0.05] transition-all flex gap-6 items-start"
            >
              <div className="mt-1 p-2 bg-black/40 rounded-xl">
                <StanceIcon className={stanceColor} size={24} strokeWidth={2.5} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg border ${s.credibility_tier === 'tier_1' ? 'border-purple-500/30 text-purple-400 bg-purple-500/10' :
                        s.credibility_tier === 'tier_2' ? 'border-blue-500/30 text-blue-400 bg-blue-500/10' :
                          'border-white/10 text-slate-500 bg-white/5'
                      }`}>
                      {s.credibility_tier.replace('_', ' ')}
                    </span>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 bg-white/5 px-2.5 py-1 rounded-lg">
                      {s.source_type}
                    </span>
                  </div>
                  {s.published_at && (
                    <span className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Record Date: {s.published_at.split('T')[0]}</span>
                  )}
                </div>

                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="group/link inline-flex items-center gap-2 font-black text-white hover:text-blue-400 text-lg tracking-tight mb-2 transition-colors"
                >
                  <span className="line-clamp-1">{s.title}</span>
                  <ExternalLink size={16} className="text-slate-600 transition-all group-hover/link:text-blue-400 group-hover/link:translate-x-1" />
                </a>

                <p className="text-sm text-slate-400 line-clamp-2 leading-relaxed font-medium">
                  {s.excerpt}
                </p>

                <div className="mt-4 flex items-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <div className="h-px flex-1 bg-white/5"></div>
                  <span className="text-[10px] font-black uppercase tracking-[0.3em] text-blue-500/50 italic">Secure Citation Verified</span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
