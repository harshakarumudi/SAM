import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ActuatorItem, UserRole } from '../types';
import { Power, ShieldAlert, CheckCircle2, AlertCircle, Play, Square, Info } from 'lucide-react';

interface ActuatorsPageProps {
  userRole: UserRole;
}

export const ActuatorsPage: React.FC<ActuatorsPageProps> = ({ userRole }) => {
  const [actuators, setActuators] = useState<ActuatorItem[]>([]);
  const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const fetchActuators = async () => {
    try {
      const data = await api.getActuators();
      setActuators(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchActuators();
    const interval = setInterval(fetchActuators, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleCommand = async (actuatorId: string, cmd: 'START' | 'STOP') => {
    setActionMsg(null);
    setLoadingId(`${actuatorId}-${cmd}`);

    try {
      const res = await api.executeActuatorCommand(actuatorId, cmd, `Manual operator override from UI`);
      setActionMsg({
        type: 'success',
        text: `Command ${cmd} on ${actuatorId} successfully executed and audited.`,
      });
      fetchActuators();
    } catch (err: any) {
      setActionMsg({
        type: 'error',
        text: `Backend Rejection: ${err.message}`,
      });
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Actuator Control & Manual Override</h2>
        <p className="text-xs text-slate-400">
          Supervisory control of irrigation pumps, ventilation fans, and greenhouse radiant heaters
        </p>
      </div>

      {userRole === 'VIEWER' && (
        <div className="p-4 bg-purple-950/40 border border-purple-800/80 rounded-2xl flex items-start gap-3 text-purple-300 text-xs">
          <ShieldAlert className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold uppercase tracking-wider">Viewer RBAC Protection Active</div>
            <p>
              Your account has the <span className="font-semibold underline">VIEWER</span> role. Viewers are strictly prohibited from issuing actuator commands. If you click Start/Stop, the backend will reject the request with HTTP 403 Forbidden and record an unauthorized access attempt in the audit log.
            </p>
          </div>
        </div>
      )}

      {actionMsg && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-start gap-3 ${
            actionMsg.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
              : 'bg-red-950/40 border-red-800 text-red-300'
          }`}
        >
          {actionMsg.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          )}
          <span>{actionMsg.text}</span>
        </div>
      )}

      {/* Actuator Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {actuators.map((actuator) => {
          const isOn = actuator.status === 'ON';

          return (
            <div
              key={actuator.id}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2.5 rounded-xl bg-slate-800 text-slate-300">
                    <Power className={`w-5 h-5 ${isOn ? 'text-emerald-400' : 'text-slate-500'}`} />
                  </div>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-bold border uppercase ${
                      isOn
                        ? 'bg-emerald-950 text-emerald-400 border-emerald-800 animate-pulse'
                        : 'bg-slate-950 text-slate-500 border-slate-800'
                    }`}
                  >
                    {actuator.status}
                  </span>
                </div>

                <div>
                  <h3 className="text-base font-bold text-white capitalize">
                    {actuator.actuator_type} Controller
                  </h3>
                  <div className="text-[11px] font-mono text-slate-500">{actuator.id}</div>
                </div>

                <div className="space-y-1.5 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
                  <div className="flex justify-between">
                    <span>Control Mode:</span>
                    <span className="text-slate-200 font-semibold">{actuator.mode}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Device Node:</span>
                    <span className="text-slate-200 font-mono text-[11px]">{actuator.device_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last Activation:</span>
                    <span className="text-slate-200 text-[11px]">
                      {actuator.last_activated_at
                        ? new Date(actuator.last_activated_at).toLocaleTimeString()
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => handleCommand(actuator.id, 'START')}
                  disabled={loadingId === `${actuator.id}-START`}
                  className="py-2.5 px-3 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 border border-emerald-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Start</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleCommand(actuator.id, 'STOP')}
                  disabled={loadingId === `${actuator.id}-STOP`}
                  className="py-2.5 px-3 rounded-xl bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/30 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <Square className="w-3.5 h-3.5" />
                  <span>Stop</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
