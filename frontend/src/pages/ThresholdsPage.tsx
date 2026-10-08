import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Thresholds, UserRole } from '../types';
import { Sliders, Save, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';

interface ThresholdsPageProps {
  userRole: UserRole;
}

export const ThresholdsPage: React.FC<ThresholdsPageProps> = ({ userRole }) => {
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);
  const [formData, setFormData] = useState({
    soil_moisture_min: 30.0,
    soil_moisture_target: 60.0,
    temperature_min: 18.0,
    temperature_max: 32.0,
    humidity_min: 40.0,
    humidity_max: 85.0,
    water_level_safe_min: 15.0,
    max_pump_runtime_seconds: 600,
  });
  const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const isAdmin = userRole === 'ADMIN';

  const fetchThresholds = async () => {
    try {
      const data = await api.getThresholds();
      setThresholds(data);
      setFormData({
        soil_moisture_min: data.soil_moisture_min,
        soil_moisture_target: data.soil_moisture_target,
        temperature_min: data.temperature_min,
        temperature_max: data.temperature_max,
        humidity_min: data.humidity_min,
        humidity_max: data.humidity_max,
        water_level_safe_min: data.water_level_safe_min,
        max_pump_runtime_seconds: data.max_pump_runtime_seconds,
      });
    } catch (e: any) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchThresholds();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: parseFloat(value) || 0,
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);

    // Client-side validation
    if (formData.soil_moisture_target <= formData.soil_moisture_min) {
      setStatusMsg({
        type: 'error',
        text: 'Validation Error: Target soil moisture must be strictly greater than minimum threshold.',
      });
      return;
    }

    if (formData.temperature_max <= formData.temperature_min) {
      setStatusMsg({
        type: 'error',
        text: 'Validation Error: Maximum temperature must be strictly greater than minimum temperature.',
      });
      return;
    }

    setLoading(true);
    try {
      await api.updateThresholds('farm_1', formData);
      setStatusMsg({
        type: 'success',
        text: 'Thresholds successfully updated and recorded in the security audit log.',
      });
      fetchThresholds();
    } catch (err: any) {
      setStatusMsg({
        type: 'error',
        text: err.message || 'Failed to update thresholds.',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">Farm Automation Threshold Configuration</h2>
        <p className="text-xs text-slate-400">
          Configure physical trigger parameters for automatic irrigation and greenhouse environmental control
        </p>
      </div>

      {!isAdmin && (
        <div className="p-4 bg-amber-950/40 border border-amber-800/80 rounded-2xl flex items-start gap-3 text-amber-300 text-xs">
          <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold uppercase tracking-wider">Read-Only Mode (RBAC Enforced)</div>
            <p>
              Your current account role is <span className="font-semibold underline">{userRole}</span>. Threshold modification is strictly restricted to <span className="font-semibold text-white">ADMIN</span> accounts. Any direct API calls to modify thresholds will return HTTP 403 Forbidden and create an audit event.
            </p>
          </div>
        </div>
      )}

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

      <form onSubmit={handleSave} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Soil Moisture */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              Soil Moisture & Irrigation Setpoints
            </h3>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Irrigation Activation Trigger (Min %)
              </label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="100"
                name="soil_moisture_min"
                value={formData.soil_moisture_min}
                onChange={handleChange}
                disabled={!isAdmin}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <span className="text-[10px] text-slate-500">Irrigation starts when soil drops below this value</span>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Irrigation Safe Cutoff Target (%)
              </label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="100"
                name="soil_moisture_target"
                value={formData.soil_moisture_target}
                onChange={handleChange}
                disabled={!isAdmin}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <span className="text-[10px] text-slate-500">Irrigation stops when soil reaches this value</span>
            </div>
          </div>

          {/* Temperature */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sliders className="w-4 h-4 text-rose-400" />
              Greenhouse Climate Thresholds
            </h3>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Heater Trigger Temperature (°C)
              </label>
              <input
                type="number"
                step="0.5"
                min="-10"
                max="50"
                name="temperature_min"
                value={formData.temperature_min}
                onChange={handleChange}
                disabled={!isAdmin}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <span className="text-[10px] text-slate-500">Radiant heater activates below this temperature</span>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Ventilation Fan Trigger (°C)
              </label>
              <input
                type="number"
                step="0.5"
                min="-10"
                max="50"
                name="temperature_max"
                value={formData.temperature_max}
                onChange={handleChange}
                disabled={!isAdmin}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <span className="text-[10px] text-slate-500">Cooling fan activates above this temperature</span>
            </div>
          </div>

          {/* Humidity & Reservoir Safety */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              Humidity Range
            </h3>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Maximum Safe Humidity (%)</label>
              <input
                type="number"
                step="0.5"
                min="0"
                max="100"
                name="humidity_max"
                value={formData.humidity_max}
                onChange={handleChange}
                disabled={!isAdmin}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <span className="text-[10px] text-slate-500">Ventilation fan starts if humidity exceeds this level</span>
            </div>
          </div>

          {/* Safety Interlocks */}
          <div className="space-y-4 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sliders className="w-4 h-4 text-blue-400" />
              Safety Interlock Parameters
            </h3>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Water Reservoir Safety Minimum Cutoff (%)
              </label>
              <input
                type="number"
                step="0.5"
                min="5"
                max="50"
                name="water_level_safe_min"
                value={formData.water_level_safe_min}
                onChange={handleChange}
                disabled={!isAdmin}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <span className="text-[10px] text-rose-400">Pumps are completely locked out below this reservoir level</span>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">
                Max Continuous Pump Runtime (Seconds)
              </label>
              <input
                type="number"
                min="30"
                max="3600"
                name="max_pump_runtime_seconds"
                value={formData.max_pump_runtime_seconds}
                onChange={handleChange}
                disabled={!isAdmin}
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-emerald-500 disabled:opacity-50"
              />
              <span className="text-[10px] text-slate-500">Automatic cutoff to prevent motor burnout</span>
            </div>
          </div>
        </div>

        {isAdmin && (
          <div className="flex justify-end pt-4 border-t border-slate-800">
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-emerald-800 text-white font-medium text-xs transition-colors flex items-center gap-2 shadow-lg shadow-emerald-950/50"
            >
              <Save className="w-4 h-4" />
              <span>{loading ? 'Saving Thresholds...' : 'Save Configuration'}</span>
            </button>
          </div>
        )}
      </form>
    </div>
  );
};
