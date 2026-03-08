import { motion } from 'framer-motion';
import { VerificationResult } from '../../store/verificationStore';
import { ShieldAlert, ShieldCheck, HelpCircle, Zap, Fingerprint } from 'lucide-react';

export function CredibilityScore({ result }: { result: VerificationResult }) {
  const { credibility_score, category, confidence, cached, claim_type } = result;

  const colorStr =
    credibility_score >= 70 ? 'text-emerald-400' :
      credibility_score >= 40 ? 'text-amber-400' :
        'text-red-400';

  const glowColor =
    credibility_score >= 70 ? 'shadow-emerald-500/20' :
      credibility_score >= 40 ? 'shadow-amber-500/20' :
        'shadow-red-500/20';

  const borderColor =
    credibility_score >= 70 ? 'border-emerald-500/30' :
      credibility_score >= 40 ? 'border-amber-500/30' :
        'border-red-500/30';

  const Icon = credibility_score >= 70 ? ShieldCheck : credibility_score >= 40 ? HelpCircle : ShieldAlert;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`glass-card-heavy p-8 flex flex-col items-center justify-center text-center overflow-hidden relative border ${borderColor} ${glowColor}`}
    >
      <div className="absolute top-0 right-0 p-6 flex flex-col items-end gap-2">
        {cached && (
          <motion.div
            initial={{ x: 20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] px-3 py-1.5 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400"
          >
            <Zap size={10} fill="currentColor" /> Neural Cache
          </motion.div>
        )}
        <div className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-[0.2em] px-3 py-1.5 bg-white/5 border border-white/10 rounded-full text-slate-500">
          <Fingerprint size={10} /> {claim_type}
        </div>
      </div>

      <div className="relative mt-4">
        <motion.div
          initial={{ rotate: -90, opacity: 0 }}
          animate={{ rotate: 0, opacity: 1 }}
          transition={{ duration: 1, ease: "circOut" }}
          className="relative"
        >
          <svg className="w-48 h-48 transform -rotate-90">
            <circle cx="96" cy="96" r="88" fill="none" className="stroke-white/5" strokeWidth="4" />
            <motion.circle
              cx="96" cy="96" r="88" fill="none"
              stroke="currentColor" strokeWidth="12" strokeLinecap="round"
              className={colorStr}
              initial={{ strokeDasharray: 553, strokeDashoffset: 553 }}
              animate={{ strokeDashoffset: 553 - (553 * credibility_score) / 100 }}
              transition={{ duration: 2, delay: 0.5, ease: "circOut" }}
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1 }}
              className="flex flex-col items-center"
            >
              <Icon size={32} className={`${colorStr} mb-1 drop-shadow-2xl`} />
              <span className="text-6xl font-black tabular-nums tracking-tighter text-white">
                {credibility_score}
              </span>
              <span className="text-[10px] uppercase font-black text-slate-500 tracking-[0.3em]">Precision</span>
            </motion.div>
          </div>
        </motion.div>
      </div>

      <div className="mt-10 w-full">
        <motion.h2
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className={`text-4xl font-black mb-4 tracking-tighter uppercase ${colorStr}`}
        >
          {category}
        </motion.h2>

        <div className="grid grid-cols-2 gap-4 mt-8">
          <div className="p-5 rounded-3xl bg-white/[0.02] border border-white/5 text-left">
            <div className="text-[10px] uppercase font-black text-slate-500 mb-2 tracking-widest">Confidence Index</div>
            <div className={`text-lg font-bold flex items-center gap-2 ${confidence === 'High' ? 'text-emerald-400' : 'text-blue-400'}`}>
              <span className={`w-2 h-2 rounded-full ${confidence === 'High' ? 'bg-emerald-500' : 'bg-blue-500'} shadow-[0_0_10px_currentColor]`} />
              {confidence} Level
            </div>
          </div>

          <motion.div
            whileHover={{ scale: 1.02 }}
            className="p-5 rounded-3xl bg-blue-600/10 border border-blue-500/20 text-left"
          >
            <div className="text-[10px] uppercase font-black text-blue-500/60 mb-2 tracking-widest">Protocol Status</div>
            <div className="text-lg font-bold text-blue-400">
              Verified Result
            </div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
}
