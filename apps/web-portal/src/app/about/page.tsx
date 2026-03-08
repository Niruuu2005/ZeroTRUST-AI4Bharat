"use client";

import { motion } from 'framer-motion';
import { ShieldCheck, BrainCircuit, Globe, Lock, Zap, Users, ArrowLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

const PILLARS = [
    {
        icon: BrainCircuit,
        title: 'Multi-Agent Intelligence',
        body: 'Six specialised AI agents — Fact, Deepfake Detector, Bias, Source, Consensus, and Orchestrator — independently analyse every claim and vote on a unified verdict.',
    },
    {
        icon: ShieldCheck,
        title: 'Zero-Trust Verification',
        body: "No single agent is trusted unconditionally. Every verdict requires corroboration across the pipeline, mirroring the security model we're named after.",
    },
    {
        icon: Globe,
        title: 'Real-Time Source Grounding',
        body: 'Agents cross-reference live web sources, academic databases, and structured knowledge graphs rather than relying on static training data alone.',
    },
    {
        icon: Lock,
        title: 'Privacy by Design',
        body: 'Queries are never stored or used for model training. Your browsing habits and submitted claims remain entirely your own.',
    },
    {
        icon: Zap,
        title: 'Edge-Speed Results',
        body: 'Parallel agent execution means full multi-source analysis completes in seconds, not minutes — even for complex geopolitical or scientific claims.',
    },
    {
        icon: Users,
        title: 'Built for Everyone',
        body: 'From journalists and researchers to everyday readers, ZeroTrust AI integrates directly into your browser so verification fits naturally into any workflow.',
    },
];

const fade = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } };

export default function AboutPage() {
    const router = useRouter();
    return (
        <main className="min-h-screen bg-[#030303] pt-28 px-6">
            <Navbar />
            <div className="max-w-3xl mx-auto">
                <button onClick={() => router.back()} className="inline-flex items-center gap-2 mb-8 text-white/30 hover:text-orange-500 text-[10px] font-black uppercase tracking-widest transition-colors">
                    <ArrowLeft size={13} /> Back
                </button>
            </div>

            {/* ── Hero blurb ── */}
            <motion.section
                className="max-w-3xl mx-auto text-center mb-24"
                initial="hidden"
                animate="show"
                variants={{ show: { transition: { staggerChildren: 0.12 } } }}
            >
                <motion.p variants={fade} className="text-[10px] uppercase tracking-[0.3em] font-black text-orange-500 mb-4">
                    About
                </motion.p>

                <motion.h1 variants={fade} className="text-4xl md:text-5xl font-black text-white leading-tight mb-6">
                    Trust should be{' '}
                    <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                        earned, not assumed
                    </span>
                </motion.h1>

                <motion.p variants={fade} className="text-white/50 text-base leading-relaxed max-w-2xl mx-auto">
                    ZeroTrust AI is an open-source, multi-agent fact-verification platform built to combat
                    the spread of misinformation at the speed it travels. We believe truth-checking should
                    be automatic, transparent, and accessible — not a manual afterthought.
                </motion.p>
            </motion.section>

            {/* ── Divider line ── */}
            <div className="max-w-3xl mx-auto mb-24 flex items-center gap-4">
                <div className="flex-1 h-px bg-white/5" />
                <span className="text-white/10 text-[10px] uppercase tracking-widest font-black">Core Pillars</span>
                <div className="flex-1 h-px bg-white/5" />
            </div>

            {/* ── Pillars grid ── */}
            <motion.section
                className="max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-24"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.15 }}
                variants={{ show: { transition: { staggerChildren: 0.1 } } }}
            >
                {PILLARS.map((p) => (
                    <motion.div
                        key={p.title}
                        variants={fade}
                        className="group glass-card border-white/5 bg-black/40 p-6 rounded-xl hover:border-orange-500/20 transition-all duration-300"
                    >
                        <div className="w-9 h-9 rounded-lg bg-orange-500/10 flex items-center justify-center mb-4 group-hover:bg-orange-500/20 transition-colors">
                            <p.icon size={17} className="text-orange-500" />
                        </div>
                        <h3 className="text-white font-black text-sm mb-2">{p.title}</h3>
                        <p className="text-white/40 text-xs leading-relaxed">{p.body}</p>
                    </motion.div>
                ))}
            </motion.section>

            {/* ── Mission statement ── */}
            <motion.section
                className="max-w-2xl mx-auto text-center"
                initial={{ opacity: 0, y: 32 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6 }}
            >
                <div className="glass-card border-white/5 bg-black/40 rounded-2xl px-10 py-12">
                    <p className="text-[10px] uppercase tracking-[0.3em] font-black text-orange-500 mb-5">
                        Our Mission
                    </p>
                    <blockquote className="text-white/70 text-lg font-light leading-relaxed italic">
                        "In a world where misinformation spreads faster than correction, we're building
                        the infrastructure to make truth-checking as effortless as reading."
                    </blockquote>
                    <div className="mt-8 flex items-center justify-center gap-3">
                        <div className="h-px w-12 bg-orange-500/40" />
                        <span className="text-orange-500/70 text-[10px] uppercase tracking-widest font-black">
                            ZeroTrust AI Team
                        </span>
                        <div className="h-px w-12 bg-orange-500/40" />
                    </div>
                </div>
            </motion.section>

            <Footer />
        </main>
    );
}
