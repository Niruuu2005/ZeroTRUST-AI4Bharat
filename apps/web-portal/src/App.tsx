import { useState } from 'react';
import { ClaimInput } from './components/claim/ClaimInput';
import { CredibilityScore } from './components/results/CredibilityScore';
import { SourceList } from './components/results/SourceList';
import { AgentBreakdown } from './components/results/AgentBreakdown';
import { EvidenceSummary } from './components/results/EvidenceSummary';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { HistoryPage } from './components/history/HistoryPage';
import { useVerificationStore } from './store/verificationStore';
import { useAuthStore } from './store/authStore';
import { ShieldCheck, LogIn, UserPlus, History, LogOut } from 'lucide-react';

type View = 'home' | 'login' | 'register' | 'history';

function App() {
  const [view, setView] = useState<View>('home');
  const { current, isLoading, error } = useVerificationStore();
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900 pb-20">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 glass-card bg-white/90 border-b border-slate-200/50 rounded-none shadow-sm px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <button type="button" onClick={() => setView('home')} className="flex items-center gap-3">
            <div className="bg-blue-600 p-2 rounded-xl text-white shadow-lg shadow-blue-500/30">
              <ShieldCheck size={24} strokeWidth={2.5} />
            </div>
            <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-700 to-indigo-700">
              ZeroTRUST
            </span>
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setView('home')}
              className="px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Verify
            </button>
            {accessToken ? (
              <>
                <button
                  type="button"
                  onClick={() => setView('history')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  <History size={16} /> History
                </button>
                <button
                  type="button"
                  onClick={() => { logout(); setView('home'); }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  <LogOut size={16} /> Logout
                </button>
                <span className="text-xs text-slate-400 truncate max-w-[120px]">{user?.email}</span>
              </>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => setView('login')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  <LogIn size={16} /> Login
                </button>
                <button
                  type="button"
                  onClick={() => setView('register')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-100"
                >
                  <UserPlus size={16} /> Register
                </button>
              </>
            )}
          </div>
        </div>
        <div className="text-sm font-medium text-slate-500">Prototype v1.0</div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 pt-16">
        {view === 'login' && (
          <div className="pt-8">
            <LoginForm onSuccess={() => setView('home')} onSwitchRegister={() => setView('register')} />
          </div>
        )}
        {view === 'register' && (
          <div className="pt-8">
            <RegisterForm onSuccess={() => setView('home')} onSwitchLogin={() => setView('login')} />
          </div>
        )}
        {view === 'history' && (
          <div className="pt-4">
            <HistoryPage />
          </div>
        )}
        {view === 'home' && (
          <>
            {/* Hero Section */}
            <div className="text-center mb-16">
              <h1 className="text-5xl font-black text-slate-900 mb-6 tracking-tight">
                Verify any claim in <span className="text-blue-600 relative inline-block">seconds.
                  <span className="absolute -bottom-2 left-0 w-full h-1.5 bg-blue-200 rounded-full"></span>
                </span>
              </h1>
              <p className="text-lg text-slate-500 max-w-2xl mx-auto font-medium leading-relaxed">
                Our multi-agent AI system consults 6 distinct models and dozens of live sources
                to fact-check text, news articles, images, and videos.
              </p>
            </div>

            {/* Input */}
            <ClaimInput />

        {/* Results */}
        {error && (
          <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-2xl text-red-700 font-medium text-center shadow-sm">
            ❌ {error}
          </div>
        )}

        {current && !isLoading && view === 'home' && (
          <div className="mt-16 space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-700 ease-out">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <CredibilityScore result={current} />
              <div className="space-y-4">
                {current.evidence_summary && (
                  <EvidenceSummary evidence_summary={current.evidence_summary} />
                )}
                <div className="glass-card p-8 flex flex-col justify-center">
                 <h3 className="text-sm uppercase tracking-widest font-bold text-slate-400 mb-4">Recommendation</h3>
                 <p className="text-lg leading-relaxed text-slate-700">{current.recommendation}</p>
                 
                 {current.limitations?.length > 0 && (
                   <div className="mt-6 pt-6 border-t border-slate-100">
                     <h4 className="text-xs font-bold uppercase text-slate-400 mb-2">Transparency Notes</h4>
                     <ul className="space-y-2">
                       {current.limitations.map((lim, i) => (
                         <li key={i} className="text-sm text-slate-500 flex gap-2">
                           <span className="text-amber-500">⚠️</span> {lim}
                         </li>
                       ))}
                     </ul>
                   </div>
                 )}
                </div>
              </div>
            </div>

            <AgentBreakdown verdicts={current.agent_verdicts} />
            <SourceList sources={current.sources} />
          </div>
        )}
          </>
        )}
      </main>
    </div>
  );
}

export default App;
