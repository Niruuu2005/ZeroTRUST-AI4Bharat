import { motion } from 'framer-motion';
import { VerificationResult } from '../../store/verificationStore';
import { ShieldAlert, ShieldCheck, HelpCircle } from 'lucide-react';

export function CredibilityScore({ result }: { result: VerificationResult }) {
  const { credibility_score, category, confidence, cached, claim_type } = result;

  const colorStr =
    credibility_score >= 70 ? 'text-emerald-500' :
    credibility_score >= 40 ? 'text-amber-500' :
    'text-red-500';

  const gradient =
    credibility_score >= 70 ? 'from-emerald-400 to-teal-600' :
    credibility_score >= 40 ? 'from-amber-400 to-orange-500' :
    'from-red-500 to-rose-600';

  const bgColor =
    credibility_score >= 70 ? 'bg-emerald-50 border-emerald-100' :
    credibility_score >= 40 ? 'bg-amber-50 border-amber-100' :
    'bg-red-50 border-red-100';

  const Icon = credibility_score >= 70 ? ShieldCheck : credibility_score >= 40 ? HelpCircle : ShieldAlert;

  return (
    <div className={`glass-card p-8 flex flex-col items-center justify-center text-center overflow-hidden relative border-2 ${bgColor}`}>
      {/* Background decoration */}
      <div className="absolute -top-32 -right-32 w-64 h-64 rounded-full bg-white/40 blur-3xl"></div>
      
      {cached && (
        <span className="absolute top-4 right-4 text-xs font-bold uppercase tracking-wider px-3 py-1 bg-white/60 rounded-full text-slate-500 shadow-sm border border-slate-200 backdrop-blur-md">
          ⚡ Cached
        </span>
      )}

      <div className="relative">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: "spring", stiffness: 100, damping: 15 }}
          className={`w-40 h-40 rounded-full flex items-center justify-center bg-white shadow-2xl shadow-slate-200 relative z-10`}
        >
          {/* Circular progress bar SVG mapping the score out of 100 */}
          <svg className="absolute inset-0 w-full h-full transform -rotate-90">
            <circle cx="80" cy="80" r="70" fill="none" className="stroke-slate-100" strokeWidth="8" />
            <motion.circle
              cx="80" cy="80" r="70" fill="none"
              stroke="url(#gradient)" strokeWidth="8" strokeLinecap="round"
              initial={{ strokeDasharray: 440, strokeDashoffset: 440 }}
              animate={{ strokeDashoffset: 440 - (440 * credibility_score) / 100 }}
              transition={{ duration: 1.5, ease: "easeOut" }}
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" className={credibility_score >= 70 ? 'stop-emerald-400' : credibility_score >= 40 ? 'stop-amber-400' : 'stop-red-500'} />
                <stop offset="100%" className={credibility_score >= 70 ? 'stop-teal-600' : credibility_score >= 40 ? 'stop-orange-500' : 'stop-rose-600'} />
              </linearGradient>
            </defs>
          </svg>

          <div className="flex flex-col items-center">
            <Icon size={32} strokeWidth={2.5} className={`mb-1 ${colorStr}`} />
            <span className={`text-4xl font-black tabular-nums tracking-tighter bg-clip-text text-transparent bg-gradient-to-br ${gradient}`}>
              {credibility_score}
            </span>
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-widest mt-0.5">/ 100</span>
          </div>
        </motion.div>
      </div>

      <div className="mt-8 relative z-10 w-full">
        <h2 className={`text-2xl font-black mb-2 ${colorStr}`}>{category}</h2>
        
        <div className="flex items-center justify-center gap-4 mt-6">
          <div className="px-4 py-2 bg-white rounded-xl shadow-sm border border-slate-100">
            <div className="text-[10px] uppercase font-bold text-slate-400 mb-0.5 tracking-wider">Confidence</div>
            <div className={`text-sm font-bold ${confidence === 'High' ? 'text-emerald-600' : confidence === 'Medium' ? 'text-blue-600' : 'text-slate-600'}`}>
              {confidence}
            </div>
          </div>
          <div className="px-4 py-2 bg-white rounded-xl shadow-sm border border-slate-100">
            <div className="text-[10px] uppercase font-bold text-slate-400 mb-0.5 tracking-wider">Type</div>
            <div className="text-sm font-bold text-slate-700 capitalize">
              {claim_type}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
