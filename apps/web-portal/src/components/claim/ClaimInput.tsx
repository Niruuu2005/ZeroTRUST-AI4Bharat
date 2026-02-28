import { useState, useRef } from 'react';
import axios from 'axios';
import { FileText, Link as LinkIcon, Image as ImageIcon, Video, Loader2 } from 'lucide-react';
import { useVerificationStore } from '../../store/verificationStore';
import { useAuthStore } from '../../store/authStore';

const MODES = [
  { id: 'text', label: 'Text Claim', icon: FileText },
  { id: 'url', label: 'Webpage URL', icon: LinkIcon },
  { id: 'image', label: 'Image', icon: ImageIcon },
  { id: 'video', label: 'Video', icon: Video },
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
        // Prototype mock: in real app, GET presigned URL → PUT → set submitContent = S3 Key
        submitContent = file.name;
        await new Promise(r => setTimeout(r, 1000)); // fake upload delay
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
      setError(err.response?.data?.error || err.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      {/* Tabs */}
      <div className="flex gap-2 p-1.5 bg-slate-100 rounded-2xl mb-4 max-w-fit mx-auto glass-card shadow-none border-0">
        {MODES.map((m) => {
          const Icon = m.icon;
          const active = mode === m.id;
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => { setMode(m.id); setContent(''); setFile(null); setError(null); }}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-300
                ${active 
                  ? 'bg-white text-blue-700 shadow-sm ring-1 ring-slate-200' 
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-200/50'}`}
            >
              <Icon size={16} strokeWidth={active ? 2.5 : 2} />
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="glass-card p-4 relative group transition-all duration-300 hover:shadow-2xl hover:shadow-slate-200/60 overflow-hidden">
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-50 to-indigo-50/50 opacity-0 group-hover:opacity-100 transition-opacity duration-700 -z-10" />

        {(mode === 'text' || mode === 'url') ? (
          <textarea
            className="w-full bg-transparent p-4 min-h-[120px] outline-none resize-none text-lg text-slate-800 placeholder:text-slate-400 font-medium"
            placeholder={mode === 'text' ? "Paste a controversial claim, news headline, or statement to verify..." : "Paste a URL to an article or news report..."}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={isLoading}
            autoFocus
          />
        ) : (
          <div 
            className="w-full min-h-[140px] border-2 border-dashed border-slate-300 rounded-xl flex flex-col items-center justify-center p-6 cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-colors group/drop"
            onClick={() => fileRef.current?.click()}
          >
            <input 
              ref={fileRef} type="file" className="hidden" 
              accept={mode === 'image' ? 'image/*' : 'video/*'}
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            {file ? (
              <div className="text-blue-700 font-semibold text-lg flex items-center gap-2">
                <Icon className="text-blue-500" /> {file.name} ({(file.size / 1e6).toFixed(1)}MB)
              </div>
            ) : (
              <div className="text-slate-500 flex flex-col items-center gap-3">
                <div className="p-4 bg-white rounded-full shadow-sm group-hover/drop:scale-110 transition-transform">
                  {mode === 'image' ? <ImageIcon className="text-blue-500" size={32} /> : <Video className="text-indigo-500" size={32} />}
                </div>
                <span className="font-medium">Click to browse or drag {mode} file here</span>
                <span className="text-xs text-slate-400">Deepfake forensic analysis supported</span>
              </div>
            )}
          </div>
        )}

        {/* Footer Actions */}
        <div className="flex justify-between items-center mt-4 border-t border-slate-100 pt-4 px-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Agents Ready
          </div>
          
          <button
            type="submit"
            disabled={isLoading || (!content.trim() && !file)}
            className="relative overflow-hidden group/btn bg-slate-900 text-white px-8 py-3.5 rounded-xl font-bold text-sm tracking-wide transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:-translate-y-0.5"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300"></div>
            <span className="relative flex items-center gap-2">
              {isLoading ? (
                <><Loader2 size={18} className="animate-spin" /> Verifying (avg 4s)...</>
              ) : (
                <>Run Verification &rarr;</>
              )}
            </span>
          </button>
        </div>
      </form>
    </div>
  );
}

// Ensure icon variables exist for JSX mapping trick above
const Icon = ({ className }: {className?: string}) => <FileText className={className} />;
