export type UserRole = 'ADMIN' | 'OPERATOR' | 'VIEWER';

export interface AuthUser {
  username: string;
  role: UserRole;
  token: string;
}

export interface SensorStatus {
  device_id: string;
  device_name: string;
  farm_id: string;
  device_status: string;
  sensor_type: string;
  current_value: number | null;
  unit: string;
  state: 'NORMAL' | 'WARNING' | 'CRITICAL';
  last_seen: string | null;
  recent_readings: Array<{ value: number; timestamp: string }>;
}

export interface ActuatorItem {
  id: string;
  device_id: string;
  farm_id: string;
  actuator_type: string;
  status: 'ON' | 'OFF';
  mode: 'AUTO' | 'MANUAL';
  current_runtime_seconds: number;
  last_activated_at: string | null;
  last_deactivated_at: string | null;
  updated_at: string;
}

export interface Thresholds {
  id: number;
  farm_id: string;
  soil_moisture_min: number;
  soil_moisture_target: number;
  temperature_min: number;
  temperature_max: number;
  humidity_min: number;
  humidity_max: number;
  water_level_safe_min: number;
  max_pump_runtime_seconds: number;
  updated_at: string;
  updated_by: string | null;
}

export interface AlertItem {
  id: number;
  farm_id: string;
  device_id: string | null;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  category: 'SECURITY' | 'ENVIRONMENTAL' | 'EQUIPMENT' | 'AVAILABILITY';
  title: string;
  message: string;
  resolved: boolean;
  created_at: string;
  resolved_at: string | null;
}

export interface DeviceItem {
  id: string;
  farm_id: string;
  device_name: string;
  device_type: string;
  status: 'active' | 'inactive' | 'suspended';
  last_seen: string | null;
  created_at: string;
}

export interface AuditLogItem {
  id: number;
  timestamp: string;
  event_type: string;
  actor_type: string;
  actor_id: string;
  action: string;
  resource: string;
  result: 'SUCCESS' | 'FAILURE' | 'REJECTED' | 'BLOCKED';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  ip_address: string | null;
  details: string | null;
}

export interface WeatherInfo {
  location: string;
  temperature: number;
  humidity: number;
  condition: string;
  wind_speed_kmh: number;
  rainfall_probability: number;
  solar_radiation_w_m2: number;
  timestamp: string;
  is_simulated: boolean;
}
