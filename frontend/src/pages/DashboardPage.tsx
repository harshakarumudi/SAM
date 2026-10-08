import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { SensorStatus, ActuatorItem, WeatherInfo, AlertItem, Thresholds } from '../types';
import {
  Droplets,
  Thermometer,
  CloudRain,
  Waves,
  Power,
  Sun,
  ShieldCheck,
  AlertTriangle,
  RotateCw,
  Wind,
  Flame
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const [sensors, setSensors] = useState<SensorStatus[]>([]);
  const [actuators, setActuators] = useState<ActuatorItem[]>([]);
  const [weather, setWeather] = useState<WeatherInfo | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [thresholds, setThresholds] = useState<Thresholds | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  const fetchData = async () => {
    try {
      const [sData, aData, wData, alData, tData] = await Promise.all([
        api.getSensors().catch(() => []),
        api.getActuators().catch(() => []),
        api.getWeather().catch(() => null),
        api.getAlerts(false).catch(() => []),
        api.getThresholds().catch(() => null),
      ]);
      setSensors(sData);
      setActuators(aData);
      setWeather(wData);
      setAlerts(alData);
      setThresholds(tData);
      setLastRefreshed(new Date());
    } catch (e) {
      console.error('Error fetching dashboard data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000); // 3-second auto-poll for live demonstration
    return () => clearInterval(interval);
  }, []);

  const getSensorByType = (type: string) => {
    return sensors.find((s) => s.sensor_type === type);
  };

  const getActuatorByType = (type: string) => {
    return actuators.find((a) => a.actuator_type === type);
  };

  const soilSensor = getSensorByType('soil_moisture');
  const tempSensor = getSensorByType('temperature');
  const humSensor = getSensorByType('humidity');
  const waterSensor = getSensorByType('water_level');

  const pump = getActuatorByType('pump');
  const fan = getActuatorByType('fan');
  const heater = getActuatorByType('heater');

  const getStateBadge = (state: string) => {
    switch (state) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-950 text-red-400 border border-red-800">CRITICAL</span>;
      case 'WARNING':
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-950 text-amber-400 border border-amber-800">WARNING</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">NORMAL</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Agricultural Telemetry Overview</h2>
          <p className="text-xs text-slate-400">
            Real-time multi-sensor telemetry, weather, and actuator automation
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">
            Updated: {lastRefreshed.toLocaleTimeString()}
          </span>
          <button
            onClick={fetchData}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
            title="Manual refresh"
          >
            <RotateCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 4 Core Sensor Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Soil Moisture */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Droplets className="w-5 h-5" />
            </div>
            {getStateBadge(soilSensor?.state || 'NORMAL')}
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Soil Moisture</div>
            <div className="text-2xl font-black text-white mt-0.5">
              {soilSensor?.current_value !== null && soilSensor?.current_value !== undefined
                ? `${soilSensor.current_value}%`
                : '--'}
            </div>
          </div>
          <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
            <span>Threshold Min:</span>
            <span className="text-slate-300 font-semibold">{thresholds?.soil_moisture_min || 30}%</span>
          </div>
        </div>

        {/* Temperature */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
              <Thermometer className="w-5 h-5" />
            </div>
            {getStateBadge(tempSensor?.state || 'NORMAL')}
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Greenhouse Temperature</div>
            <div className="text-2xl font-black text-white mt-0.5">
              {tempSensor?.current_value !== null && tempSensor?.current_value !== undefined
                ? `${tempSensor.current_value}°C`
                : '--'}
            </div>
          </div>
          <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
            <span>Safe Range:</span>
            <span className="text-slate-300 font-semibold">
              {thresholds?.temperature_min || 18}°C - {thresholds?.temperature_max || 32}°C
            </span>
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <CloudRain className="w-5 h-5" />
            </div>
            {getStateBadge(humSensor?.state || 'NORMAL')}
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Relative Humidity</div>
            <div className="text-2xl font-black text-white mt-0.5">
              {humSensor?.current_value !== null && humSensor?.current_value !== undefined
                ? `${humSensor.current_value}%`
                : '--'}
            </div>
          </div>
          <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
            <span>Safe Range:</span>
            <span className="text-slate-300 font-semibold">
              {thresholds?.humidity_min || 40}% - {thresholds?.humidity_max || 85}%
            </span>
          </div>
        </div>

        {/* Water Level */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between">
            <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400">
              <Waves className="w-5 h-5" />
            </div>
            {getStateBadge(waterSensor?.state || 'NORMAL')}
          </div>
          <div>
            <div className="text-xs font-medium text-slate-400">Water Reservoir Level</div>
            <div className="text-2xl font-black text-white mt-0.5">
              {waterSensor?.current_value !== null && waterSensor?.current_value !== undefined
                ? `${waterSensor.current_value}%`
                : '--'}
            </div>
          </div>
          <div className="text-[11px] text-slate-400 border-t border-slate-800/80 pt-2 flex justify-between">
            <span>Safety Cutoff:</span>
            <span className="text-rose-400 font-semibold">
              {thresholds?.water_level_safe_min || 15}% Min
            </span>
          </div>
        </div>
      </div>

      {/* Middle Grid: Actuators Status & Live Weather Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Actuators & Automation Status (2 cols) */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Power className="w-5 h-5 text-emerald-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Automated Actuator Systems
              </h3>
            </div>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              Closed-Loop Control
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Irrigation Pump */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Irrigation Pump</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
                    pump?.status === 'ON'
                      ? 'bg-emerald-950 text-emerald-400 border-emerald-800 animate-pulse'
                      : 'bg-slate-900 text-slate-500 border-slate-800'
                  }`}
                >
                  {pump?.status || 'OFF'}
                </span>
              </div>
              <div className="text-xs text-slate-300">
                Mode: <span className="font-semibold text-slate-200">{pump?.mode || 'AUTO'}</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                Safety interlock active: Locked if water &lt; {thresholds?.water_level_safe_min || 15}%
              </p>
            </div>

            {/* Greenhouse Fan */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Cooling Fan</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
                    fan?.status === 'ON'
                      ? 'bg-cyan-950 text-cyan-400 border-cyan-800'
                      : 'bg-slate-900 text-slate-500 border-slate-800'
                  }`}
                >
                  {fan?.status || 'OFF'}
                </span>
              </div>
              <div className="text-xs text-slate-300">
                Mode: <span className="font-semibold text-slate-200">{fan?.mode || 'AUTO'}</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                Triggers when temp &gt; {thresholds?.temperature_max || 32}°C or humidity &gt; {thresholds?.humidity_max || 85}%
              </p>
            </div>

            {/* Radiant Heater */}
            <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-400">Radiant Heater</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
                    heater?.status === 'ON'
                      ? 'bg-amber-950 text-amber-400 border-amber-800'
                      : 'bg-slate-900 text-slate-500 border-slate-800'
                  }`}
                >
                  {heater?.status || 'OFF'}
                </span>
              </div>
              <div className="text-xs text-slate-300">
                Mode: <span className="font-semibold text-slate-200">{heater?.mode || 'AUTO'}</span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                Triggers when temp &lt; {thresholds?.temperature_min || 18}°C
              </p>
            </div>
          </div>
        </div>

        {/* Live Weather Widget (1 col) */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Sun className="w-5 h-5 text-amber-400" />
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Farm Weather
              </h3>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              {weather?.is_simulated ? 'Physics Model' : 'Live Station'}
            </span>
          </div>

          {weather ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-black text-white">{weather.temperature}°C</div>
                  <div className="text-xs text-slate-400">{weather.condition}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-slate-400">Rain Probability</div>
                  <div className="text-sm font-bold text-cyan-400">{weather.rainfall_probability}%</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-800/80">
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400 block text-[10px]">Wind Speed</span>
                  <span className="text-slate-200 font-semibold">{weather.wind_speed_kmh} km/h</span>
                </div>
                <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                  <span className="text-slate-400 block text-[10px]">Solar Flux</span>
                  <span className="text-slate-200 font-semibold">{weather.solar_radiation_w_m2} W/m²</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 py-6 text-center">Loading weather metrics...</div>
          )}
        </div>
      </div>

      {/* Active Alerts Feed */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-400" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Active Security & System Alerts ({alerts.length})
            </h3>
          </div>
        </div>

        {alerts.length === 0 ? (
          <div className="py-6 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>All agricultural systems and environmental sensors nominal. No active warnings.</span>
          </div>
        ) : (
          <div className="space-y-2.5">
            {alerts.slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase ${
                        alert.severity === 'CRITICAL'
                          ? 'bg-red-950 text-red-400 border-red-800'
                          : alert.severity === 'WARNING'
                          ? 'bg-amber-950 text-amber-400 border-amber-800'
                          : 'bg-blue-950 text-blue-400 border-blue-800'
                      }`}
                    >
                      {alert.severity}
                    </span>
                    <span className="text-xs font-semibold text-slate-200">{alert.title}</span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(alert.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">{alert.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
