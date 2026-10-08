import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AlertItem, UserRole } from '../types';
import { Bell, AlertTriangle, ShieldAlert, CheckCircle2, RotateCw } from 'lucide-react';

interface AlertsPageProps {
  userRole: UserRole;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ userRole }) => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [filterSeverity, setFilterSeverity] = useState<string>('');
  const [onlyActive, setOnlyActive] = useState<boolean>(true);
  const [loading, setLoading] = useState(true);

  const canResolve = userRole === 'ADMIN' || userRole === 'OPERATOR';

  const fetchAlerts = async () => {
    try {
      const data = await api.getAlerts(onlyActive ? false : undefined, filterSeverity || undefined);
      setAlerts(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [onlyActive, filterSeverity]);

  const handleResolve = async (id: number) => {
    try {
      await api.resolveAlert(id);
      fetchAlerts();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Security & Operational Alerts</h2>
          <p className="text-xs text-slate-400">
            Real-time multi-tier notification feed for anomaly detection and safety interlocks
          </p>
        </div>

        <button
          onClick={fetchAlerts}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
          title="Refresh alerts"
        >
          <RotateCw className="w-4 h-4" />
        </button>
      </div>

      {/* Filter Controls */}
      <div className="flex flex-wrap items-center gap-3 bg-slate-900 border border-slate-800 rounded-2xl p-4 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium">Filter Severity:</span>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white focus:outline-none focus:border-emerald-500"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>
        </div>

        <label className="flex items-center gap-2 text-slate-300 cursor-pointer ml-auto">
          <input
            type="checkbox"
            checked={onlyActive}
            onChange={(e) => setOnlyActive(e.target.checked)}
            className="rounded border-slate-700 text-emerald-500 focus:ring-emerald-500 bg-slate-950"
          />
          <span>Show Unresolved Only</span>
        </label>
      </div>

      {/* Alerts Feed */}
      <div className="space-y-3">
        {alerts.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500 bg-slate-900 border border-slate-800 rounded-2xl">
            No alerts match the selected criteria.
          </div>
        ) : (
          alerts.map((al) => (
            <div
              key={al.id}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex items-start justify-between gap-4 shadow-sm"
            >
              <div className="space-y-2">
                <div className="flex items-center gap-2.5">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                      al.severity === 'CRITICAL'
                        ? 'bg-red-950 text-red-400 border-red-800'
                        : al.severity === 'WARNING'
                        ? 'bg-amber-950 text-amber-400 border-amber-800'
                        : 'bg-blue-950 text-blue-400 border-blue-800'
                    }`}
                  >
                    {al.severity}
                  </span>

                  <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 border border-slate-700 uppercase font-mono">
                    {al.category}
                  </span>

                  <h3 className="text-sm font-bold text-white">{al.title}</h3>
                  <span className="text-[11px] text-slate-500">
                    {new Date(al.created_at).toLocaleString()}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{al.message}</p>

                {al.device_id && (
                  <div className="text-[11px] text-slate-500 font-mono">Node ID: {al.device_id}</div>
                )}
              </div>

              {!al.resolved && canResolve && (
                <button
                  onClick={() => handleResolve(al.id)}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition-colors flex-shrink-0"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Mark Resolved</span>
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
