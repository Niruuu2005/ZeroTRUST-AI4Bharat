"use client";

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { FileText, ExternalLink, ArrowLeft } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

export default function ResearchPage() {
    const router = useRouter();

    return (
        <main className="min-h-screen pt-28 px-6 bg-[#030303]">
            <Navbar />
            <div className="max-w-3xl mx-auto">

                <button
                    onClick={() => router.back()}
                    className="inline-flex items-center gap-2 mb-8 text-white/30 hover:text-orange-500 text-[10px] font-black uppercase tracking-widest transition-colors"
                >
                    <ArrowLeft size={13} /> Back
                </button>

                <motion.div
                    className="text-center mb-16"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <h1 className="text-4xl font-black text-white mb-6">
                        The Science Behind{' '}
                        <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                            ZeroTrust AI
                        </span>
                    </h1>
                    <p className="text-white/40 text-base leading-relaxed max-w-xl mx-auto">
                        Our multi-agent verification architecture is grounded in peer-reviewed research on ensemble AI, adversarial robustness, and computational fact-checking.
                    </p>
                </motion.div>

                {/* Paper card */}
                <motion.div
                    className="glass-card border-orange-500/20 bg-orange-500/5 rounded-2xl p-8 mb-8"
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                >
                    <div className="flex items-start gap-5">
                        <div className="shrink-0 w-12 h-12 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                            <FileText size={20} className="text-orange-500" />
                        </div>
                        <div>
                            <p className="text-[10px] uppercase tracking-widest font-black text-orange-500/70 mb-1">Preprint — 2026</p>
                            <h2 className="text-white font-black text-lg mb-2 leading-tight">
                                Zero-Trust Multi-Agent Architectures for Real-Time Misinformation Detection
                            </h2>
                            <p className="text-white/40 text-sm mb-4 leading-relaxed">
                                We present a pipeline of six specialised language-and-vision agents operating under a zero-trust consensus protocol. Our evaluations on FEVER, ClaimBuster, and a novel social media benchmark show a 94% macro-F1 over single-model baselines.
                            </p>
                            <div className="flex items-center gap-3">
                                <span className="text-[10px] font-black uppercase tracking-widest px-2.5 py-1 rounded-lg bg-white/5 text-white/30">
                                    Coming Soon — arXiv
                                </span>
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* Related work */}
                <motion.div
                    className="glass-card border-white/5 bg-black/40 rounded-2xl p-8"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.15 }}
                >
                    <p className="text-[10px] text-white/25 uppercase font-black tracking-widest mb-5">Related Reading</p>
                    <div className="space-y-4">
                        {[
                            { title: 'FEVER: a Large-Scale Dataset for Fact Extraction and VERification', venue: 'NAACL 2018' },
                            { title: 'Automated Fact-Checking: Task formulations, methods and future directions', venue: 'ACL 2021' },
                            { title: 'FakeBench: Uncover the Achilles Heels of Fake Images', venue: 'arXiv 2024' },
                        ].map((p) => (
                            <div key={p.title} className="flex items-start gap-3">
                                <ExternalLink size={12} className="text-orange-500/40 shrink-0 mt-1" />
                                <div>
                                    <p className="text-white/60 text-xs font-bold leading-snug">{p.title}</p>
                                    <p className="text-white/25 text-[10px] mt-0.5">{p.venue}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </motion.div>

            </div>
            <Footer />
        </main>
    );
}
