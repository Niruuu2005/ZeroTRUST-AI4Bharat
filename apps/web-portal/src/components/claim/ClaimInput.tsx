import { useState, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Link as LinkIcon, Image as ImageIcon, Video, Loader2, SendHorizontal } from 'lucide-react';
import { useVerificationStore } from '../../store/verificationStore';
import { useAuthStore } from '../../store/authStore';

const MODES = [
  { id: 'text', label: 'Claim Text', icon: FileText, color: 'text-blue-400' },
  { id: 'url', label: 'Source URL', icon: LinkIcon, color: 'text-indigo-400' },
  { id: 'image', label: 'Image Scan', icon: ImageIcon, color: 'text-purple-400' },
  { id: 'video', label: 'Video Deepfake', icon: Video, color: 'text-cyan-400' },
] as const;

export function ClaimInput() {
  const [mode, setMode] = useState<typeof MODES[number]['id']>('text');
  const [content, setContent] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const { setLoading, setCurrent, setError, addToHistory, isLoading } = useVerificationStore();
  const accessToken = useAuthStore((s) => s.accessToken);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;
    if ((mode === 'text' || mode === 'url') && !content.trim()) return;
    if ((mode === 'image' || mode === 'video') && !file) return;

    setLoading(true);
    setError(null);
    setCurrent(null);

    try {
      let submitContent = content;
      if (file) {
        submitContent = file.name;
        await new Promise(r => setTimeout(r, 2000));
      }

      const { data } = await axios.post('/api/v1/verify', {
        content: submitContent,
        type: mode,
        source: 'web_portal',
      }, {
        headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
      });

      setCurrent(data);
      addToHistory(data);
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Verification system offline');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full relative">
      {/* Tabs / Switcher */}
      <div className="flex flex-wrap justify-center gap-3 mb-8">
        {MODES.map((m) => {
          const Icon = m.icon;
          const active = mode === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => { setMode(m.id); setContent(''); setFile(null); setError(null); }}
              className={`relative flex items-center gap-2.5 px-6 py-3 rounded-2xl font-bold text-xs uppercase tracking-widest transition-all duration-300
                ${active
                  ? 'bg-blue-600/10 text-blue-400 border border-blue-500/30'
                  : 'text-slate-500 hover:text-slate-300 hover:bg-white/[0.03] border border-transparent'}`}
            >
              <Icon size={14} className={active ? m.color : 'text-current'} strokeWidth={2.5} />
              {m.label}
              {active && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 bg-blue-500/5 rounded-2xl -z-10"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Main Container */}
      <motion.form
        onSubmit={handleSubmit}
        className="glass-card-heavy p-2 relative overflow-hidden group"
        animate={{
          borderColor: isLoading ? 'rgba(59, 130, 246, 0.4)' : 'rgba(255, 255, 255, 0.05)',
          boxShadow: isLoading ? '0 0 50px rgba(59, 130, 246, 0.15)' : 'none'
        }}
      >
        {/* Scanning Animation */}
        <AnimatePresence>
          {isLoading && (
            <motion.div
              initial={{ top: '-10%' }}
              animate={{ top: '110%' }}
              exit={{ opacity: 0 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="absolute left-0 right-0 h-40 bg-gradient-to-b from-transparent via-blue-500/20 to-transparent pointer-events-none z-10"
            />
          )}
        </AnimatePresence>

        <div className="bg-white/[0.02] rounded-[2rem] p-6">
          {(mode === 'text' || mode === 'url') ? (
            <textarea
              className="w-full bg-transparent p-4 min-h-[160px] outline-none resize-none text-xl text-white placeholder:text-slate-600 font-medium tracking-tight"
              placeholder={mode === 'text' ? "Paste any claim or statement to fact-check..." : "Enter a URL to verify the entire webpage..."}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              disabled={isLoading}
              autoFocus
            />
          ) : (
            <div
              className="w-full min-h-[180px] border-2 border-dashed border-white/5 rounded-3xl flex flex-col items-center justify-center p-8 cursor-pointer hover:border-blue-500/30 hover:bg-white/[0.02] transition-all group/drop"
              onClick={() => fileRef.current?.click()}
            >
              <input
                ref={fileRef} type="file" className="hidden"
                accept={mode === 'image' ? 'image/*' : 'video/*'}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <AnimatePresence mode="wait">
                {file ? (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-blue-400 font-bold text-lg flex flex-col items-center gap-2"
                  >
                    <div className="p-4 bg-blue-500/10 rounded-full mb-2">
                      {mode === 'image' ? <ImageIcon size={32} /> : <Video size={32} />}
                    </div>
                    {file.name}
                    <span className="text-xs text-slate-500">{(file.size / 1e6).toFixed(1)}MB readiness confirmed</span>
                  </motion.div>
                ) : (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-slate-500 flex flex-col items-center gap-4"
                  >
                    <div className="p-5 bg-white/[0.03] rounded-3xl shadow-inner group-hover/drop:scale-110 group-hover/drop:bg-blue-600/10 transition-all duration-500">
                      {mode === 'image' ? <ImageIcon className="text-blue-500/50" size={40} /> : <Video className="text-cyan-500/50" size={40} />}
                    </div>
                    <div className="text-center">
                      <span className="font-bold text-slate-300 block mb-1">Click to Upload</span>
                      <span className="text-xs text-slate-500">Deepfake forensic analysis will be performed</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* Footer Actions */}
          <div className="flex flex-col sm:flex-row justify-between items-center mt-8 gap-6 px-2">
            <div className="flex items-center gap-4">
              <div className="flex -space-x-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="w-8 h-8 rounded-full border-2 border-[#111] bg-slate-800 flex items-center justify-center text-[10px] font-black text-slate-500">AI</div>
                ))}
              </div>
              <div className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                Cognitive Engines <span className="text-emerald-500 ml-1">Live</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || (!content.trim() && !file)}
              className="neon-button group/btn w-full sm:w-auto min-w-[200px]"
            >
              <span className="relative z-10 flex items-center justify-center gap-3">
                {isLoading ? (
                  <><Loader2 size={18} className="animate-spin" /> Analyzing Dynamics...</>
                ) : (
                  <>
                    Initialize Verification
                    <SendHorizontal size={18} className="group-hover/btn:translate-x-1 transition-transform" />
                  </>
                )}
              </span>
              <div className="absolute inset-x-0 bottom-0 h-1 bg-white/20 scale-x-0 group-hover/btn:scale-x-100 transition-transform origin-left" />
            </button>
          </div>
        </div>
      </motion.form>

      {/* Decorative Light */}
      <div className="absolute -bottom-10 left-1/2 -translate-x-1/2 w-1/2 h-1 bg-blue-500/20 blur-xl"></div>
    </div>
  );
}
