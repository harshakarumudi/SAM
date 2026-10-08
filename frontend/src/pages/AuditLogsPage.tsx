import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AuditLogItem, UserRole } from '../types';
import { ScrollText, ShieldAlert, RotateCw, Filter, CheckCircle2, Ban } from 'lucide-react';

interface AuditLogsPageProps {
  userRole: UserRole;
}

export const AuditLogsPage: React.FC<AuditLogsPageProps> = ({ userRole }) => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [severity, setSeverity] = useState<string>('');
  const [eventType, setEventType] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await api.getAuditLogs(severity || undefined, eventType || undefined);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Access to security audit logs denied by backend RBAC.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [severity, eventType]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Security Audit & Compliance Logs</h2>
          <p className="text-xs text-slate-400">
            Immutable tamper-evident security audit trail for forensic incident analysis (Admin only)
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
          title="Refresh audit trail"
        >
          <RotateCw className="w-4 h-4" />
        </button>
      </div>

      {error ? (
        <div className="p-6 bg-red-950/40 border border-red-800 rounded-2xl flex items-start gap-4 text-red-300 text-xs">
          <ShieldAlert className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="font-bold text-sm text-red-200">Backend Access Restriction Enforced</h3>
            <p>{error}</p>
            <p className="text-slate-400 mt-2">
              Viewing security audit trails requires the <span className="font-semibold text-white">ADMIN</span> role. This access denial event has itself been logged in the security database.
            </p>
          </div>
        </div>
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 bg-slate-900 border border-slate-800 rounded-2xl p-4 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Severity:</span>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="">All</option>
                <option value="CRITICAL">Critical</option>
                <option value="WARNING">Warning</option>
                <option value="INFO">Info</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Event Type:</span>
              <input
                type="text"
                placeholder="e.g. SENSOR_SPOOF, UNAUTHORIZED"
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white focus:outline-none focus:border-emerald-500"
              />
            </div>
          </div>

          {/* Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 uppercase font-semibold border-b border-slate-800">
                  <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Event Type</th>
                    <th className="px-4 py-3">Actor</th>
                    <th className="px-4 py-3">Action / Resource</th>
                    <th className="px-4 py-3">Result</th>
                    <th className="px-4 py-3">Severity</th>
                    <th className="px-4 py-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-slate-300">
                  {logs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="px-4 py-3 text-slate-400 font-mono text-[11px] whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 font-mono font-bold text-white text-[11px]">
                        {log.event_type}
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-white font-medium">{log.actor_id}</div>
                        <div className="text-[10px] text-slate-500">{log.actor_type} • {log.ip_address || 'Internal'}</div>
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        <div>{log.action}</div>
                        <div className="text-[10px] font-mono text-slate-500">{log.resource}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                            log.result === 'SUCCESS'
                              ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                              : log.result === 'BLOCKED' || log.result === 'REJECTED'
                              ? 'bg-red-950 text-red-400 border-red-800'
                              : 'bg-amber-950 text-amber-400 border-amber-800'
                          }`}
                        >
                          {log.result}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-[10px] font-bold uppercase ${
                            log.severity === 'CRITICAL'
                              ? 'text-red-400'
                              : log.severity === 'WARNING'
                              ? 'text-amber-400'
                              : 'text-slate-400'
                          }`}
                        >
                          {log.severity}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400 text-[11px] max-w-xs truncate" title={log.details || ''}>
                        {log.details || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
