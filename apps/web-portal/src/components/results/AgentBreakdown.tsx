import { motion } from 'framer-motion';

export function AgentBreakdown({ verdicts }: { verdicts: Record<string, any> }) {
  const agents = Object.entries(verdicts || {});
  
  if (agents.length === 0) return null;

  return (
    <div className="glass-card p-6 border border-slate-200">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
        <h3 className="text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
          🧠 Agent Consensus
        </h3>
        <p className="text-sm text-slate-500 font-medium">Analyses from 6 specialized AI models</p>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map(([name, data], i) => {
          const v = data.verdict;
          const bg = v === 'supports' ? 'bg-emerald-50 border-emerald-100' : 
                     v === 'contradicts' ? 'bg-red-50 border-red-100' : 
                     v === 'mixed' ? 'bg-amber-50 border-amber-100' : 
                     'bg-slate-50 border-slate-100';
                     
          const color = v === 'supports' ? 'text-emerald-700' : 
                        v === 'contradicts' ? 'text-red-700' : 
                        v === 'mixed' ? 'text-amber-700' : 
                        'text-slate-600';

          return (
            <motion.div 
              key={name}
              initial={{ y: 10, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: i * 0.1 }}
              className={`p-4 rounded-xl border ${bg} transition-all duration-300 hover:shadow-md hover:-translate-y-1`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="font-bold text-sm uppercase tracking-wider text-slate-800">
                  {name.replace('_', ' ')}
                </span>
                <span className="text-xs font-bold text-slate-400 bg-white px-2 py-0.5 rounded-full shadow-sm">
                  {Math.round(data.confidence * 100)}% conf
                </span>
              </div>
              <div className={`text-sm font-bold capitalize mb-2 ${color}`}>
                {v}
              </div>
              <p className="text-xs text-slate-600 leading-relaxed line-clamp-3">
                {data.summary}
              </p>
              {name === 'sentiment' && data.manipulation_score !== undefined && (
                <div className="mt-3 pt-3 border-t border-black/5 flex justify-between items-center">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Manipulation</span>
                  <div className="w-16 h-1.5 bg-white rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${data.manipulation_score > 0.5 ? 'bg-red-500' : 'bg-slate-300'}`} 
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
