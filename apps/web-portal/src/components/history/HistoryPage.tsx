import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuthStore } from '../../store/authStore';
import { CredibilityScore } from '../results/CredibilityScore';
import { VerificationResult } from '../../store/verificationStore';
import { Loader2, History } from 'lucide-react';

export function HistoryPage() {
  const accessToken = useAuthStore((s) => s.accessToken);
  const [items, setItems] = useState<VerificationResult[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const limit = 10;

  useEffect(() => {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    axios
      .get('/api/v1/history', {
        params: { page, limit },
        headers: { Authorization: `Bearer ${accessToken}` },
      })
      .then((res) => {
        const list = res.data.items || [];
        setItems(list.map((v: any) => ({
          id: v.id,
          credibility_score: v.credibilityScore,
          category: v.category,
          confidence: v.confidence,
          claim_type: v.claimType,
          sources_consulted: v.sourcesConsulted,
          agent_consensus: v.agentConsensus,
          evidence_summary: v.evidenceSummary || { supporting: 0, contradicting: 0, neutral: 0 },
          sources: v.sources || [],
          agent_verdicts: v.agentVerdicts || {},
          limitations: v.limitations || [],
          recommendation: v.recommendation,
          processing_time: v.processingTime,
          cached: v.cached,
          created_at: v.createdAt,
        })));
        setTotal(res.data.total ?? 0);
      })
      .catch((err) => setError(err.response?.data?.error || err.message || 'Failed to load history'))
      .finally(() => setLoading(false));
  }, [accessToken, page]);

  if (!accessToken) {
    return (
      <div className="glass-card p-8 max-w-md mx-auto text-center text-slate-600">
        Sign in to view your verification history.
      </div>
    );
  }

  if (loading && items.length === 0) {
    return (
      <div className="flex justify-center py-16">
        <Loader2 size={32} className="animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <History className="text-blue-600" size={28} />
        <h2 className="text-2xl font-bold text-slate-800">Verification history</h2>
      </div>
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 font-medium">{error}</div>
      )}
      {items.length === 0 && !loading ? (
        <div className="glass-card p-8 text-center text-slate-500">No verifications yet. Run a verification from the home page.</div>
      ) : (
        <div className="space-y-6">
          {items.map((item) => (
            <div key={item.id} className="glass-card p-6">
              <div className="flex flex-wrap gap-4 items-start">
                <div className="flex-1 min-w-[200px]">
                  <CredibilityScore result={item} />
                </div>
                <div className="flex-1 min-w-[200px]">
                  <p className="text-sm text-slate-500 mb-1">Recommendation</p>
                  <p className="text-slate-700">{item.recommendation}</p>
                  <p className="text-xs text-slate-400 mt-2">{new Date(item.created_at).toLocaleString()}</p>
                </div>
              </div>
            </div>
          ))}
          {total > limit && (
            <div className="flex justify-center gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-4 py-2 rounded-xl border border-slate-200 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-slate-600">
                Page {page} of {Math.ceil(total / limit)}
              </span>
              <button
                type="button"
                disabled={page >= Math.ceil(total / limit)}
                onClick={() => setPage((p) => p + 1)}
                className="px-4 py-2 rounded-xl border border-slate-200 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
