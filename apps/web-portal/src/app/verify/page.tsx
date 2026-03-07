"use client";

import { useEffect, useState, useRef, Suspense, FormEvent } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    ShieldCheck,
    AlertCircle,
    ExternalLink,
    CheckCircle2,
    Loader2,
    // CheckCircle2 used in copied-state Share button below
    Brain,
    ArrowLeft,
    ArrowRight,
    Share2,
    Download
} from 'lucide-react';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';

interface VerificationResult {
    id: string;
    credibility_score: number;
    category: string;
    confidence: number;
    sources_consulted: number;
    evidence_summary: string | { [key: string]: any };
    sources: Array<{ title: string; url: string }>;
    agent_verdicts: { [key: string]: string };
    processing_time: number;
    cached: boolean;
}

// ── Agent pipeline config (used only by LoadingScreen) ──────────────────────
const LOAD_AGENTS = [
    { id: 'news',      label: 'News Agent',      sub: 'Reuters · AP · BBC',      color: '#f97316' },
    { id: 'scraper',   label: 'Scraper Agent',   sub: 'Web Crawler · Archives',  color: '#a78bfa' },
    { id: 'science',   label: 'Science Agent',   sub: 'PubMed · arXiv',          color: '#22d3ee' },
    { id: 'social',    label: 'Social Agent',    sub: 'Twitter · Reddit',         color: '#f472b6' },
    { id: 'research',  label: 'Research Agent',  sub: 'JSTOR · CrossRef',        color: '#4ade80' },
    { id: 'sentiment', label: 'Sentiment Agent', sub: 'NLP · BERT',              color: '#fbbf24' },
] as const;

type AgentId    = typeof LOAD_AGENTS[number]['id'];
type AgentState = 'idle' | 'scanning' | 'complete';
interface LogLine { ts: string; text: string; cls: string }

const LOG_STEPS: Array<{
    delay: number; ts: string; text: string; cls: string;
    agentId?: AgentId; agentState?: AgentState; srcAdd?: number;
}> = [
    { delay: 0,    ts: '00:00.0', text: '→ Initializing 6-Agent Neural Hub', cls: 'text-white/50' },
    { delay: 280,  ts: '00:00.3', text: '→ DNN context encoder ready', cls: 'text-white/30' },
    { delay: 520,  ts: '00:00.5', text: '→ [news]      Connecting to global news feeds...', cls: 'text-orange-400', agentId: 'news', agentState: 'scanning' },
    { delay: 720,  ts: '00:00.7', text: '→ [scraper]   Crawling primary source documents...', cls: 'text-violet-400', agentId: 'scraper', agentState: 'scanning' },
    { delay: 980,  ts: '00:01.0', text: '→ [news]      4 articles matched — 3× support, 1× neutral', cls: 'text-orange-300', agentId: 'news', agentState: 'complete', srcAdd: 4 },
    { delay: 1180, ts: '00:01.2', text: '→ [science]   Querying PubMed Central + arXiv...', cls: 'text-cyan-400', agentId: 'science', agentState: 'scanning' },
    { delay: 1340, ts: '00:01.3', text: '→ [scraper]   12 primary sources authenticated ✓', cls: 'text-violet-300', agentId: 'scraper', agentState: 'complete', srcAdd: 12 },
    { delay: 1550, ts: '00:01.6', text: '→ [social]    Scanning 14k+ posts across platforms...', cls: 'text-pink-400', agentId: 'social', agentState: 'scanning' },
    { delay: 1750, ts: '00:01.8', text: '→ [research]  Academic citation cross-reference...', cls: 'text-green-400', agentId: 'research', agentState: 'scanning' },
    { delay: 1960, ts: '00:02.0', text: '→ [science]   3 peer-reviewed papers confirmed ✓', cls: 'text-cyan-300', agentId: 'science', agentState: 'complete', srcAdd: 3 },
    { delay: 2160, ts: '00:02.2', text: '→ [social]    Viral spread score 0.12 — Low risk ✓', cls: 'text-pink-300', agentId: 'social', agentState: 'complete' },
    { delay: 2360, ts: '00:02.4', text: '→ [sentiment] NLP pipeline active — tokenizing claim...', cls: 'text-yellow-400', agentId: 'sentiment', agentState: 'scanning' },
    { delay: 2560, ts: '00:02.6', text: '→ [research]  6 academic citations verified ✓', cls: 'text-green-300', agentId: 'research', agentState: 'complete', srcAdd: 6 },
    { delay: 2800, ts: '00:02.8', text: '→ [sentiment] Consensus signal → 78% positive ✓', cls: 'text-yellow-300', agentId: 'sentiment', agentState: 'complete' },
    { delay: 3050, ts: '00:03.1', text: '→ All 6 agents complete. Synthesizing verdicts...', cls: 'text-white/60' },
    { delay: 3350, ts: '00:03.4', text: '→ Consensus Engine computing final verdict...', cls: 'text-white/60' },
    { delay: 3700, ts: '00:03.7', text: '→ Credibility score calculated', cls: 'text-orange-400' },
    { delay: 4050, ts: '00:04.1', text: '→ Signing verification report...', cls: 'text-white/40' },
];

