import React from 'react';
import { UserRole } from '../types';
import {
  LayoutDashboard,
  Activity,
  Sliders,
  Power,
  Cpu,
  Bell,
  ScrollText,
  ShieldAlert
} from 'lucide-react';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  userRole: UserRole;
  alertCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  userRole,
  alertCount,
}) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, minRole: 'VIEWER' },
    { id: 'sensors', label: 'Sensors', icon: Activity, minRole: 'VIEWER' },
    { id: 'thresholds', label: 'Thresholds', icon: Sliders, minRole: 'VIEWER', adminOnlyNotice: true },
    { id: 'actuators', label: 'Actuator Control', icon: Power, minRole: 'VIEWER', opOnly: true },
    { id: 'devices', label: 'Device Management', icon: Cpu, minRole: 'VIEWER', adminOnly: true },
    { id: 'alerts', label: 'Alerts', icon: Bell, minRole: 'VIEWER', badge: alertCount },
    { id: 'audit', label: 'Audit Logs', icon: ScrollText, minRole: 'ADMIN', badgeColor: 'bg-purple-900 text-purple-300' },
  ];

  return (
    <aside className="w-64 bg-slate-900/90 border-r border-slate-800 flex flex-col justify-between p-4 min-h-[calc(100vh-73px)]">
      <div className="space-y-1">
        <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Monitoring & Operations
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          const isRestricted = item.minRole === 'ADMIN' && userRole !== 'ADMIN';

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>

              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-red-950 text-red-400 border border-red-800">
                  {item.badge}
                </span>
              )}

              {isRestricted && (
                <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-purple-950/60 text-purple-400 border border-purple-800/50">
                  Admin
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-400 space-y-2">
        <div className="flex items-center gap-1.5 text-slate-300 font-semibold">
          <ShieldAlert className="w-4 h-4 text-emerald-400" />
          <span>Security Architecture</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-400">
          Backend RBAC and Cryptographic ACLs active. Unauthorized API or MQTT invocations are permanently audited.
        </p>
      </div>
    </aside>
  );
};
