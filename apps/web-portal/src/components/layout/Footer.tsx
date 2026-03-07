"use client";

import Image from 'next/image';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Github, Twitter, Globe, Mail, ArrowUpRight } from 'lucide-react';

const NAV_COLUMNS = [
    {
        heading: 'Product',
        links: [
            { label: 'How It Works',    href: '/how-it-works' },
            { label: 'Agent Network',   href: '/#agents'      },
            { label: 'Live Demo',       href: '/demo'         },
            { label: 'Browser Extension', href: '/extension'  },
        ],
    },
    {
        heading: 'Use Cases',
        links: [
            { label: 'Journalists',  href: '/use-cases#journalists' },
            { label: 'Researchers',  href: '/use-cases#researchers' },
            { label: 'Social Media', href: '/use-cases#social'      },
            { label: 'Enterprises',  href: '/use-cases#enterprise'  },
        ],
    },
    {
        heading: 'Resources',
        links: [
            { label: 'Documentation',  href: '/docs'        },
            { label: 'API Reference',  href: '/docs/api'    },
            { label: 'Research Paper', href: '/research'    },
            { label: 'Changelog',      href: '/changelog'   },
        ],
    },
];

// TODO: replace '#' with real URLs when accounts are available
const SOCIALS = [
    { icon: Github,  href: 'https://github.com/AI4BHARAT', label: 'GitHub'  },
    { icon: Twitter, href: '#',                             label: 'Twitter' },
    { icon: Globe,   href: '/',                             label: 'Website' },
    { icon: Mail,    href: 'mailto:contact@zerotrust.ai',   label: 'Email'   },
];

export default function Footer() {
    return (
        <footer className="relative bg-[#030303] border-t border-white/[0.06] overflow-hidden">

            {/* Subtle background glow */}
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-orange-500/5 blur-[180px] pointer-events-none" />

            <div className="relative z-10 max-w-7xl mx-auto px-6">

                {/* ── Top strip: brand + socials ── */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8 py-16 border-b border-white/[0.05]"
                >
                    {/* Brand */}
                    <div className="flex items-center gap-3">
                        <div className="relative w-10 h-10 shrink-0">
                            <Image
                                src="/logo-transparent.png"
                                alt="ZeroTrust Logo"
                                width={80}
                                height={80}
                                quality={90}
                                className="object-contain w-full h-full drop-shadow-[0_0_8px_rgba(249,115,22,0.4)]"
                            />
                        </div>
                        <div>
                            <div className="text-base font-black tracking-tight text-white leading-none">
                                Zero<span className="text-orange-500">Trust</span>{' '}
                                <span className="text-white/60">AI</span>
                            </div>
                            <div className="text-[9px] uppercase tracking-[0.2em] font-bold text-white/20 mt-0.5">
                                Multi-Agent Verification Hub
                            </div>
                        </div>
                    </div>

                    {/* Social icons */}
                    <div className="flex items-center gap-2">
                        {SOCIALS.map((s) => (
                            <Link
                                key={s.label}
                                href={s.href}
                                aria-label={s.label}
                                className="w-9 h-9 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-white/30 hover:text-orange-400 hover:border-orange-500/30 hover:bg-orange-500/5 transition-all duration-300"
                            >
                                <s.icon size={15} />
                            </Link>
                        ))}
                    </div>
                </motion.div>

                {/* ── Middle: nav columns ── */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.1 }}
                    className="grid grid-cols-2 md:grid-cols-3 gap-12 py-14 border-b border-white/[0.05]"
                >
                    {NAV_COLUMNS.map((col) => (
                        <div key={col.heading}>
                            <h4 className="text-[9px] uppercase font-black tracking-[0.22em] text-white/25 mb-5">
                                {col.heading}
                            </h4>
                            <ul className="space-y-3">
                                {col.links.map((link) => (
                                    <li key={link.label}>
                                        <Link
                                            href={link.href}
                                            className="group inline-flex items-center gap-1 text-sm font-medium text-white/40 hover:text-white transition-colors duration-200"
                                        >
                                            {link.label}
                                            <ArrowUpRight
                                                size={11}
                                                className="opacity-0 -translate-y-0.5 translate-x-0 group-hover:opacity-100 group-hover:-translate-y-1 group-hover:translate-x-0.5 transition-all duration-200 text-orange-500"
                                            />
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </motion.div>

                {/* ── Bottom: legal bar ── */}
                <motion.div
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className="flex flex-col md:flex-row items-center justify-between gap-4 py-8 text-[10px] uppercase tracking-[0.18em] font-bold text-white/15"
                >
                    <span>&copy; 2026 AI4BHARAT Zero Trust Initiative. All rights reserved.</span>
                    <div className="flex items-center gap-6">
                        <Link href="/privacy" className="hover:text-white/40 transition-colors">Privacy</Link>
                        <Link href="/terms"   className="hover:text-white/40 transition-colors">Terms</Link>
                        <Link href="/contact" className="hover:text-white/40 transition-colors">Contact</Link>
                    </div>
                </motion.div>

            </div>
        </footer>
    );
}
