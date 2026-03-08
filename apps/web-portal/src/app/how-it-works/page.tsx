"use client";

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Inbox, Network, Gavel, CheckCircle2, ArrowRight, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

const STEPS = [
    {
        number: '01',
        icon: Inbox,
        title: 'Submit Your Claim',
        body: 'Paste an article URL, raw text, social post, or upload an image, video, or audio clip. ZeroTrust AI accepts any format through the web app or browser extension.',
    },
    {
        number: '02',
        icon: Network,
        title: 'Six Agents Mobilise',
        body: 'The Orchestrator Agent splits the claim and dispatches it simultaneously to five specialist agents — Fact Verifier, Deepfake Detector, Bias Analyser, Source Credibility, and Consensus Engine — each running in parallel.',
    },
    {
        number: '03',
        icon: CheckCircle2,
        title: 'Independent Analysis',
        body: 'Each agent independently queries live news archives, academic databases, social feeds, and structured knowledge graphs. No agent can see another\'s interim result, preventing groupthink.',
    },
    {
        number: '04',
        icon: Gavel,
        title: 'Consensus Verdict',
        body: 'The Consensus Engine weighs each agent\'s verdict using a trust-weighted voting model. The final credibility score (0–100) and category are generated along with a full evidence report.',
    },
];

const METRICS = [
    { value: '6', label: 'Specialist Agents' },
    { value: '<3s', label: 'Average Latency' },
    { value: '50+', label: 'Sources Per Query' },
    { value: '94%', label: 'Consensus Accuracy' },
];

const fade = { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } };

export default function HowItWorksPage() {
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
            </div>

            {/* Hero */}
            <motion.section
                className="max-w-3xl mx-auto text-center mb-20"
                initial="hidden"
                animate="show"
                variants={{ show: { transition: { staggerChildren: 0.1 } } }}
            >
                <motion.p variants={fade} className="text-[10px] uppercase tracking-[0.3em] font-black text-orange-500 mb-4">
                    How It Works
                </motion.p>
                <motion.h1 variants={fade} className="text-4xl md:text-5xl font-black text-white leading-tight mb-6">
                    Six minds.{' '}
                    <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                        One verdict.
                    </span>
                </motion.h1>
                <motion.p variants={fade} className="text-white/40 text-base leading-relaxed">
                    A zero-trust pipeline means no single agent is trusted unconditionally.
                    Every verdict is a consensus — built on parallel, independent analysis.
                </motion.p>
            </motion.section>

            {/* Metrics strip */}
            <motion.section
                className="max-w-3xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-4 mb-20"
                initial="hidden"
                whileInView="show"
                viewport={{ once: true }}
                variants={{ show: { transition: { staggerChildren: 0.08 } } }}
            >
                {METRICS.map((m) => (
                    <motion.div
                        key={m.label}
                        variants={fade}
                        className="glass-card border-white/5 bg-black/40 rounded-xl p-5 text-center"
                    >
                        <p className="text-3xl font-black text-orange-500 mb-1">{m.value}</p>
                        <p className="text-white/30 text-[10px] uppercase tracking-widest font-black">{m.label}</p>
                    </motion.div>
                ))}
            </motion.section>

            {/* Steps */}
            <section className="max-w-3xl mx-auto mb-20">
                <div className="relative">
                    {/* Vertical connector */}
                    <div className="absolute left-[19px] top-10 bottom-10 w-px bg-white/5 hidden md:block" />

                    <div className="space-y-10">
                        {STEPS.map((step, i) => (
                            <motion.div
                                key={step.number}
                                className="flex gap-6"
                                initial={{ opacity: 0, x: -24 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                            >
                                {/* Number bubble */}
                                <div className="shrink-0 w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center font-black text-orange-500 text-xs z-10">
                                    {step.number}
                                </div>
                                <div className="pt-1.5">
                                    <div className="flex items-center gap-2 mb-2">
                                        <step.icon size={14} className="text-orange-500/70" />
                                        <h3 className="text-white font-black text-sm">{step.title}</h3>
                                    </div>
                                    <p className="text-white/40 text-sm leading-relaxed">{step.body}</p>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA */}
            <motion.section
                className="max-w-xl mx-auto text-center"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
            >
                <Link
                    href="/"
                    className="inline-flex items-center gap-3 bg-gradient-to-r from-orange-600 to-red-600 text-white font-black text-xs tracking-[0.2em] uppercase px-10 py-4 rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all"
                >
                    Try It Now <ArrowRight size={15} />
                </Link>
            </motion.section>

            <Footer />
        </main>
    );
}
