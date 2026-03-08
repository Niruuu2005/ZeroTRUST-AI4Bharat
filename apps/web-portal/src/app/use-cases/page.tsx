"use client";

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Newspaper, FlaskConical, MessagesSquare, Building2, ArrowRight, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

const CASES = [
    {
        id: 'journalists',
        icon: Newspaper,
        color: 'orange',
        title: 'Journalists',
        tagline: 'Publish with confidence.',
        body: 'Before a story goes live, run every cited claim through the 6-agent pipeline. Get source credibility scores, bias flags, and full evidence trails in seconds — not hours of manual fact-checking.',
        bullets: [
            'Cross-reference claims against 50+ live news archives',
            'Auto-detect doctored images and deepfaked video sources',
            'Export a verifiable evidence report for editorial review',
        ],
    },
    {
        id: 'researchers',
        icon: FlaskConical,
        color: 'cyan',
        title: 'Researchers',
        tagline: 'Source credibility at scale.',
        body: "Verify the credibility of papers, preprints, and cited studies automatically. The Source Credibility Agent cross-references PubMed, arXiv, and domain authority scores so you don't have to.",
        bullets: [
            'Academic database cross-referencing in real time',
            'Retraction and predatory journal detection',
            'Structured JSON export for programmatic access',
        ],
    },
    {
        id: 'social',
        icon: MessagesSquare,
        color: 'purple',
        title: 'Social Media Users',
        tagline: "Don't share without knowing.",
        body: 'Right-click any post, headline, or image in your browser and get a verdict in under 3 seconds — without switching tabs. The browser extension brings ZeroTrust directly to your feed.',
        bullets: [
            'One-click verification via browser extension',
            'Real-time flagging of viral misinformation',
            'Works on Twitter/X, Facebook, Reddit, and more',
        ],
    },
    {
        id: 'enterprise',
        icon: Building2,
        color: 'amber',
        title: 'Enterprises',
        tagline: 'Protect your brand reputation.',
        body: 'Monitor news mentions, detect coordinated disinformation campaigns targeting your brand, and integrate verification into your existing content moderation workflows via the REST API.',
        bullets: [
            'REST API with Bearer auth for pipeline integration',
            'Bulk verification for content moderation at scale',
            'Audit logs and compliance-ready evidence exports',
        ],
    },
];

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; bullet: string }> = {
    orange: { bg: 'bg-orange-500/10', border: 'border-orange-500/20', text: 'text-orange-500', bullet: 'bg-orange-500' },
    cyan:   { bg: 'bg-cyan-500/10',   border: 'border-cyan-500/20',   text: 'text-cyan-400',   bullet: 'bg-cyan-400'   },
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/20', text: 'text-purple-400', bullet: 'bg-purple-400' },
    amber:  { bg: 'bg-amber-500/10',  border: 'border-amber-500/20',  text: 'text-amber-400',  bullet: 'bg-amber-400'  },
};

const fade = { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } };

export default function UseCasesPage() {
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

            <motion.section
                className="max-w-3xl mx-auto text-center mb-20"
                initial="hidden"
                animate="show"
                variants={{ show: { transition: { staggerChildren: 0.1 } } }}
            >
                <motion.p variants={fade} className="text-[10px] uppercase tracking-[0.3em] font-black text-orange-500 mb-4">
                    Use Cases
                </motion.p>
                <motion.h1 variants={fade} className="text-4xl md:text-5xl font-black text-white leading-tight mb-6">
                    Built for{' '}
                    <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                        every workflow
                    </span>
                </motion.h1>
                <motion.p variants={fade} className="text-white/40 text-base leading-relaxed">
                    Whether you're breaking news, publishing research, scrolling your feed, or protecting a brand — ZeroTrust AI fits into how you already work.
                </motion.p>
            </motion.section>

            <div className="max-w-4xl mx-auto space-y-8">
                {CASES.map((c, i) => {
                    const col = COLOR_MAP[c.color];
                    return (
                        <motion.div
                            key={c.id}
                            id={c.id}
                            className={`glass-card border bg-black/40 rounded-2xl p-8 md:p-10 ${col.border}`}
                            initial={{ opacity: 0, x: i % 2 === 0 ? -24 : 24 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5 }}
                        >
                            <div className="md:flex gap-8 items-start">
                                <div className={`shrink-0 w-12 h-12 rounded-2xl ${col.bg} border ${col.border} flex items-center justify-center mb-5 md:mb-0`}>
                                    <c.icon size={22} className={col.text} />
                                </div>
                                <div className="flex-1">
                                    <p className={`text-[10px] uppercase tracking-[0.25em] font-black mb-1 ${col.text}`}>{c.tagline}</p>
                                    <h2 className="text-2xl font-black text-white mb-3">{c.title}</h2>
                                    <p className="text-white/40 text-sm leading-relaxed mb-5">{c.body}</p>
                                    <ul className="space-y-2">
                                        {c.bullets.map((b) => (
                                            <li key={b} className="flex items-start gap-2.5 text-xs text-white/50">
                                                <span className={`shrink-0 mt-1.5 w-1.5 h-1.5 rounded-full ${col.bullet}`} />
                                                {b}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            <motion.div
                className="max-w-xl mx-auto text-center mt-16"
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true }}
            >
                <Link
                    href="/"
                    className="inline-flex items-center gap-3 bg-gradient-to-r from-orange-600 to-red-600 text-white font-black text-xs tracking-[0.2em] uppercase px-10 py-4 rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all"
                >
                    Start Verifying <ArrowRight size={15} />
                </Link>
            </motion.div>

            <Footer />
        </main>
    );
}