function LoadingScreen() {
    const [agentStates, setAgentStates] = useState<Record<AgentId, AgentState>>(
        () => Object.fromEntries(LOAD_AGENTS.map(a => [a.id, 'idle' as AgentState])) as Record<AgentId, AgentState>
    );
    const [logs, setLogs]       = useState<LogLine[]>([]);
    const [srcCount, setSrcCount] = useState(0);
    const logEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const timers: ReturnType<typeof setTimeout>[] = [];
        LOG_STEPS.forEach(step => {
            timers.push(setTimeout(() => {
                setLogs(prev => [...prev, { ts: step.ts, text: step.text, cls: step.cls }]);
                if (step.agentId && step.agentState) {
                    setAgentStates(prev => ({ ...prev, [step.agentId!]: step.agentState! }));
                }
                if (step.srcAdd) {
                    setSrcCount(prev => prev + step.srcAdd!);
                }
            }, step.delay));
        });
        return () => timers.forEach(clearTimeout);
    }, []);

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div className="py-12">
            {/* heading */}
            <div className="text-center mb-10">
                <div className="relative inline-flex items-center justify-center mb-6">
                    <div className="absolute w-28 h-28 bg-orange-500/15 blur-[50px] rounded-full animate-pulse" />
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 14, repeat: Infinity, ease: 'linear' }}
                        className="absolute w-20 h-20 border border-orange-500/20 rounded-3xl"
                    />
                    <div className="relative w-20 h-20 border border-orange-500/30 rounded-3xl flex items-center justify-center bg-black/60">
                        <Brain size={36} className="text-orange-500" />
                    </div>
                </div>
                <h2 className="text-2xl font-black text-white italic uppercase tracking-tighter mb-2">
                    Neural Verification <span className="text-orange-500">In Progress</span>
                </h2>
                <motion.p
                    className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/30"
                    animate={{ opacity: [0.3, 0.7, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity }}
                >
                    {srcCount > 0 ? `${srcCount} sources scanned` : 'Booting agent cluster...'}
                </motion.p>
            </div>

            {/* agent cards + terminal side by side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">

                {/* agent status grid */}
                <div className="grid grid-cols-2 gap-2">
                    {LOAD_AGENTS.map(agent => {
                        const state = agentStates[agent.id];
                        return (
                            <div
                                key={agent.id}
                                className={`p-3 rounded-xl border transition-all duration-500 ${
                                    state === 'complete'
                                        ? 'border-white/10 bg-white/[0.035]'
                                        : state === 'scanning'
                                        ? 'bg-black/40'
                                        : 'border-white/[0.04] bg-white/[0.01]'
                                }`}
                                style={state === 'scanning' ? { borderColor: `${agent.color}50` } : undefined}
                            >
                                <div className="flex items-center gap-2 mb-1.5">
                                    <div
                                        className={`w-2 h-2 rounded-full flex-shrink-0 transition-all duration-300 ${
                                            state === 'complete'
                                                ? 'bg-emerald-400'
                                                : state === 'scanning'
                                                ? 'animate-pulse'
                                                : 'bg-white/15'
                                        }`}
                                        style={state === 'scanning' ? { backgroundColor: agent.color } : undefined}
                                    />
                                    <span className={`text-[9px] font-black uppercase tracking-wide leading-none ${
                                        state === 'idle' ? 'text-white/20' :
                                        state === 'scanning' ? 'text-white/80' : 'text-white/55'
                                    }`}>
                                        {agent.label}
                                    </span>
                                </div>
                                <p className={`text-[8px] mb-1.5 leading-tight ${
                                    state === 'idle' ? 'text-white/10' : 'text-white/25'
                                }`}>
                                    {agent.sub}
                                </p>
                                <div className={`flex items-center gap-1 text-[8px] font-black uppercase tracking-widest ${
                                    state === 'complete' ? 'text-emerald-400' :
                                    state === 'scanning'  ? 'text-orange-400' : 'text-white/15'
                                }`}>
                                    {state === 'complete'
                                        ? '✓ DONE'
                                        : state === 'scanning'
                                        ? <><Loader2 size={7} className="animate-spin" /> WORKING</>
                                        : 'IDLE'}
                                </div>
                            </div>
                        );
                    })}
                </div>

                {/* streaming terminal */}
                <div className="rounded-xl border border-white/[0.06] bg-black/70 overflow-hidden flex flex-col font-mono">
                    <div className="flex items-center gap-1.5 px-3 py-2 border-b border-white/[0.05] bg-white/[0.02] flex-shrink-0">
                        <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
                        <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
                        <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
                        <span className="ml-1.5 text-[8px] text-white/20 uppercase tracking-widest">zerotrust · agent.log</span>
                    </div>
                    <div className="flex-1 p-3 h-52 overflow-y-auto space-y-0.5">
                        <AnimatePresence>
                            {logs.map((log, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -6 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="flex gap-2 items-start"
                                >
                                    <span className="text-white/20 text-[8px] flex-shrink-0 mt-px">[{log.ts}]</span>
                                    <span className={`${log.cls} text-[8px] leading-relaxed`}>{log.text}</span>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        <motion.span
                            animate={{ opacity: [1, 0, 1] }}
                            transition={{ duration: 0.8, repeat: Infinity }}
                            className="text-orange-500/60 text-[10px]"
                        >▋</motion.span>
                        <div ref={logEndRef} />
                    </div>
                </div>
            </div>

            {/* progress bar */}
            <div className="w-full bg-white/[0.04] rounded-full overflow-hidden h-px">
                <motion.div
                    className="h-full bg-gradient-to-r from-orange-600 to-orange-400"
                    initial={{ width: '0%' }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 5, ease: 'easeInOut' }}
                />
            </div>
            <div className="flex justify-between mt-2">
                <span className="text-[8px] font-bold uppercase tracking-widest text-white/15">Processing</span>
                <span className="text-[8px] font-bold uppercase tracking-widest text-white/15">~5s avg latency</span>
            </div>
        </div>
    );
}

function VerifyContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [result, setResult] = useState<VerificationResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [newQuery, setNewQuery] = useState('');
    const [copied, setCopied] = useState(false);

    const handleShare = async () => {
        try {
            await navigator.clipboard.writeText(window.location.href);
            setCopied(true);
            setTimeout(() => setCopied(false), 2500);
        } catch {
            // fallback for browsers that block clipboard
            prompt('Copy this link:', window.location.href);
        }
    };

    const handleDownload = () => {
        if (!result) return;
        const payload = {
            id: result.id,
            query: query || fileName || null,
            mode,
            source,
            credibility_score: result.credibility_score,
            category: result.category,
            confidence: result.confidence,
            sources_consulted: result.sources_consulted,
            processing_time: result.processing_time,
            evidence_summary: result.evidence_summary,
            agent_verdicts: result.agent_verdicts,
            sources: result.sources,
            cached: result.cached,
            exported_at: new Date().toISOString(),
        };
        const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        a.href     = url;
        a.download = `zerotrust-report-${result.id}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const query = searchParams.get('q');
    const mode = searchParams.get('mode') || 'text';
    const source = searchParams.get('source') || 'web';
    const fileVerify = searchParams.get('fileVerify') === '1';
    const fileName = searchParams.get('fileName') || '';

    useEffect(() => {
        if (!query && !fileVerify) {
            setError("No verification query provided.");
            setLoading(false);
            return;
        }

        let cancelled = false;

        const fetchResults = async () => {
            // ── Mock data (swap for real backend later) ───────────────────
            await new Promise(resolve => setTimeout(resolve, 5200));
            if (cancelled) return;

            const label = fileVerify ? (fileName || 'Uploaded File') : (query || '');
            const data: VerificationResult = {
                id: "ZT-" + Math.floor(Math.random() * 90000 + 10000),
                credibility_score: 87,
                category: "Highly Credible Content",
                confidence: 0.94,
                sources_consulted: 25,
                processing_time: 4.1,
                evidence_summary:
                    "Multiple high-authority news agencies and peer-reviewed journals confirm the premise of this claim. " +
                    "Cross-referencing 25 global feeds across Reuters, AP, BBC, PubMed and arXiv shows strong consensus " +
                    "among established publishers. Sentiment analysis returned a 78% positive signal with low bias score (0.12). " +
                    "No deepfake indicators or synthetic manipulation detected in the submitted content.",
                sources: [
                    { title: "Reuters — Global Verification Archive", url: "https://reuters.com/fact-check" },
                    { title: "Associated Press — AP Fact Check", url: "https://apnews.com/hub/ap-fact-check" },
                    { title: "PubMed Central — Scientific Cross-Reference", url: "https://pubmed.ncbi.nlm.nih.gov" },
                    { title: "BBC Reality Check", url: "https://bbc.com/news/reality_check" },
                    { title: "Snopes — Independent Fact Checking", url: "https://snopes.com" },
                ],
                agent_verdicts: {
                    "News Agent":      "Supported",
                    "Scraper Agent":   "Supported",
                    "Science Agent":   "Supported",
                    "Social Agent":    "Contradicted (Low Confidence)",
                    "Research Agent":  "Supported",
                    "Sentiment Agent": "Neutral",
                },
                cached: false,
            };

            setResult(data);
            setLoading(false);
        };

        fetchResults();

        return () => {
            cancelled = true;
        };
    }, [query, mode, source, fileVerify]);

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center p-6 bg-[#030303]">
                <div className="glass-card p-12 border-red-500/20 bg-red-500/5 text-center max-w-lg">
                    <AlertCircle size={48} className="text-red-500 mx-auto mb-6" />
                    <h2 className="text-2xl font-black text-white mb-4 italic uppercase tracking-tighter">System Error</h2>
                    <p className="text-white/60 mb-8 font-medium">{error}</p>
                    <Link href="/" className="inline-flex items-center gap-2 text-orange-500 font-bold hover:gap-4 transition-all">
                        <ArrowLeft size={18} /> BACK TO TERMINAL
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen pt-28 pb-20 px-4 md:px-8 bg-[#030303] selection:bg-orange-500/30">
            <div className="max-w-5xl mx-auto">
                <AnimatePresence mode="wait">
                    {loading ? (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                        >
                            <LoadingScreen />
                        </motion.div>
                    ) : result && (
                        <motion.div
                            key="result"
                            initial={{ opacity: 0, y: 40 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-8"
                        >
                            {/* Header Result Card */}
                            <div className="glass-card overflow-hidden border-white/5 bg-white/[0.02]">
                                <div className="p-6 md:p-10 md:flex items-center justify-between gap-10 bg-gradient-to-br from-orange-500/10 to-transparent">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-6">
                                            <div className="bg-orange-500 p-2 rounded-xl text-black">
                                                <ShieldCheck size={24} />
                                            </div>
                                            <h3 className="text-2xl font-black text-white tracking-tighter uppercase italic">
                                                Verification <span className="text-orange-500">Report</span>
                                            </h3>
                                        </div>

                                        {(query || fileName) && (
                                            <p className="text-white/20 text-xs font-medium mb-3 truncate max-w-lg">
                                                &ldquo;{(query || fileName).length > 80 ? (query || fileName).slice(0, 80) + '\u2026' : (query || fileName)}&rdquo;
                                            </p>
                                        )}
                                        <p className="text-white/40 text-[10px] uppercase font-bold tracking-[0.3em] mb-4">Final Verdict</p>
                                        <h1 className="text-4xl md:text-5xl font-black text-white tracking-tighter mb-6 leading-[0.9]">
                                            {result.category}
                                        </h1>

                                        <div className="flex gap-4">
                                            <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/5 text-[10px] font-black tracking-widest text-white/40">
                                                {result.processing_time || 2.4}S LATENCY
                                            </div>
                                            <div className="px-4 py-2 rounded-xl bg-white/5 border border-white/5 text-[10px] font-black tracking-widest text-white/40 uppercase">
                                                {result.sources_consulted} SOURCES CITED
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-8 md:mt-0 text-center">
                                        <div className="relative inline-block">
                                            <svg viewBox="0 0 160 160" className="w-40 h-40 transform -rotate-90">
                                                <circle
                                                    cx="80"
                                                    cy="80"
                                                    r="70"
                                                    stroke="currentColor"
                                                    strokeWidth="8"
                                                    fill="transparent"
                                                    className="text-white/5"
                                                />
                                                <motion.circle
                                                    cx="80"
                                                    cy="80"
                                                    r="70"
                                                    stroke="currentColor"
                                                    strokeWidth="8"
                                                    fill="transparent"
                                                    strokeDasharray={440}
                                                    initial={{ strokeDashoffset: 440 }}
                                                    animate={{ strokeDashoffset: 440 - (440 * result.credibility_score) / 100 }}
                                                    transition={{ duration: 1.5, ease: "easeOut" }}
                                                    className="text-orange-500 drop-shadow-[0_0_10px_rgba(249,115,22,0.5)]"
                                                />
                                            </svg>
                                            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                                                <div className="text-4xl font-black text-white">{result.credibility_score}%</div>
                                                <div className="text-[8px] font-bold text-white/30 tracking-[0.2em] uppercase">Credibility</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="px-6 md:px-10 pb-8">
                                    <div className="p-5 rounded-2xl bg-white/5 border border-white/5 text-sm md:text-base font-medium text-white/70 leading-relaxed italic border-l-orange-500 border-l-4">
                                        "{typeof result.evidence_summary === 'string'
                                            ? result.evidence_summary
                                            : JSON.stringify(result.evidence_summary)}"
                                    </div>
                                </div>
                            </div>

                            {/* Agent Breakdown */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                <div className="glass-card p-6 border-white/5 bg-white/[0.02]">
                                    <h4 className="text-[9px] tracking-[0.3em] font-black text-white/30 mb-5 uppercase">Agent Consensus</h4>
                                    <div className="space-y-2.5">
                                        {Object.entries(result.agent_verdicts).map(([agent, verdict]) => (
                                            <div key={agent} className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-white/[0.03] border border-white/5">
                                                <div className="flex items-center gap-2.5 min-w-0">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse flex-shrink-0" />
                                                    <span className="text-[10px] font-black uppercase tracking-wider text-white/60 truncate">{agent}</span>
                                                </div>
                                                <span className={`text-[9px] font-black px-2.5 py-1 rounded-lg whitespace-nowrap flex-shrink-0 ${
                                                    verdict.toLowerCase().includes('support') ? 'bg-emerald-500/10 text-emerald-400' :
                                                    verdict.toLowerCase().includes('neutral') ? 'bg-amber-500/10 text-amber-400' :
                                                    'bg-red-500/10 text-red-400'
                                                }`}>
                                                    {verdict.toUpperCase()}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                <div className="glass-card p-6 border-white/5 bg-white/[0.02]">
                                    <h4 className="text-[9px] tracking-[0.3em] font-black text-white/30 mb-5 uppercase">Direct Evidence</h4>
                                    <div className="space-y-2.5">
                                        {result.sources?.slice(0, 5).map((src, i) => (
                                            <a
                                                key={i}
                                                href={src.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all group"
                                            >
                                                <span className="text-[11px] font-bold text-white/60 truncate">{src.title || 'Verified Source'}</span>
                                                <ExternalLink size={13} className="text-white/20 group-hover:text-orange-500 flex-shrink-0" />
                                            </a>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Re-verify + actions */}
                            <div className="pt-4 space-y-4">
                                <form
                                    onSubmit={(e: FormEvent) => {
                                        e.preventDefault();
                                        const q = newQuery.trim();
                                        if (!q) return;
                                        const params = new URLSearchParams({ q, mode, source });
                                        router.push(`/verify?${params.toString()}`);
                                    }}
                                    className="flex items-center gap-2 p-2 glass-card border-white/[0.06] bg-white/[0.02] rounded-2xl"
                                >
                                    <input
                                        type="text"
                                        value={newQuery}
                                        onChange={e => setNewQuery(e.target.value)}
                                        placeholder="Verify another claim, URL, or article…"
                                        className="flex-1 bg-transparent outline-none text-sm text-white font-medium placeholder:text-white/20 px-4 py-3"
                                    />
                                    <button
                                        type="submit"
                                        disabled={!newQuery.trim()}
                                        className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-orange-600 to-red-600 text-white text-xs font-black disabled:opacity-30 disabled:cursor-not-allowed hover:scale-[1.02] active:scale-[0.98] transition-all uppercase tracking-widest"
                                    >
                                        <ArrowRight size={14} /> Verify
                                    </button>
                                </form>
                                <div className="flex flex-wrap justify-center gap-4">
                                    <button
                                        onClick={handleShare}
                                        className="flex items-center gap-2 px-8 py-4 rounded-2xl bg-white/5 border border-white/5 text-xs font-black text-white/60 hover:bg-white/10 transition-all uppercase tracking-widest"
                                    >
                                        {copied
                                            ? <><CheckCircle2 size={16} className="text-orange-500" /> Copied!</>
                                            : <><Share2 size={16} /> Share Report</>
                                        }
                                    </button>
                                    <button
                                        onClick={handleDownload}
                                        className="flex items-center gap-2 px-8 py-4 rounded-2xl bg-white/5 border border-white/5 text-xs font-black text-white/60 hover:bg-white/10 transition-all uppercase tracking-widest"
                                    >
                                        <Download size={16} /> Download JSON
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}

export default function VerifyPage() {
    return (
        <main className="bg-[#030303] text-white min-h-screen">
            <Navbar />
            <Suspense fallback={
                <div className="min-h-screen flex items-center justify-center">
                    <Loader2 size={40} className="text-orange-500 animate-spin" />
                </div>
            }>
                <VerifyContent />
            </Suspense>
        </main>
    );
}
