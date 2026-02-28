import { motion } from 'framer-motion';
import { ExternalLink, CheckCircle, XCircle, MinusCircle } from 'lucide-react';

export function SourceList({ sources }: { sources: any[] }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="glass-card p-6 border border-slate-200">
      <div className="flex justify-between items-end border-b border-slate-100 pb-4 mb-4">
        <div>
          <h3 className="text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
            📚 Evidence Sources
          </h3>
          <p className="text-sm text-slate-500 font-medium mt-1">Deduplicated across {sources.length} citations</p>
        </div>
      </div>
      
      <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
        {sources.map((s, i) => {
          const StanceIcon = 
            s.stance === 'supporting' ? CheckCircle : 
            s.stance === 'contradicting' ? XCircle : 
            MinusCircle;
            
          const stanceColor = 
            s.stance === 'supporting' ? 'text-emerald-500' : 
            s.stance === 'contradicting' ? 'text-red-500' : 
            'text-slate-400';

          return (
            <motion.div 
              key={i}
              initial={{ x: -10, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: (i % 10) * 0.05 }}
              className="group p-4 bg-white border border-slate-100 rounded-xl hover:border-blue-200 hover:shadow-md transition-all duration-200 flex gap-4 items-start"
            >
              <div className="mt-1">
                <StanceIcon className={stanceColor} size={20} strokeWidth={2.5} />
              </div>
              <div className="flex-1 min-w-0">
                <a 
                  href={s.url} 
                  target="_blank" 
                  rel="noreferrer"
                  className="font-bold text-slate-800 hover:text-blue-600 line-clamp-1 mb-1 flex items-center gap-1.5 group-hover:underline"
                >
                  {s.title}
                  <ExternalLink size={14} className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                </a>
                <p className="text-sm text-slate-600 line-clamp-2 mb-2 leading-relaxed">
                  {s.excerpt}
                </p>
                <div className="flex items-center gap-3 text-xs font-medium">
                  <span className={`px-2 py-0.5 rounded-full capitalize ${
                    s.credibility_tier === 'tier_1' ? 'bg-purple-100 text-purple-700' :
                    s.credibility_tier === 'tier_2' ? 'bg-blue-100 text-blue-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    {s.credibility_tier.replace('_', ' ')}
                  </span>
                  <span className="text-slate-400 capitalize flex items-center gap-1">
                    {s.source_type}
                  </span>
                  {s.published_at && (
                    <span className="text-slate-400">• {s.published_at.split('T')[0]}</span>
                  )}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
