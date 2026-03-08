"use client";

import { motion } from 'framer-motion';
import { ShieldCheck, AlertCircle, ExternalLink } from 'lucide-react';

export default function ResultPreview() {
    return (
        <div className="w-full max-w-2xl glass-card overflow-hidden border-white/10 bg-black/40">
            <div className="p-8 border-b border-white/5 bg-gradient-to-br from-cyan-500/10 to-transparent">
                <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center gap-3">
                        <div className="bg-cyan-500 p-2 rounded-xl text-black">
                            <ShieldCheck size={24} />
                        </div>
                        <div>
                            <h3 className="text-xl font-black text-white tracking-tight">VERIFICATION REPORT</h3>
                            <p className="text-[10px] uppercase tracking-[0.2em] font-bold text-cyan-400">Claim ID: #ZT-9821</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-4xl font-black text-cyan-400">88%</div>
                        <div className="text-[10px] uppercase tracking-[0.2em] font-bold text-white/30">Credibility</div>
                    </div>
                </div>

                <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-sm font-medium text-white/70 leading-relaxed italic">
                    "The reported claim regarding the 2026 climate accord expansion is supported by 8 unique international news agencies and official government records."
                </div>
            </div>

            <div className="p-8 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <h4 className="text-[10px] uppercase tracking-[0.2em] font-black text-white/30 mb-4">Evidence Sources</h4>
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors cursor-pointer group">
                                <span className="text-xs font-bold text-white/60">REUTERS_GLOBAL_{i}</span>
                                <ExternalLink size={12} className="text-white/20 group-hover:text-cyan-400" />
                            </div>
                        ))}
                    </div>
                </div>
                <div>
                    <h4 className="text-[10px] uppercase tracking-[0.2em] font-black text-white/30 mb-4">Risk Factors</h4>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                            <AlertCircle size={16} className="text-yellow-500" />
                            <span className="text-xs font-bold text-yellow-500/80 uppercase tracking-wider">Mild Bias Found</span>
                        </div>
                        <div className="flex items-center gap-3 p-3 rounded-xl bg-green-500/10 border border-green-500/20">
                            <ShieldCheck size={16} className="text-green-500" />
                            <span className="text-xs font-bold text-green-500/80 uppercase tracking-wider">Verified Source</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
