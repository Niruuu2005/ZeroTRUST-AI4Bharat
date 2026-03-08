"use client";

import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search, Sparkles, ArrowRight, FileText, Image as ImageIcon,
    Video, Mic, Link as LinkIcon, Upload, Globe, Twitter, Youtube, X
} from 'lucide-react';
import { fileStore } from '@/lib/fileStore';

/* ─────────────────────────────────────────────
   Typing Badge – cycles through capability labels
───────────────────────────────────────────── */
const LABELS = [
    'Deepfake Detection',
    'Fact Verification',
    'Bias Analysis',
    'Source Credibility',
    'Misinformation Sweep',
];

function TypingBadge() {
    const [labelIndex, setLabelIndex] = useState(0);
    const [displayed, setDisplayed] = useState('');
    const [phase, setPhase] = useState<'typing' | 'pause' | 'erasing'>('typing');
    const charRef = useRef(0);

    useEffect(() => {
        const target = LABELS[labelIndex];

        if (phase === 'typing') {
            if (charRef.current < target.length) {
                const t = setTimeout(() => {
                    charRef.current += 1;
                    setDisplayed(target.slice(0, charRef.current));
                }, 55);
                return () => clearTimeout(t);
            } else {
                const t = setTimeout(() => setPhase('pause'), 1800);
                return () => clearTimeout(t);
            }
        }

        if (phase === 'pause') {
            const t = setTimeout(() => setPhase('erasing'), 400);
            return () => clearTimeout(t);
        }

        if (phase === 'erasing') {
            if (charRef.current > 0) {
                const t = setTimeout(() => {
                    charRef.current -= 1;
                    setDisplayed(target.slice(0, charRef.current));
                }, 30);
                return () => clearTimeout(t);
            } else {
                setLabelIndex((i) => (i + 1) % LABELS.length);
                setPhase('typing');
            }
        }
    }, [phase, displayed, labelIndex]);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            className="mb-8 flex items-center gap-2 px-5 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20 backdrop-blur-md"
        >
            <Sparkles size={13} className="text-orange-500 shrink-0" />
            <span className="text-[10px] uppercase font-black tracking-[0.2em] text-orange-500/90 min-w-[180px] text-left">
                {displayed}
                <span className="animate-pulse text-orange-500">|</span>
            </span>
        </motion.div>
    );
}

/* ─────────────────────────────────────────────
   Hero
───────────────────────────────────────────── */
type InputMode = 'text' | 'image' | 'video' | 'audio';

