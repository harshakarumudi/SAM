import React from 'react';
import { AuthUser } from '../types';
import { Sprout, ShieldCheck, LogOut, User } from 'lucide-react';

interface NavbarProps {
  user: AuthUser;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout }) => {
  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-900/60 text-purple-300 border-purple-500';
      case 'OPERATOR':
        return 'bg-blue-900/60 text-blue-300 border-blue-500';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-600';
    }
  };

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between sticky top-0 z-50">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400">
          <Sprout className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            Smart Agriculture Monitoring System
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1 font-normal">
              <ShieldCheck className="w-3 h-3" /> Secure IoT Platform
            </span>
          </h1>
          <p className="text-xs text-slate-400">Sector 4B • Automated Farm Environment</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg">
          <User className="w-4 h-4 text-slate-400" />
          <span className="text-slate-200 font-medium">{user.username}</span>
          <span className={`text-xs px-2 py-0.5 rounded border font-semibold ${getRoleBadgeColor(user.role)}`}>
            {user.role}
          </span>
        </div>

        <button
          onClick={onLogout}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-800/50 text-sm transition-colors"
          title="Sign out of system"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>
    </header>
  );
};
