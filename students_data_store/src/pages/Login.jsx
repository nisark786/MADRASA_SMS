import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { GraduationCap, Mail, Lock, LogIn } from 'lucide-react';

const TEST_ACCOUNTS = [
  { email: 'admin@example.com', password: 'admin123' },
  { email: 'sara@example.com', password: 'sara1234' },
  { email: 'john@example.com', password: 'john1234' },
];

export default function Login() {
  const { login } = useAuthStore();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(form.email, form.password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fillTestCredentials = (email, password) => {
    setForm({ email, password });
    setError('');
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50/50 font-sans p-4 antialiased">
      <div className="bg-white border border-gray-200 rounded-3xl p-10 w-full max-w-[420px] shadow-[0_8px_40px_rgba(0,0,0,0.04)] ring-1 ring-gray-950/5 relative overflow-hidden">
        
        {/* Subtle decorative background */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-40 h-40 bg-indigo-50 rounded-full blur-3xl opacity-60" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-40 h-40 bg-purple-50 rounded-full blur-3xl opacity-60" />

        <div className="text-center mb-10 relative">
          <div className="bg-indigo-600 inline-flex p-3 rounded-2xl shadow-xl shadow-indigo-100 mb-4">
            <GraduationCap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight mb-1">Students DS</h1>
          <p className="text-sm text-gray-400 font-medium">Management & Analytics Platform</p>
        </div>

        <form className="flex flex-col gap-5 relative" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-2">
            <label className="text-[0.8rem] font-bold text-gray-700 uppercase tracking-wider ml-1" htmlFor="email">Email</label>
            <div className="relative group">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
              <input
                id="email"
                type="email"
                placeholder="name@example.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full pl-11 pr-4 py-3 bg-gray-50/50 border border-gray-200 rounded-xl text-gray-900 text-sm font-sans outline-none transition-all placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                required
                autoFocus
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-[0.8rem] font-bold text-gray-700 uppercase tracking-wider ml-1" htmlFor="password">Password</label>
            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-gray-400 group-focus-within:text-indigo-500 transition-colors" />
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full pl-11 pr-4 py-3 bg-gray-50/50 border border-gray-200 rounded-xl text-gray-900 text-sm font-sans outline-none transition-all placeholder:text-gray-400 focus:bg-white focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10"
                required
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50/80 border border-red-100 text-red-700 px-4 py-3 rounded-xl text-[0.8125rem] font-medium animate-in fade-in slide-in-from-top-2 duration-200">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full py-3.5 bg-indigo-600 border-none rounded-xl text-white text-[0.9375rem] font-bold shadow-lg shadow-indigo-200 cursor-pointer transition-all flex items-center justify-center gap-2.5 hover:bg-indigo-700 hover:shadow-indigo-300 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed mt-3 mb-2"
            disabled={loading}
          >
            {loading ? (
              <span className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <LogIn className="w-[18px] h-[18px]" strokeWidth={2.5} />
                Sign In
              </>
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-100 relative">
          <p className="text-gray-400 text-[0.7rem] font-bold uppercase tracking-[0.1em] text-center mb-4">Click to Fill Credentials</p>
          <div className="grid grid-cols-1 gap-2">
            {TEST_ACCOUNTS.map((account) => (
              <button
                key={account.email}
                type="button"
                className="flex items-center justify-center bg-gray-50 border border-gray-200 rounded-xl px-4 py-2 text-[0.8rem] text-gray-500 font-bold hover:bg-indigo-50 hover:border-indigo-100 hover:text-indigo-600 transition-all"
                onClick={() => fillTestCredentials(account.email, account.password)}
              >
                <code className="font-mono font-medium">{account.email}</code>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
