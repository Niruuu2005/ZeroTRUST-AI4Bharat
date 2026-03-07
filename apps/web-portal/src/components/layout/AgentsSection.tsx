"use client";

import { useRef, useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    BrainCircuit,
    ScanSearch,
    ShieldAlert,
    Scale,
    BadgeCheck,
    GitMerge,
} from 'lucide-react';

/* ─────────────────────────────────────────────
   Agent definitions
───────────────────────────────────────────── */
const AGENTS = [
    {
        id: '01',
        name: 'Orchestrator',
        role: 'Mission Control',
        desc: 'Routes incoming content to specialist agents, monitors progress, and manages the verification pipeline end-to-end.',
        icon: BrainCircuit,
        color: 'orange',
        glow: 'rgba(249,115,22,0.25)',
    },
    {
        id: '02',
        name: 'Fact Verifier',
        role: 'Truth Engine',
        desc: 'Cross-checks every claim against 500+ real-time databases, encyclopedic knowledge bases, and fact-checker archives.',
        icon: ScanSearch,
        color: 'cyan',
        glow: 'rgba(34,211,238,0.2)',
    },
    {
        id: '03',
        name: 'Deepfake Detector',
        role: 'Visual Forensics',
        desc: 'Performs frame-level analysis on images and video for GAN artifacts, face-swap signatures, and AI-synthesis markers.',
        icon: ShieldAlert,
        color: 'purple',
        glow: 'rgba(168,85,247,0.2)',
    },
    {
        id: '04',
        name: 'Bias Analyzer',
        role: 'Sentiment & Spin',
        desc: 'Measures political lean, emotional loading, framing techniques, and loaded language across the full content body.',
        icon: Scale,
        color: 'amber',
        glow: 'rgba(245,158,11,0.2)',
    },
    {
        id: '05',
        name: 'Source Credibility',
        role: 'Publisher Trust',
        desc: 'Scores domains, authors, and publishers against historical accuracy records, media bias indexes, and citation networks.',
        icon: BadgeCheck,
        color: 'blue',
        glow: 'rgba(59,130,246,0.2)',
    },
    {
        id: '06',
        name: 'Consensus Engine',
        role: 'Final Verdict',
        desc: 'Aggregates multi-agent verdicts using a weighted Bayesian model to produce a single calibrated integrity score.',
        icon: GitMerge,
        color: 'emerald',
        glow: 'rgba(16,185,129,0.2)',
    },
];

/* ─────────────────────────────────────────────
   Per-colour token map (static classes only,
   so Tailwind's scanner can detect them at build)
───────────────────────────────────────────── */
const COLOR_TOKENS: Record<string, {
    badge: string;
    icon: string;
    number: string;
    border: string;
    dot: string;
}> = {
    orange: {
        badge: 'bg-orange-500/10 border-orange-500/20 text-orange-400',
        icon:  'bg-orange-500/10 border-orange-500/20 text-orange-400',
        number:'text-orange-500/20',
        border:'hover:border-orange-500/30',
        dot:   'bg-orange-500',
    },
    cyan: {
        badge: 'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
        icon:  'bg-cyan-500/10 border-cyan-500/20 text-cyan-400',
        number:'text-cyan-500/20',
        border:'hover:border-cyan-500/30',
        dot:   'bg-cyan-500',
    },
    purple: {
        badge: 'bg-purple-500/10 border-purple-500/20 text-purple-400',
        icon:  'bg-purple-500/10 border-purple-500/20 text-purple-400',
        number:'text-purple-500/20',
        border:'hover:border-purple-500/30',
        dot:   'bg-purple-500',
    },
    amber: {
        badge: 'bg-amber-500/10 border-amber-500/20 text-amber-400',
        icon:  'bg-amber-500/10 border-amber-500/20 text-amber-400',
        number:'text-amber-500/20',
        border:'hover:border-amber-500/30',
        dot:   'bg-amber-500',
    },
    blue: {
        badge: 'bg-blue-500/10 border-blue-500/20 text-blue-400',
        icon:  'bg-blue-500/10 border-blue-500/20 text-blue-400',
        number:'text-blue-500/20',
        border:'hover:border-blue-500/30',
        dot:   'bg-blue-500',
    },
    emerald: {
        badge: 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
        icon:  'bg-emerald-500/10 border-emerald-500/20 text-emerald-400',
        number:'text-emerald-500/20',
        border:'hover:border-emerald-500/30',
        dot:   'bg-emerald-500',
    },
};

