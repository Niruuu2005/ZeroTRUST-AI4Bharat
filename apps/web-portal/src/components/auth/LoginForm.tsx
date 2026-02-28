import { useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../../store/authStore';
import { Loader2 } from 'lucide-react';

export function LoginForm({ onSuccess, onSwitchRegister }: { onSuccess?: () => void; onSwitchRegister?: () => void }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const setAuth = useAuthStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { data } = await axios.post('/api/v1/auth/login', { email, password });
      setAuth(data.accessToken, data.user);
      onSuccess?.();
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-8 max-w-md mx-auto">
      <h2 className="text-xl font-bold text-slate-800 mb-6">Sign in</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-1">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            required
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-slate-900 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : null}
          Sign in
        </button>
      </form>
      {onSwitchRegister && (
        <p className="mt-4 text-center text-sm text-slate-500">
          No account?{' '}
          <button type="button" onClick={onSwitchRegister} className="text-blue-600 font-medium hover:underline">
            Register
          </button>
        </p>
      )}
    </div>
  );
}
