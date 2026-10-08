import React, { useState } from 'react';
import { api } from '../services/api';
import { AuthUser } from '../types';
import { Sprout, Lock, User, KeyRound, ShieldAlert, AlertCircle } from 'lucide-react';

interface LoginPageProps {
  onLoginSuccess: (user: AuthUser) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const user = await api.login(username, password);
      localStorage.setItem('agri_jwt_token', user.token);
      localStorage.setItem('agri_user', JSON.stringify(user));
      onLoginSuccess(user);
    } catch (err: any) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (uname: string, pwd: string) => {
    setUsername(uname);
    setPassword(pwd);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl text-emerald-400 mb-2">
            <Sprout className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Smart Agriculture Platform</h2>
          <p className="text-sm text-slate-400">Secure Laboratory IoT Examination System</p>
        </div>

        {error && (
          <div className="p-3 bg-red-950/60 border border-red-800 rounded-xl text-red-300 text-sm flex items-start gap-2.5">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Username</label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. admin"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-emerald-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 text-white font-medium text-sm rounded-xl transition-colors shadow-lg shadow-emerald-950/50 flex items-center justify-center gap-2"
          >
            <KeyRound className="w-4 h-4" />
            <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
          </button>
        </form>

        <div className="border-t border-slate-800 pt-5 space-y-3">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider text-center">
            Demo Credentials for Evaluation
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin('admin', 'Admin@Secure2026!')}
              className="px-2 py-1.5 rounded-lg bg-purple-950/40 hover:bg-purple-900/60 border border-purple-800/60 text-purple-300 text-xs font-medium transition-colors text-center"
            >
              Admin
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('operator', 'Operator@Secure2026!')}
              className="px-2 py-1.5 rounded-lg bg-blue-950/40 hover:bg-blue-900/60 border border-blue-800/60 text-blue-300 text-xs font-medium transition-colors text-center"
            >
              Operator
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('viewer', 'Viewer@Secure2026!')}
              className="px-2 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 border border-slate-700/60 text-slate-300 text-xs font-medium transition-colors text-center"
            >
              Viewer
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2 p-3 bg-slate-950 rounded-xl text-slate-400 text-xs border border-slate-800/80">
          <ShieldAlert className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>Protected with Argon2/Bcrypt hash, HS256 JWT, and IP rate limiting.</span>
        </div>
      </div>
    </div>
  );
};