export default function Hero() {
    const router = useRouter();
    const [mode, setMode] = useState<InputMode>('text');
    const [source, setSource] = useState('web');
    const [inputValue, setInputValue] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [filePreviewUrl, setFilePreviewUrl] = useState<string | null>(null);
    const [dragOver, setDragOver] = useState(false);
    const [fileError, setFileError] = useState<string | null>(null);

    // Clear file state whenever the user switches modes
    useEffect(() => {
        if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl);
        setSelectedFile(null);
        setFilePreviewUrl(null);
        setFileError(null);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mode]);

    const ACCEPT: Record<InputMode, string> = {
        text: '', image: 'image/*', video: 'video/*', audio: 'audio/*',
    };

    const handleFileSelect = (file: File) => {
        setFileError(null);
        if (file.size > 10 * 1024 * 1024) {
            setFileError('File exceeds the 10 MB limit. Please choose a smaller file.');
            return;
        }
        setSelectedFile(file);
        setFilePreviewUrl(URL.createObjectURL(file));
    };

    const clearFile = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl);
        setSelectedFile(null);
        setFilePreviewUrl(null);
        setFileError(null);
    };

    const handleVerify = () => {
        if (mode === 'text') {
            if (!inputValue.trim()) return;
            const params = new URLSearchParams({ q: inputValue, mode, source });
            router.push(`/verify?${params.toString()}`);
        } else {
            if (!selectedFile) return;
            fileStore.set({ file: selectedFile, mode, source });
            const params = new URLSearchParams({ mode, source, fileVerify: '1', fileName: selectedFile.name });
            router.push(`/verify?${params.toString()}`);
        }
    };

    const modes = [
        { id: 'text', icon: FileText, label: 'Text/Link' },
        { id: 'image', icon: ImageIcon, label: 'Image' },
        { id: 'video', icon: Video, label: 'Video' },
        { id: 'audio', icon: Mic, label: 'Audio' },
    ];

    const sources = [
        { id: 'web', icon: Globe, label: 'Web' },
        { id: 'twitter', icon: Twitter, label: 'X/Twitter' },
        { id: 'youtube', icon: Youtube, label: 'YouTube' },
    ];

    return (
        <section className="relative h-screen w-full flex items-center justify-center overflow-hidden">
            {/* Gradient Overlay over the global Hyperspeed background */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/80 z-10" />

            {/* Content */}
            <div className="relative z-20 flex flex-col items-center text-center px-4 max-w-5xl">

                {/* Typing Badge */}
                <TypingBadge />

                {/* Headline */}
                <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.2 }}
                    className="text-5xl md:text-7xl font-black tracking-tight text-white mb-10 leading-[0.95]"
                >
                    Verify the world with <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-orange-500 to-red-600">
                        Absolute Certainty.
                    </span>
                </motion.h1>

                {/* Verification Center UI */}
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.4 }}
                    className="w-full max-w-3xl relative"
                >
                    <div className="glass-card border-white/5 bg-black/60 p-1 shadow-[0_0_80px_rgba(249,115,22,0.15)] rounded-[2.5rem] overflow-hidden">

                        {/* Header: Mode Switcher */}
                        <div className="flex items-center justify-between px-6 py-3 border-b border-white/5">
                            <div className="flex gap-4">
                                {modes.map((m) => (
                                    <button
                                        key={m.id}
                                        onClick={() => setMode(m.id as InputMode)}
                                        className={`flex items-center gap-2 text-[10px] uppercase font-black tracking-widest transition-all duration-300 px-3 py-1.5 rounded-full ${mode === m.id
                                            ? 'text-orange-500 bg-orange-500/10 border border-orange-500/20'
                                            : 'text-white/30 hover:text-white/60'
                                            }`}
                                    >
                                        <m.icon size={12} />
                                        {m.label}
                                    </button>
                                ))}
                            </div>

                            {/* Source Indicator */}
                            <div className="hidden md:flex items-center gap-3">
                                <span className="text-[9px] uppercase font-bold text-white/20 tracking-tighter">Source Content:</span>
                                <div className="flex bg-white/5 p-1 rounded-lg border border-white/5">
                                    {sources.map((s) => (
                                        <button
                                            key={s.id}
                                            onClick={() => setSource(s.id)}
                                            className={`p-1.5 rounded-md transition-all ${source === s.id ? 'bg-orange-500 text-white' : 'text-white/20 hover:text-white/50'
                                                }`}
                                            title={s.label}
                                        >
                                            <s.icon size={12} />
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Middle: Dynamic Input Area */}
                        <div className="px-6 pt-6 pb-4 text-left">
                            <AnimatePresence mode="wait">
                                {mode === 'text' ? (
                                    <motion.div
                                        key="text"
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 10 }}
                                        className="relative group"
                                    >
                                        <div className="flex items-start gap-4">
                                            <div className="w-10 h-10 rounded-xl bg-orange-500/20 border border-orange-500/30 flex items-center justify-center shrink-0">
                                                <LinkIcon size={18} className="text-orange-500" />
                                            </div>
                                            <div className="flex-1">
                                                <textarea
                                                    placeholder="Paste an article link, X/Twitter URL, or document text here..."
                                                    className="w-full bg-transparent border-none outline-none text-lg text-white font-medium placeholder:text-white/10 resize-none min-h-[80px]"
                                                    value={inputValue}
                                                    onChange={(e) => setInputValue(e.target.value)}
                                                />
                                            </div>
                                        </div>
                                    </motion.div>
                                ) : (
                                    <motion.div
                                        key="media"
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: 10 }}
                                    >
                                        {/* Hidden file input */}
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            hidden
                                            accept={ACCEPT[mode]}
                                            onChange={(e) => {
                                                const f = e.target.files?.[0];
                                                if (f) handleFileSelect(f);
                                                e.target.value = '';
                                            }}
                                        />

                                        {selectedFile && filePreviewUrl ? (
                                            /* ── Inline preview ── */
                                            <div className="rounded-2xl overflow-hidden border border-white/10 bg-black/40">
                                                {mode === 'image' && (
                                                    <img
                                                        src={filePreviewUrl}
                                                        alt="Preview"
                                                        className="w-full max-h-48 object-contain bg-black/60"
                                                    />
                                                )}
                                                {mode === 'video' && (
                                                    <video
                                                        src={filePreviewUrl}
                                                        controls
                                                        className="w-full max-h-48 bg-black"
                                                    />
                                                )}
                                                {mode === 'audio' && (
                                                    <div className="flex flex-col items-center gap-4 p-6">
                                                        <div className="w-14 h-14 rounded-2xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                                                            <Mic size={24} className="text-orange-500" />
                                                        </div>
                                                        <audio src={filePreviewUrl} controls className="w-full" />
                                                    </div>
                                                )}
                                                {/* File info bar */}
                                                <div className="flex items-center justify-between px-4 py-2.5 bg-black/70 border-t border-white/5">
                                                    <div className="min-w-0">
                                                        <p className="text-white/70 text-xs font-bold truncate max-w-[220px]">{selectedFile.name}</p>
                                                        <p className="text-white/30 text-[10px]">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                                                    </div>
                                                    <button
                                                        onClick={clearFile}
                                                        className="ml-4 shrink-0 w-7 h-7 rounded-lg bg-white/10 hover:bg-red-500/20 flex items-center justify-center text-white/40 hover:text-red-400 transition-all"
                                                    >
                                                        <X size={12} />
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            /* ── Drop zone ── */
                                            <div
                                                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                                                onDragLeave={() => setDragOver(false)}
                                                onDrop={(e) => {
                                                    e.preventDefault();
                                                    setDragOver(false);
                                                    const file = e.dataTransfer.files[0];
                                                    if (file) handleFileSelect(file);
                                                }}
                                                onClick={() => fileInputRef.current?.click()}
                                                className={`flex flex-col items-center justify-center py-8 border-2 border-dashed rounded-3xl transition-all cursor-pointer group ${
                                                    dragOver
                                                        ? 'border-orange-500/40 bg-orange-500/5'
                                                        : 'border-white/5 bg-white/[0.02] hover:bg-white/[0.04] hover:border-white/10'
                                                }`}
                                            >
                                                <Upload
                                                    size={32}
                                                    className={`mb-3 transition-colors ${
                                                        dragOver ? 'text-orange-500' : 'text-white/20 group-hover:text-orange-500'
                                                    }`}
                                                />
                                                <p className={`text-sm font-bold transition-colors ${
                                                    dragOver ? 'text-white/70' : 'text-white/40 group-hover:text-white/60'
                                                }`}>
                                                    {dragOver ? 'Drop file here' : 'Click to upload or drag & drop'}
                                                </p>
                                                <p className="text-[10px] uppercase tracking-widest text-white/10 mt-1">
                                                    {mode} · Max 10 MB
                                                </p>
                                            </div>
                                        )}

                                        {fileError && (
                                            <p className="mt-2 text-xs text-red-400 font-medium text-center">{fileError}</p>
                                        )}
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>

                        {/* Footer: Action Bar */}
                        <div className="px-6 pb-6 flex items-center justify-end">
                            <button
                                onClick={handleVerify}
                                disabled={mode !== 'text' && !selectedFile}
                                className="relative group disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                                <div className="absolute -inset-1 bg-gradient-to-r from-orange-500 to-red-600 rounded-2xl blur opacity-30 group-hover:opacity-60 transition duration-300" />
                                <div className="relative flex items-center gap-3 bg-gradient-to-r from-orange-600 to-red-600 text-white font-black text-xs tracking-[0.2em] px-10 py-4 rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all">
                                    VERIFY SOURCE
                                    <ArrowRight size={16} />
                                </div>
                            </button>
                        </div>
                    </div>
                </motion.div>

            </div>
        </section>
    );
}
