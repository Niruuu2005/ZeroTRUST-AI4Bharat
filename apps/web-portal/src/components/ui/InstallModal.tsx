"use client";

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, FolderOpen, ToggleRight, PackagePlus, CheckCircle2 } from 'lucide-react';

const STEPS = [
    {
        icon: Download,
        title: 'Download the extension',
        body: 'Click the button below to download zerotrust-extension.zip to your computer.',
        highlight: true,
    },
    {
        icon: FolderOpen,
        title: 'Extract the ZIP',
        body: 'Unzip the downloaded file anywhere on your computer (e.g. Downloads/zerotrust-extension).',
    },
    {
        icon: ToggleRight,
        title: 'Enable Developer Mode',
        body: (
            <>
                Open{' '}
                <code className="px-1.5 py-0.5 rounded bg-white/10 text-orange-400 text-[11px]">
                    chrome://extensions
                </code>{' '}
                and toggle <strong className="text-white/80">Developer mode</strong> on (top-right corner).
            </>
        ),
    },
    {
        icon: PackagePlus,
        title: 'Load Unpacked',
        body: 'Click "Load unpacked" and select the extracted folder. The ZeroTrust icon will appear in your toolbar.',
    },
    {
        icon: CheckCircle2,
        title: 'All done!',
        body: 'Pin the extension, then click its icon or right-click any text to start verifying claims.',
    },
];

interface Props {
    open: boolean;
    onClose: () => void;
}

export default function InstallModal({ open, onClose }: Props) {
    // Close on Escape
    useEffect(() => {
        if (!open) return;
        const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [open, onClose]);

    return (
        <AnimatePresence>
            {open && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        key="backdrop"
                        className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                    />

                    {/* Panel */}
                    <motion.div
                        key="panel"
                        className="fixed z-[101] inset-0 flex items-center justify-center p-4"
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                    >
                        <div className="relative w-full max-w-lg bg-[#0e0e0e] border border-white/10 rounded-2xl shadow-[0_0_80px_rgba(249,115,22,0.12)] overflow-hidden">

                            {/* Header */}
                            <div className="flex items-center justify-between px-7 pt-7 pb-5 border-b border-white/5">
                                <div>
                                    <p className="text-[9px] uppercase tracking-[0.3em] font-black text-orange-500 mb-1">Chrome / Edge / Brave</p>
                                    <h2 className="text-lg font-black text-white leading-tight">Install ZeroTrust Extension</h2>
                                </div>
                                <button
                                    onClick={onClose}
                                    className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white transition-all"
                                >
                                    <X size={14} />
                                </button>
                            </div>

                            {/* Steps */}
                            <div className="px-7 py-6 space-y-5">
                                {STEPS.map((step, i) => (
                                    <div key={i} className="flex gap-4 items-start">
                                        <div className="shrink-0 w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                                            <step.icon size={15} className="text-orange-500" />
                                        </div>
                                        <div className="pt-0.5">
                                            <p className="text-white text-xs font-black mb-0.5">{step.title}</p>
                                            <p className="text-white/40 text-[11px] leading-relaxed">{step.body}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* CTA */}
                            <div className="px-7 pb-7">
                                <a
                                    href="/zerotrust-extension.zip"
                                    download="zerotrust-extension.zip"
                                    className="group relative flex items-center justify-center gap-3 w-full py-4 rounded-xl font-black text-xs tracking-[0.2em] uppercase text-white overflow-hidden"
                                >
                                    <div className="absolute inset-0 bg-gradient-to-r from-orange-600 to-red-600 transition-opacity group-hover:opacity-90" />
                                    <div className="absolute -inset-1 bg-gradient-to-r from-orange-500 to-red-600 blur opacity-20 group-hover:opacity-40 transition" />
                                    <Download size={15} className="relative z-10" />
                                    <span className="relative z-10">Download Extension ZIP</span>
                                </a>
                                <p className="text-center text-white/20 text-[10px] mt-3 leading-relaxed">
                                    Works on Chrome, Edge, and Brave — any Chromium-based browser.
                                </p>
                            </div>

                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
