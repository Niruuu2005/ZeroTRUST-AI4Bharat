import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
import { ShieldCheck, LogIn, LogOut, Cpu, AlertCircle } from 'lucide-react';

type View = 'home' | 'login' | 'register' | 'history';

function App() {
  const [view, setView] = useState<View>('home');
  const { current, isLoading, error } = useVerificationStore();
  const accessToken = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      {/* Background Decorative Elements */}
      <div className="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 rounded-full blur-[120px] -z-10" />
      <div className="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 rounded-full blur-[120px] -z-10" />

      {/* Floating Navbar */}
      <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-3rem)] max-w-5xl">
        <div className="glass-card-heavy px-6 py-4 flex items-center justify-between border-white/[0.08]">
          <div className="flex items-center gap-8">
            <button
              type="button"
              onClick={() => setView('home')}
              className="flex items-center gap-3 group"
            >
              <motion.div
                whileHover={{ rotate: 360, scale: 1.1 }}
                transition={{ duration: 0.8, ease: "anticipate" }}
                className="bg-blue-600 p-2 rounded-2xl text-white shadow-[0_0_20px_rgba(37,99,235,0.4)]"
              >
                <ShieldCheck size={22} strokeWidth={2.5} />
              </motion.div>
              <div className="hidden sm:block">
                <span className="text-xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400 tracking-tight">
                  ZeroTRUST
                </span>
                <div className="text-[10px] font-bold text-blue-500/60 uppercase tracking-[0.2em] leading-none">AI Intelligence</div>
              </div>
            </button>
            <div className="hidden md:flex items-center gap-6">
              <button
                type="button"
                onClick={() => setView('home')}
                className={`text-sm font-bold tracking-wide transition-colors ${view === 'home' ? 'text-blue-400' : 'text-slate-400 hover:text-white'}`}
              >
                Verify
              </button>
              {accessToken && (
                <button
                  type="button"
                  onClick={() => setView('history')}
                  className={`text-sm font-bold tracking-wide transition-colors ${view === 'history' ? 'text-blue-400' : 'text-slate-400 hover:text-white'}`}
                >
                  Deep History
                </button>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <AnimatePresence mode="wait">
              {accessToken ? (
                <motion.div
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="flex items-center gap-4"
                >
                  <div className="hidden lg:flex flex-col items-end mr-2">
                    <span className="text-xs font-bold text-slate-200">{user?.email?.split('@')[0]}</span>
                    <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">Online</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => { logout(); setView('home'); }}
                    className="p-3 rounded-2xl bg-white/[0.03] border border-white/10 text-slate-400 hover:text-red-400 hover:bg-red-400/10 transition-all"
                  >
                    <LogOut size={18} />
                  </button>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="flex items-center gap-2"
                >
                  <button
                    type="button"
                    onClick={() => setView('login')}
                    className="hidden sm:flex items-center gap-2 px-5 py-2.5 rounded-2xl font-bold text-sm text-slate-400 hover:text-white hover:bg-white/[0.05] transition-all"
                  >
                    <LogIn size={16} /> Login
                  </button>
                  <button
                    type="button"
                    onClick={() => setView('register')}
                    className="flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-blue-600 text-white font-bold text-sm shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:bg-blue-500 transition-all"
                  >
                    Join <span className="hidden sm:inline">Portal</span>
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 pt-40 pb-32">
        <AnimatePresence mode="wait">
          {view === 'home' && (
            <motion.div
              key="home"
              initial="hidden"
              animate="visible"
              exit="hidden"
              variants={containerVariants}
              className="space-y-12"
            >
              {/* Hero Section */}
              <motion.div variants={itemVariants} className="text-center relative">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-blue-500/20 blur-[80px] -z-10 rounded-full" />
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold tracking-widest uppercase mb-8">
                  <Cpu size={14} /> Multi-Agent Verification Platform
                </div>
                <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black text-white mb-8 tracking-tighter leading-[1.1]">
                  Uncover truth with <br />
                  <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 glow-text">
                    Pure AI Intelligence.
                  </span>
                </h1>
                <p className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto font-medium leading-relaxed">
                  Real-time consensus from 6 premium models analyzing news, deepfakes, and controversial claims across dozens of verified data streams.
                </p>
              </motion.div>

              {/* Input */}
              <motion.div variants={itemVariants} className="relative">
                <ClaimInput />
              </motion.div>

              {/* Error Message */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="p-6 glass-card border-red-500/30 bg-red-500/5 text-red-200 flex items-center gap-4 max-w-2xl mx-auto"
                >
                  <div className="bg-red-500/20 p-2 rounded-xl text-red-400">
                    <AlertCircle size={24} />
                  </div>
                  <div>
                    <div className="font-bold">Verification Error</div>
                    <div className="text-sm text-red-300/80">{error}</div>
                  </div>
                </motion.div>
              )}

              {/* Discovery Results */}
              {current && !isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 40 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="pt-12 space-y-12"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <CredibilityScore result={current} />
                    <div className="space-y-6">
                      {current.evidence_summary && (
                        <EvidenceSummary evidence_summary={current.evidence_summary} />
                      )}
                      <motion.div
                        whileHover={{ y: -5 }}
                        className="glass-card-heavy p-8 border-white/[0.05]"
                      >
                        <h3 className="text-xs uppercase tracking-[0.2em] font-black text-blue-400 mb-6">Strategic Recommendation</h3>
                        <p className="text-xl leading-relaxed text-slate-200 font-medium italic">"{current.recommendation}"</p>

                        {current.limitations?.length > 0 && (
                          <div className="mt-8 pt-8 border-t border-white/5">
                            <h4 className="text-[10px] font-black uppercase text-slate-500 tracking-widest mb-4">Precision Notes</h4>
                            <div className="grid grid-cols-1 gap-3">
                              {current.limitations.map((lim, i) => (
                                <div key={i} className="text-sm text-slate-400 flex gap-3 items-start bg-white/[0.02] p-3 rounded-xl border border-white/5">
                                  <span className="text-amber-500 shrink-0 mt-0.5">⚠️</span>
                                  <span>{lim}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    </div>
                  </div>

                  <AgentBreakdown verdicts={current.agent_verdicts} />
                  <SourceList sources={current.sources} />
                </motion.div>
              )}
            </motion.div>
          )}

          {view === 'login' && (
            <motion.div
              key="login"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-md mx-auto"
            >
              <LoginForm onSuccess={() => setView('home')} onSwitchRegister={() => setView('register')} />
            </motion.div>
          )}

          {view === 'register' && (
            <motion.div
              key="register"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-md mx-auto"
            >
              <RegisterForm onSuccess={() => setView('home')} onSwitchLogin={() => setView('login')} />
            </motion.div>
          )}

          {view === 'history' && (
            <motion.div
              key="history"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <HistoryPage />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Footer Branding */}
      <footer className="fixed bottom-6 left-1/2 -translate-x-1/2 opacity-40 hover:opacity-100 transition-opacity">
        <div className="text-[10px] font-black uppercase tracking-[0.5em] text-slate-500">
          Distributed Intelligence Protocol v1.4
        </div>
      </footer>
    </div>
  );
}

export default App;
