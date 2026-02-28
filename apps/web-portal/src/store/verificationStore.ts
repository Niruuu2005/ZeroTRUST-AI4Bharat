import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface VerificationResult {
  id: string;
  credibility_score: number;
  category: string;
  confidence: string;
  claim_type: string;
  sources_consulted: number;
  agent_consensus: string;
  evidence_summary: { supporting: number; contradicting: number; neutral: number };
  sources: any[];
  agent_verdicts: Record<string, any>;
  limitations: string[];
  recommendation: string;
  processing_time: number;
  cached: boolean;
  cache_tier?: string;
  created_at: string;
}

interface Store {
  current: VerificationResult | null;
  history: VerificationResult[];
  isLoading: boolean;
  error: string | null;
  setCurrent: (r: VerificationResult | null) => void;
  setLoading: (b: boolean) => void;
  setError: (e: string | null) => void;
  addToHistory: (r: VerificationResult) => void;
}

export const useVerificationStore = create<Store>()(devtools((set) => ({
  current: null,
  history: [],
  isLoading: false,
  error: null,
  setCurrent: (r) => set({ current: r }),
  setLoading: (b) => set({ isLoading: b }),
  setError: (e) => set({ error: e }),
  addToHistory: (r) => set((s) => ({ history: [r, ...s.history].slice(0, 50) })),
})));
