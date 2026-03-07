"use client";

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

const ENTRIES = [
    {
        version: 'v0.3.0',
        date: 'March 2026',
        tag: 'Latest',
        changes: [
            { type: 'new',  text: 'Image / video / audio upload with drag-and-drop and inline preview' },
            { type: 'new',  text: 'Share Report (clipboard) and Download JSON on verify page' },
            { type: 'new',  text: 'About page, Use Cases, How It Works, and API Reference pages' },
            { type: 'new',  text: 'Browser extension installer modal with step-by-step guide' },
            { type: 'fix',  text: 'Hyperspeed WebGL context no longer resets on page navigation' },
            { type: 'fix',  text: 'Footer nav links now route to real pages' },
        ],
    },
    {
        version: 'v0.2.0',
        date: 'February 2026',
        tag: null,
        changes: [
            { type: 'new',  text: 'Chrome MV3 browser extension (popup, sidebar, content script)' },
            { type: 'new',  text: 'Extension icons generated from project logo' },
            { type: 'new',  text: 'Backend URL configurable from extension settings popup' },
            { type: 'new',  text: 'Real backend integration with demo fallback on /verify' },
        ],
    },
    {
        version: 'v0.1.0',
        date: 'January 2026',
        tag: null,
        changes: [
            { type: 'new',  text: 'Initial frontend: Hero, AgentsSection, Verify page, Extension marketing page' },
            { type: 'new',  text: 'Page transitions with Framer Motion AnimatePresence' },
            { type: 'new',  text: 'HyperspeedBackground persistent global WebGL layer' },
            { type: 'new',  text: 'Navbar with active-route detection' },
        ],
    },
];

const TYPE_STYLE: Record<string, string> = {
    new:  'bg-orange-500/10 text-orange-400',
    fix:  'bg-green-500/10  text-green-400',
    break:'bg-red-500/10    text-red-400',
};

export default function ChangelogPage() {
    const router = useRouter();

    return (
        <main className="min-h-screen pt-28 px-6 bg-[#030303]">
            <Navbar />
            <div className="max-w-2xl mx-auto">

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
                    <p className="text-[10px] uppercase tracking-[0.3em] font-black text-orange-500 mb-4">Changelog</p>
                    <h1 className="text-4xl font-black text-white mb-4">
                        What&apos;s{' '}
                        <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                            New
                        </span>
                    </h1>
                    <p className="text-white/40 text-sm">Every release, documented.</p>
                </motion.div>

                <div className="space-y-10">
                    {ENTRIES.map((entry, i) => (
                        <motion.div
                            key={entry.version}
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <h2 className="text-white font-black text-lg">{entry.version}</h2>
                                {entry.tag && (
                                    <span className="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md bg-orange-500/10 text-orange-500">
                                        {entry.tag}
                                    </span>
                                )}
                                <span className="text-white/20 text-xs ml-auto">{entry.date}</span>
                            </div>
                            <div className="glass-card border-white/5 bg-black/40 rounded-xl overflow-hidden divide-y divide-white/[0.04]">
                                {entry.changes.map((c, j) => (
                                    <div key={j} className="flex items-start gap-3 px-5 py-3.5">
                                        <span className={`shrink-0 text-[9px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded mt-0.5 ${TYPE_STYLE[c.type]}`}>
                                            {c.type}
                                        </span>
                                        <p className="text-white/50 text-xs leading-relaxed">{c.text}</p>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    ))}
                </div>

            </div>
            <Footer />
        </main>
    );
}
