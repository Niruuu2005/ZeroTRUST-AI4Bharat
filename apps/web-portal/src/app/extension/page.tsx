"use client";

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
    Chrome,
    ShieldCheck,
    Zap,
    Search,
    Shield,
    Globe
} from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import InstallModal from '@/components/ui/InstallModal';

export default function ExtensionPage() {
    const [modalOpen, setModalOpen] = useState(false);

    return (
        <main className="min-h-screen text-white selection:bg-orange-500/30">
            <InstallModal open={modalOpen} onClose={() => setModalOpen(false)} />
            <Navbar />

            {/* Hero Section — full-screen, uses global Hyperspeed background */}
            <section className="relative h-screen w-full flex items-center justify-center overflow-hidden">
                {/* Gradient overlay over the global Hyperspeed background */}
                <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/80 z-10" />

                {/* Content */}
                <div className="relative z-20 max-w-7xl mx-auto px-6 text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20 mb-8"
                    >
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                        <span className="text-[10px] uppercase font-black tracking-[0.2em] text-orange-500">
                            Now Available for Chrome &amp; Edge
                        </span>
                    </motion.div>

                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-5xl md:text-8xl font-black tracking-tighter leading-[0.9] mb-8"
                    >
                        THE TRUTH, <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-orange-500 to-red-600">IN EVERY BROWSER.</span>
                    </motion.h1>

                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="text-white/40 text-lg max-w-2xl mx-auto font-medium leading-relaxed mb-12"
                    >
                        Stop switching tabs. The ZeroTrust Browser Extension brings our 6-agent verification
                        engine directly into your social feeds, news sites, and research portals.
                    </motion.p>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className="flex flex-wrap justify-center gap-4"
                    >
                        <button onClick={() => setModalOpen(true)} className="relative group">
                            <div className="absolute -inset-1 bg-gradient-to-r from-orange-500 to-red-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300" />
                            <div className="relative flex items-center gap-3 bg-gradient-to-r from-orange-600 to-red-600 text-white font-black text-xs tracking-[0.2em] px-10 py-5 rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all">
                                <Chrome size={18} />
                                INSTALL FOR CHROME
                            </div>
                        </button>
                    </motion.div>
                </div>
            </section>

            {/* Visual Showcase (Mockup) */}
            <section className="relative z-10 py-24 px-6 bg-[#030303]">
                <div className="max-w-6xl mx-auto">
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                        <motion.div
                            initial={{ opacity: 0, x: -30 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            className="space-y-8"
                        >
                            <div className="space-y-4">
                                <h2 className="text-4xl font-black tracking-tighter">SURF WITH <span className="text-orange-500">NO DOUBTS.</span></h2>
                                <p className="text-white/40 font-medium leading-relaxed">
                                    Our extension sits quietly in your sidebar, scanning content in real-time.
                                    When you scroll past a questionable claim, ZeroTrust flags it automatically.
                                </p>
                            </div>

                            <div className="space-y-6">
                                {[
                                    { icon: Zap, title: "Contextual Analysis", desc: "Right-click any text block or image to verify it instantly without leaving the page." },
                                    { icon: Search, title: "Source Scraper", desc: "Automatically extracts and archives citations from news articles for deep analysis." },
                                    { icon: Shield, title: "Phishing Guard", desc: "Detects domain manipulation and fake news sites before you even click." }
                                ].map((item, i) => (
                                    <div key={i} className="flex gap-4">
                                        <div className="mt-1 w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center shrink-0">
                                            <item.icon size={16} className="text-orange-500" />
                                        </div>
                                        <div>
                                            <h4 className="text-sm font-black uppercase tracking-widest text-white/80">{item.title}</h4>
                                            <p className="text-xs text-white/30 font-medium mt-1 leading-relaxed">{item.desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            className="relative"
                        >
                            {/* Browser Mockup */}
                            <div className="relative rounded-3xl overflow-hidden border border-white/10 bg-black shadow-[0_0_100px_rgba(249,115,22,0.1)]">
                                <div className="px-4 py-3 bg-white/[0.05] border-b border-white/5 flex items-center gap-4">
                                    <div className="flex gap-1.5">
                                        <div className="w-2.5 h-2.5 rounded-full bg-red-500/30" />
                                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-400/30" />
                                        <div className="w-2.5 h-2.5 rounded-full bg-green-500/30" />
                                    </div>
                                    <div className="flex-1 h-6 bg-white/5 rounded-lg flex items-center px-4">
                                        <div className="text-[10px] text-white/20 font-bold uppercase tracking-widest">social.network/feed</div>
                                    </div>
                                </div>
                                <div className="p-8 aspect-video bg-black/40 relative">
                                    <div className="space-y-4">
                                        <div className="w-2/3 h-4 bg-white/5 rounded" />
                                        <div className="w-full h-24 bg-white/5 rounded-2xl" />
                                        <div className="w-1/2 h-4 bg-white/5 rounded" />
                                    </div>

                                    {/* Extension Overlay Mockup */}
                                    <motion.div
                                        initial={{ x: 50, opacity: 0 }}
                                        whileInView={{ x: 0, opacity: 1 }}
                                        transition={{ delay: 0.5 }}
                                        className="absolute top-12 right-6 w-48 glass-card border-orange-500/30 bg-black/90 p-4 shadow-[0_0_40px_rgba(249,115,22,0.2)]"
                                    >
                                        <div className="flex items-center gap-2 mb-3">
                                            <div className="w-6 h-6 rounded-md bg-orange-500 flex items-center justify-center">
                                                <ShieldCheck size={14} className="text-black" />
                                            </div>
                                            <span className="text-[9px] font-black uppercase tracking-wider text-white">Verdict</span>
                                        </div>
                                        <div className="text-[10px] font-bold text-orange-500 uppercase tracking-tighter mb-2 italic">Low Credibility</div>
                                        <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden mb-3">
                                            <div className="w-1/4 h-full bg-orange-500 animate-pulse" />
                                        </div>
                                        <div className="text-[8px] text-white/40 leading-tight">6 Agents suspect AI-generated manipulative content.</div>
                                    </motion.div>
                                </div>
                            </div>
                        </motion.div>
                    </div>
                </div>
            </section>

            {/* Final CTA Strip */}
            <section className="relative z-10 py-32 px-6 bg-[#030303] overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-[300px] bg-orange-500/5 blur-[150px] pointer-events-none" />
                <div className="max-w-4xl mx-auto text-center">
                    <h2 className="text-4xl md:text-6xl font-black tracking-tighter mb-8">READY TO <span className="text-orange-500">ARM YOUR BROWSER?</span></h2>
                    <div className="flex flex-wrap justify-center gap-6">
                        {[
                            { label: 'Chrome',  icon: <Chrome  className="text-white/20 group-hover:text-orange-500 transition-colors" /> },
                            { label: 'Edge',    icon: <Globe   className="text-white/20 group-hover:text-orange-500 transition-colors" /> },
                            { label: 'Brave',   icon: <Shield  className="text-white/20 group-hover:text-orange-500 transition-colors" /> },
                        ].map((browser) => (
                            <button key={browser.label} onClick={() => setModalOpen(true)} className="flex flex-col items-center gap-3">
                                <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center hover:border-orange-500/30 hover:bg-orange-500/5 transition-all group">
                                    {browser.icon}
                                </div>
                                <span className="text-[10px] font-black uppercase tracking-widest text-white/30">{browser.label}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </section>

            <Footer />
        </main>
    );
}