/* ─────────────────────────────────────────────
   Pipeline Visualisation (replaces flow.mp4)
───────────────────────────────────────────── */
const PIPELINE_AGENTS = [
    { label: 'Orchestrator',  color: '#f97316', delay: 0    },
    { label: 'Fact Verifier', color: '#22d3ee', delay: 0.4  },
    { label: 'Deepfake Det.', color: '#a855f7', delay: 0.8  },
    { label: 'Bias Analyzer', color: '#fbbf24', delay: 1.2  },
    { label: 'Src Credibility',color: '#3b82f6', delay: 1.6 },
    { label: 'Consensus Eng.',color: '#10b981', delay: 2.0  },
];

const LOG_LINES = [
    { t: 0,   text: '→ Claim received. Dispatching to 6 agents…',         color: 'text-white/40' },
    { t: 700, text: '✓ Fact Verifier: 14 sources matched (Reuters, AP)',   color: 'text-cyan-400/80' },
    { t: 1400,text: '✓ Deepfake Detector: No visual manipulation found',   color: 'text-purple-400/80' },
    { t: 2100,text: '✓ Bias Analyzer: Low political loading detected',     color: 'text-amber-400/80' },
    { t: 2800,text: '✓ Source Credibility: Domain authority 94/100',       color: 'text-blue-400/80' },
    { t: 3500,text: '✓ Consensus Engine: 5/6 agents SUPPORT claim',        color: 'text-emerald-400/80' },
    { t: 4200,text: '◆ Verdict: HIGHLY CREDIBLE — score 91/100',           color: 'text-orange-400 font-bold' },
];

