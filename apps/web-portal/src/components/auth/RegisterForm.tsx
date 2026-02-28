import { useState } from 'react';
import axios from 'axios';
import { useAuthStore } from '../../store/authStore';
import { Loader2 } from 'lucide-react';

export function RegisterForm({ onSuccess, onSwitchLogin }: { onSuccess?: () => void; onSwitchLogin?: () => void }) {
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
      await axios.post('/api/v1/auth/register', { email, password });
      const { data } = await axios.post('/api/v1/auth/login', { email, password });
      setAuth(data.accessToken, data.user);
      onSuccess?.();
    } catch (err: any) {
      setError(err.response?.data?.error || err.response?.data?.details?.fieldErrors?.password?.[0] || err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-8 max-w-md mx-auto">
      <h2 className="text-xl font-bold text-slate-800 mb-6">Create account</h2>
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
          <label className="block text-sm font-medium text-slate-600 mb-1">Password (min 8 characters)</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            minLength={8}
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
          Register
        </button>
      </form>
      {onSwitchLogin && (
        <p className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{' '}
          <button type="button" onClick={onSwitchLogin} className="text-blue-600 font-medium hover:underline">
            Sign in
          </button>
        </p>
      )}
    </div>
  );
}
