"use client";

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

const SECTIONS = [
    {
        title: '1. Information We Collect',
        body: 'ZeroTrust AI does not store any queries, uploaded files, or verification results. All processing is ephemeral — data sent through the verification pipeline is used solely to produce your result and is discarded immediately afterward. We do not log IP addresses, create user profiles, or sell data to third parties.',
    },
    {
        title: '2. Browser Extension',
        body: 'The browser extension reads only the text you explicitly select and right-click to verify, or files you manually upload. It does not scan pages passively, track browsing history, or access any data beyond what you intentionally submit.',
    },
    {
        title: '3. Local Storage',
        body: 'The extension stores your API key and backend URL preference in Chrome\'s local storage (`chrome.storage.local`), which is sandboxed to your device and is never transmitted to our servers.',
    },
    {
        title: '4. Analytics',
        body: 'We do not use any third-party analytics, tracking pixels, or telemetry scripts. No cookies are set by this application.',
    },
    {
        title: '5. Changes to This Policy',
        body: 'We may update this policy as the product evolves. Material changes will be reflected in the Changelog. Continued use of ZeroTrust AI after any change constitutes acceptance of the revised policy.',
    },
    {
        title: '6. Contact',
        body: 'Questions about privacy? Reach us through the Contact page.',
    },
];

export default function PrivacyPage() {
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
                    className="text-center mb-14"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <p className="text-[10px] uppercase tracking-[0.3em] font-black text-orange-500 mb-4">Legal</p>
                    <h1 className="text-4xl font-black text-white mb-4">Privacy Policy</h1>
                    <p className="text-white/30 text-sm">Last updated: March 2026</p>
                </motion.div>

                <div className="space-y-6">
                    {SECTIONS.map((s, i) => (
                        <motion.div
                            key={s.title}
                            className="glass-card border-white/5 bg-black/40 rounded-xl px-7 py-6"
                            initial={{ opacity: 0, y: 12 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.06 }}
                        >
                            <h2 className="text-white font-black text-sm mb-3">{s.title}</h2>
                            <p className="text-white/40 text-sm leading-relaxed">{s.body}</p>
                        </motion.div>
                    ))}
                </div>

                <motion.div
                    className="text-center mt-12"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                >
                    <Link href="/contact" className="text-orange-500 hover:text-orange-400 text-xs font-black uppercase tracking-widest transition-colors">
                        Contact Us →
                    </Link>
                </motion.div>

            </div>
            <Footer />
        </main>
    );
}
