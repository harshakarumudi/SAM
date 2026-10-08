import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { SensorStatus } from '../types';
import { Activity, ShieldCheck, Clock, CheckCircle2, AlertOctagon } from 'lucide-react';

export const SensorsPage: React.FC = () => {
  const [sensors, setSensors] = useState<SensorStatus[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchSensors = async () => {
    try {
      const data = await api.getSensors();
      setSensors(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSensors();
    const interval = setInterval(fetchSensors, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Sensor Telemetry & Monitoring</h2>
        <p className="text-xs text-slate-400">
          Hardware node status, live environmental measurements, and multi-layer validation
        </p>
      </div>

      {/* Physical Limits Reference Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
          <ShieldCheck className="w-4 h-4" />
          <span>Ingestion Validation Rules & Physical Boundary Protections</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
            <span className="text-slate-400 block text-[10px]">Soil Moisture</span>
            <span className="text-slate-200 font-bold">0.0% - 100.0%</span>
            <span className="text-[10px] text-slate-500 block">Max Jump: 40%</span>
          </div>
          <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
            <span className="text-slate-400 block text-[10px]">Temperature</span>
            <span className="text-slate-200 font-bold">-10.0°C - 60.0°C</span>
            <span className="text-[10px] text-slate-500 block">Max Jump: 25°C</span>
          </div>
          <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
            <span className="text-slate-400 block text-[10px]">Humidity</span>
            <span className="text-slate-200 font-bold">0.0% - 100.0%</span>
            <span className="text-[10px] text-slate-500 block">Max Jump: 45%</span>
          </div>
          <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800">
            <span className="text-slate-400 block text-[10px]">Water Level</span>
            <span className="text-slate-200 font-bold">0.0% - 100.0%</span>
            <span className="text-[10px] text-slate-500 block">Safety Cutoff: 15%</span>
          </div>
        </div>
      </div>

      {/* Sensors Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Connected Field Sensor Nodes
          </h3>
          <span className="text-xs text-slate-400">Total: {sensors.length} Nodes</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-semibold border-b border-slate-800">
              <tr>
                <th className="px-4 py-3">Device Node</th>
                <th className="px-4 py-3">Sensor Type</th>
                <th className="px-4 py-3">Current Telemetry</th>
                <th className="px-4 py-3">Safety Status</th>
                <th className="px-4 py-3">Node State</th>
                <th className="px-4 py-3">Last Telemetry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {sensors.map((sensor) => (
                <tr key={sensor.device_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3.5">
                    <div className="font-semibold text-white">{sensor.device_name}</div>
                    <div className="text-[10px] font-mono text-slate-500">{sensor.device_id}</div>
                  </td>
                  <td className="px-4 py-3.5 capitalize font-medium">{sensor.sensor_type.replace('_', ' ')}</td>
                  <td className="px-4 py-3.5">
                    <span className="text-sm font-black text-white">
                      {sensor.current_value !== null ? `${sensor.current_value}${sensor.unit}` : 'N/A'}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${
                        sensor.state === 'CRITICAL'
                          ? 'bg-red-950 text-red-400 border-red-800'
                          : sensor.state === 'WARNING'
                          ? 'bg-amber-950 text-amber-400 border-amber-800'
                          : 'bg-emerald-950 text-emerald-400 border-emerald-800'
                      }`}
                    >
                      {sensor.state}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 font-medium">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      {sensor.device_status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-slate-400">
                    {sensor.last_seen ? new Date(sensor.last_seen).toLocaleTimeString() : 'Never'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
