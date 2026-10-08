import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { DeviceItem, UserRole } from '../types';
import { Cpu, ShieldCheck, ShieldAlert, Plus, Ban, CheckCircle2, AlertCircle } from 'lucide-react';

interface DevicesPageProps {
  userRole: UserRole;
}

export const DevicesPage: React.FC<DevicesPageProps> = ({ userRole }) => {
  const [devices, setDevices] = useState<DeviceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const [newDevice, setNewDevice] = useState({
    id: '',
    device_name: '',
    device_type: 'soil_moisture',
    auth_secret: '',
    farm_id: 'farm_1',
  });

  const isAdmin = userRole === 'ADMIN';

  const fetchDevices = async () => {
    try {
      const data = await api.getDevices();
      setDevices(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleSuspend = async (deviceId: string) => {
    setStatusMsg(null);
    try {
      await api.suspendDevice(deviceId);
      setStatusMsg({
        type: 'success',
        text: `Device '${deviceId}' has been suspended. Incoming telemetry from this node will now be rejected.`,
      });
      fetchDevices();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Suspension failed' });
    }
  };

  const handleActivate = async (deviceId: string) => {
    setStatusMsg(null);
    try {
      await api.activateDevice(deviceId);
      setStatusMsg({
        type: 'success',
        text: `Device '${deviceId}' reactivated successfully.`,
      });
      fetchDevices();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Activation failed' });
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);
    try {
      await api.registerDevice(newDevice);
      setStatusMsg({
        type: 'success',
        text: `Device '${newDevice.id}' successfully provisioned and registered in database.`,
      });
      setShowModal(false);
      setNewDevice({
        id: '',
        device_name: '',
        device_type: 'soil_moisture',
        auth_secret: '',
        farm_id: 'farm_1',
      });
      fetchDevices();
    } catch (err: any) {
      setStatusMsg({ type: 'error', text: err.message || 'Device registration failed' });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">IoT Hardware Device Management</h2>
          <p className="text-xs text-slate-400">
            Cryptographic device authentication, node authorization, and revocation management
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => setShowModal(true)}
            className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors flex items-center gap-1.5 shadow-lg shadow-emerald-950/50"
          >
            <Plus className="w-4 h-4" />
            <span>Register Device</span>
          </button>
        )}
      </div>

      {statusMsg && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-start gap-3 ${
            statusMsg.type === 'success'
              ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
              : 'bg-red-950/40 border-red-800 text-red-300'
          }`}
        >
          {statusMsg.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          )}
          <span>{statusMsg.text}</span>
        </div>
      )}

      {/* Device Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Hardware ID</th>
                <th className="px-4 py-3">Device Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Authorization Status</th>
                <th className="px-4 py-3">Last Heartbeat</th>
                <th className="px-4 py-3 text-right">Administrative Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {devices.map((dev) => (
                <tr key={dev.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3.5 font-mono text-emerald-400 font-semibold">{dev.id}</td>
                  <td className="px-4 py-3.5 font-medium text-white">{dev.device_name}</td>
                  <td className="px-4 py-3.5 capitalize">{dev.device_type.replace('_', ' ')}</td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                        dev.status === 'active'
                          ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                          : dev.status === 'suspended'
                          ? 'bg-red-950 text-red-400 border-red-800'
                          : 'bg-slate-950 text-slate-400 border-slate-800'
                      }`}
                    >
                      {dev.status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-slate-400">
                    {dev.last_seen ? new Date(dev.last_seen).toLocaleTimeString() : 'Offline'}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    {isAdmin ? (
                      dev.status === 'active' ? (
                        <button
                          onClick={() => handleSuspend(dev.id)}
                          className="px-2.5 py-1 rounded-lg bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/60 text-[11px] font-medium transition-colors flex items-center gap-1 ml-auto"
                        >
                          <Ban className="w-3 h-3" />
                          <span>Suspend Node</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(dev.id)}
                          className="px-2.5 py-1 rounded-lg bg-emerald-950/40 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-800/60 text-[11px] font-medium transition-colors flex items-center gap-1 ml-auto"
                        >
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Reactivate</span>
                        </button>
                      )
                    ) : (
                      <span className="text-[10px] text-slate-500 italic">Admin Only</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal for Device Registration */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Cpu className="w-5 h-5 text-emerald-400" />
                Provision IoT Hardware Node
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                ✕
              </button>
            </div>

            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-300 mb-1">Hardware Device ID</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. DEV_SOIL_02"
                  value={newDevice.id}
                  onChange={(e) => setNewDevice({ ...newDevice, id: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">Friendly Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Field Section 2 Moisture Sensor"
                  value={newDevice.device_name}
                  onChange={(e) => setNewDevice({ ...newDevice, device_name: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">Device Subsystem Type</label>
                <select
                  value={newDevice.device_type}
                  onChange={(e) => setNewDevice({ ...newDevice, device_type: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="soil_moisture">Soil Moisture Sensor</option>
                  <option value="environmental">Greenhouse Environmental (Temp/Humidity)</option>
                  <option value="water_level">Water Level Reservoir Sensor</option>
                  <option value="actuator">Actuator Controller</option>
                </select>
              </div>

              <div>
                <label className="block text-xs text-slate-300 mb-1">Pre-Shared Auth Secret</label>
                <input
                  type="text"
                  required
                  placeholder="Cryptographic key / secret token"
                  value={newDevice.auth_secret}
                  onChange={(e) => setNewDevice({ ...newDevice, auth_secret: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 font-mono text-xs"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950/50"
                >
                  Provision Device
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
