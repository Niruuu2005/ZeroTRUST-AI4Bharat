"use client";

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Github, Twitter, Mail, MessageSquare, ArrowLeft } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

const CHANNELS = [
    {
        icon: Github,
        label: 'GitHub',
        desc: 'Browse source code, file issues, and submit pull requests.',
        action: 'View Repository',
        href: 'https://github.com/AI4BHARAT',
    },
    {
        icon: Twitter,
        label: 'X / Twitter',
        desc: 'Follow for updates, research previews, and announcements.',
        action: 'Follow @ZeroTrustAI',
        href: '#',
    },
    {
        icon: Mail,
        label: 'Email',
        desc: 'For partnerships, research collaboration, or press inquiries.',
        action: 'Send an Email',
        href: 'mailto:contact@zerotrust.ai',
    },
    {
        icon: MessageSquare,
        label: 'Discussions',
        desc: 'Join the community conversation on GitHub Discussions.',
        action: 'Open Discussions',
        href: 'https://github.com/AI4BHARAT',
    },
];

export default function ContactPage() {
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
                    <p className="text-[10px] uppercase tracking-[0.3em] font-black text-orange-500 mb-4">Contact</p>
                    <h1 className="text-4xl font-black text-white mb-6">
                        Get in{' '}
                        <span className="bg-gradient-to-r from-orange-500 to-red-500 bg-clip-text text-transparent">
                            Touch
                        </span>
                    </h1>
                    <p className="text-white/40 text-base leading-relaxed max-w-xl mx-auto">
                        We&apos;re a small research team. The fastest route to a response is GitHub Issues or Discussions.
                    </p>
                </motion.div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    {CHANNELS.map((c, i) => (
                        <motion.a
                            key={c.label}
                            href={c.href}
                            target={c.href.startsWith('http') ? '_blank' : undefined}
                            rel="noopener noreferrer"
                            className="group glass-card border-white/5 bg-black/40 hover:border-orange-500/20 rounded-2xl p-6 transition-all"
                            initial={{ opacity: 0, y: 16 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.08 }}
                        >
                            <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center mb-4 group-hover:bg-orange-500/20 transition-colors">
                                <c.icon size={18} className="text-orange-500" />
                            </div>
                            <h3 className="text-white font-black text-sm mb-1.5">{c.label}</h3>
                            <p className="text-white/35 text-xs leading-relaxed mb-4">{c.desc}</p>
                            <span className="text-orange-500 text-[10px] font-black uppercase tracking-widest group-hover:underline">
                                {c.action} →
                            </span>
                        </motion.a>
                    ))}
                </div>

            </div>
            <Footer />
        </main>
    );
}
