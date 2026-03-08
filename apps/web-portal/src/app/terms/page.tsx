"use client";

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

const SECTIONS = [
    {
        title: '1. Acceptance of Terms',
        body: 'By accessing or using ZeroTrust AI (the "Service"), you agree to be bound by these Terms of Service. If you do not agree, do not use the Service.',
    },
    {
        title: '2. Use of the Service',
        body: 'ZeroTrust AI is provided for lawful fact-verification purposes only. You may not use the Service to verify content with the intent to harass, defame, or harm any individual or group. Automated bulk abuse of the public API without prior written permission is prohibited.',
    },
    {
        title: '3. Accuracy Disclaimer',
        body: 'ZeroTrust AI uses AI-powered analysis and produces probabilistic verdicts. Results should be treated as one input in an editorial or research workflow — not as definitive legal or journalistic proof. We make no warranty of accuracy or fitness for a particular purpose.',
    },
    {
        title: '4. Intellectual Property',
        body: 'The ZeroTrust AI platform, branding, and source code are the intellectual property of the AI4BHARAT Zero Trust Initiative. You may not copy, redistribute, or create derivative works without explicit written consent.',
    },
    {
        title: '5. Limitation of Liability',
        body: 'To the fullest extent permitted by law, ZeroTrust AI and its contributors shall not be liable for any indirect, incidental, or consequential damages arising from your use of or reliance on the Service.',
    },
    {
        title: '6. Modifications',
        body: 'We reserve the right to update these Terms at any time. Continued use of the Service after changes constitutes acceptance. Material changes will be noted in the Changelog.',
    },
];

export default function TermsPage() {
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
                    <h1 className="text-4xl font-black text-white mb-4">Terms of Service</h1>
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

            </div>
            <Footer />
        </main>
    );
}
