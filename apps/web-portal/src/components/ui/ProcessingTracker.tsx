"use client";

import { motion } from 'framer-motion';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

const steps = [
    { id: 1, name: 'Agent Research', status: 'complete' },
    { id: 2, name: 'Cross-Referencing', status: 'complete' },
    { id: 3, name: 'Sentiment Analysis', status: 'loading' },
    { id: 4, name: 'Deepfake Scan', status: 'pending' },
    { id: 5, name: 'Final Aggregation', status: 'pending' },
];

export default function ProcessingTracker() {
    return (
        <div className="w-full max-w-md glass-card p-6 border-white/5 bg-white/[0.02]">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-xs font-bold uppercase tracking-widest text-cyan-400">Live Engine Status</h3>
                <div className="px-2 py-1 rounded-md bg-cyan-500/10 text-[10px] font-bold text-cyan-400 animate-pulse">
                    PROCESSING
                </div>
            </div>

            <div className="space-y-4">
                {steps.map((step, i) => (
                    <motion.div
                        key={step.name}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex items-center gap-4"
                    >
                        {step.status === 'complete' ? (
                            <CheckCircle2 size={18} className="text-cyan-400" />
                        ) : step.status === 'loading' ? (
                            <Loader2 size={18} className="text-blue-400 animate-spin" />
                        ) : (
                            <Circle size={18} className="text-white/10" />
                        )}
                        <span className={`text-sm font-medium ${step.status === 'pending' ? 'text-white/20' : 'text-white/80'}`}>
                            {step.name}
                        </span>
                        {step.status === 'loading' && (
                            <div className="flex-1 ml-4 h-[1px] bg-gradient-to-r from-blue-400 to-transparent" />
                        )}
                    </motion.div>
                ))}
            </div>

            <div className="mt-8 pt-6 border-t border-white/5">
                <div className="flex justify-between text-[10px] font-bold text-white/20 mb-2">
                    <span>LATENCY: 124ms</span>
                    <span>92% COMPLETE</span>
                </div>
                <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: '92%' }}
                        className="h-full bg-cyan-500 shadow-[0_0_10px_rgba(0,229,255,0.5)]"
                    />
                </div>
            </div>
        </div>
    );
}