function PipelineViz() {
    const [visibleLogs, setVisibleLogs] = useState<number[]>([]);
    const [activeAgent, setActiveAgent] = useState(0);
    const [done, setDone] = useState(false);
    const timerRefs = useRef<ReturnType<typeof setTimeout>[]>([]);

    const restart = () => {
        timerRefs.current.forEach(clearTimeout);
        timerRefs.current = [];
        setVisibleLogs([]);
        setActiveAgent(0);
        setDone(false);

        LOG_LINES.forEach((line, i) => {
            const t = setTimeout(() => {
                setVisibleLogs(prev => [...prev, i]);
                setActiveAgent(Math.min(i, PIPELINE_AGENTS.length - 1));
                if (i === LOG_LINES.length - 1) setDone(true);
            }, line.t + 400);
            timerRefs.current.push(t);
        });
    };

    useEffect(() => {
        restart();
        return () => timerRefs.current.forEach(clearTimeout);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Auto-loop
    useEffect(() => {
        if (!done) return;
        const t = setTimeout(restart, 2800);
        return () => clearTimeout(t);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [done]);

    return (
        <div className="flex flex-col md:flex-row gap-0 min-h-[320px]">

            {/* Left: agent nodes */}
            <div className="md:w-44 shrink-0 flex flex-row md:flex-col justify-center md:justify-start gap-2 p-4 bg-black/40 border-b md:border-b-0 md:border-r border-white/5">
                {PIPELINE_AGENTS.map((a, i) => (
                    <motion.div
                        key={a.label}
                        animate={{
                            opacity: i <= activeAgent ? 1 : 0.2,
                            scale:   i === activeAgent ? 1.04 : 1,
                        }}
                        transition={{ duration: 0.3 }}
                        className="flex items-center gap-2 px-2 py-1.5 rounded-lg"
                    >
                        <motion.span
                            className="shrink-0 w-2 h-2 rounded-full"
                            style={{ backgroundColor: a.color }}
                            animate={i === activeAgent ? { scale: [1, 1.6, 1], opacity: [1, 0.5, 1] } : {}}
                            transition={{ duration: 0.8, repeat: i === activeAgent && !done ? Infinity : 0 }}
                        />
                        <span className="text-[9px] font-black uppercase tracking-wider text-white/50 hidden md:block leading-tight">
                            {a.label}
                        </span>
                    </motion.div>
                ))}
            </div>

            {/* Right: scrolling log */}
            <div className="flex-1 p-5 font-mono text-[11px] leading-6 overflow-hidden flex flex-col justify-end gap-0.5 bg-black/20">
                <AnimatePresence initial={false}>
                    {visibleLogs.map(i => (
                        <motion.p
                            key={i}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.25 }}
                            className={LOG_LINES[i].color}
                        >
                            {LOG_LINES[i].text}
                        </motion.p>
                    ))}
                </AnimatePresence>
                {/* blinking cursor */}
                {!done && (
                    <motion.span
                        className="w-2 h-3.5 bg-orange-500/70 inline-block ml-0.5"
                        animate={{ opacity: [1, 0, 1] }}
                        transition={{ duration: 0.9, repeat: Infinity }}
                    />
                )}
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────
   AgentsSection
───────────────────────────────────────────── */
export default function AgentsSection() {

    return (
        <section id="agents" className="relative py-32 px-6 bg-[#030303] overflow-hidden">

            {/* Ambient background glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[700px] bg-orange-500/5 blur-[220px] pointer-events-none" />
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyan-500/5 blur-[180px] pointer-events-none" />

            <div className="max-w-7xl mx-auto relative z-10">

                {/* ── Section Header ── */}
                <motion.div
                    initial={{ opacity: 0, y: 24 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, margin: '-80px' }}
                    transition={{ duration: 0.7 }}
                    className="text-center mb-20"
                >
                    {/* Label badge */}
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-orange-500/10 border border-orange-500/20 mb-6">
                        <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                        <span className="text-[10px] uppercase font-black tracking-[0.2em] text-orange-500">
                            The Agent Network
                        </span>
                    </div>

                    <h2 className="text-5xl md:text-7xl font-black tracking-tighter text-white leading-[0.92] mb-6">
                        6 MINDS.{' '}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 via-orange-500 to-red-600">
                            ONE VERDICT.
                        </span>
                    </h2>

                    <p className="text-white/40 text-lg max-w-2xl mx-auto font-medium leading-relaxed">
                        Every query triggers a coordinated swarm of specialist AI agents that
                        debate, cross-examine, and converge on the truth — with zero room for
                        manipulation.
                    </p>
                </motion.div>

                {/* ── Video Showcase ── */}
                <motion.div
                    initial={{ opacity: 0, y: 40, scale: 0.97 }}
                    whileInView={{ opacity: 1, y: 0, scale: 1 }}
                    viewport={{ once: true, margin: '-80px' }}
                    transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
                    className="relative mb-24 mx-auto max-w-3xl"
                >
                    {/* Outer gradient glow rings */}
                    <div className="absolute -inset-[1px] rounded-[2.5rem] bg-gradient-to-r from-orange-500/40 via-white/5 to-cyan-500/30 blur-[2px]" />
                    <div className="absolute -inset-[8px] rounded-[2.8rem] bg-gradient-to-r from-orange-500/10 to-cyan-500/10 blur-2xl" />

                    {/* Video card */}
                    <div className="relative rounded-[2.5rem] overflow-hidden border border-white/10 bg-black shadow-[0_0_140px_rgba(249,115,22,0.12)]">

                        {/* Top chrome bar */}
                        <div className="flex items-center justify-between px-6 py-3.5 bg-white/[0.03] border-b border-white/5">
                            {/* Left: status */}
                            <div className="flex items-center gap-2.5">
                                <span className="relative flex">
                                    <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-orange-500 opacity-60" />
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500" />
                                </span>
                                <span className="text-[10px] uppercase font-black tracking-[0.2em] text-white/30">
                                    Live Agent Workflow
                                </span>
                            </div>

                            {/* Right: mock window controls */}
                            <div className="flex items-center gap-1.5">
                                <div className="w-3 h-3 rounded-full bg-red-500/50" />
                                <div className="w-3 h-3 rounded-full bg-yellow-400/50" />
                                <div className="w-3 h-3 rounded-full bg-green-500/50" />
                            </div>
                        </div>

                        {/* Animated Pipeline Visualisation */}
                        <PipelineViz />

                        {/* Bottom info bar */}
                        <div className="flex items-center justify-between px-6 py-3.5 bg-white/[0.02] border-t border-white/5">
                            <span className="text-[9px] uppercase font-black tracking-[0.18em] text-white/20">
                                ZeroTrust · Multi-Agent Verification Pipeline
                            </span>
                            <div className="flex items-center gap-4">
                                {['Routing', 'Analysis', 'Consensus'].map((step, i) => (
                                    <div key={step} className="flex items-center gap-1.5">
                                        <span className="w-1 h-1 rounded-full bg-cyan-500/60" />
                                        <span className="text-[9px] uppercase font-black tracking-widest text-white/20">{step}</span>
                                        {i < 2 && (
                                            <span className="text-white/10 text-[8px] ml-1">›</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </motion.div>

                {/* ── Agent Cards ── */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {AGENTS.map((agent, i) => {
                        const c = COLOR_TOKENS[agent.color];
                        return (
                            <motion.div
                                key={agent.id}
                                initial={{ opacity: 0, y: 36 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true, margin: '-60px' }}
                                transition={{ duration: 0.55, delay: i * 0.07, ease: [0.22, 1, 0.36, 1] }}
                                className={`group relative p-7 rounded-[2rem] bg-white/[0.025] border border-white/[0.06] ${c.border} transition-all duration-500 overflow-hidden cursor-default`}
                            >
                                {/* Per-card hover glow */}
                                <div
                                    className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-[2rem]"
                                    style={{ background: `radial-gradient(ellipse at 50% -10%, ${agent.glow} 0%, transparent 65%)` }}
                                />

                                <div className="relative z-10">
                                    {/* Ghost number */}
                                    <div className={`absolute -top-2 right-3 text-7xl font-black ${c.number} leading-none select-none pointer-events-none`}>
                                        {agent.id}
                                    </div>

                                    {/* Icon */}
                                    <div className={`w-12 h-12 rounded-2xl border flex items-center justify-center mb-5 ${c.icon} group-hover:scale-110 transition-transform duration-500`}>
                                        <agent.icon size={22} />
                                    </div>

                                    {/* Role badge */}
                                    <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-[9px] uppercase font-black tracking-[0.15em] mb-3 ${c.badge}`}>
                                        <span className={`w-1 h-1 rounded-full ${c.dot}`} />
                                        {agent.role}
                                    </div>

                                    {/* Name */}
                                    <h3 className="text-xl font-black text-white tracking-tight mb-2.5">
                                        {agent.name}
                                    </h3>

                                    {/* Description */}
                                    <p className="text-sm text-white/35 leading-relaxed font-medium">
                                        {agent.desc}
                                    </p>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>

                {/* ── Bottom connector hint ── */}
                <motion.div
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.5 }}
                    className="mt-16 flex items-center justify-center gap-3"
                >
                    <div className="h-px w-24 bg-gradient-to-r from-transparent to-white/10" />
                    <span className="text-[9px] uppercase font-black tracking-[0.25em] text-white/20">
                        All agents operate in parallel
                    </span>
                    <div className="h-px w-24 bg-gradient-to-l from-transparent to-white/10" />
                </motion.div>

            </div>
        </section>
    );
}
