import {
  AuthUser,
  SensorStatus,
  ActuatorItem,
  Thresholds,
  AlertItem,
  DeviceItem,
  AuditLogItem,
  WeatherInfo
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function getHeaders(): HeadersInit {
  const token = localStorage.getItem('agri_jwt_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  async login(username: string, password: string): Promise<AuthUser> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Authentication failed');
    }
    const data = await res.json();
    return {
      username: data.username,
      role: data.role,
      token: data.access_token,
    };
  },

  async getSensors(): Promise<SensorStatus[]> {
    const res = await fetch(`${API_BASE}/sensors`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load sensor readings');
    return res.json();
  },

  async getActuators(): Promise<ActuatorItem[]> {
    const res = await fetch(`${API_BASE}/actuators`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load actuators');
    return res.json();
  },

  async executeActuatorCommand(actuatorId: string, command: 'START' | 'STOP', reason?: string) {
    const res = await fetch(`${API_BASE}/actuators/${actuatorId}/command`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ command, reason }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Actuator command rejected');
    }
    return res.json();
  },

  async getThresholds(): Promise<Thresholds> {
    const res = await fetch(`${API_BASE}/thresholds`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load thresholds');
    return res.json();
  },

  async updateThresholds(farmId: string, data: Partial<Thresholds>): Promise<Thresholds> {
    const res = await fetch(`${API_BASE}/thresholds/${farmId}`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Threshold update rejected');
    }
    return res.json();
  },

  async getDevices(): Promise<DeviceItem[]> {
    const res = await fetch(`${API_BASE}/devices`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load devices');
    return res.json();
  },

  async registerDevice(data: { id: string; farm_id: string; device_name: string; device_type: string; auth_secret: string }) {
    const res = await fetch(`${API_BASE}/devices`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Device registration failed');
    }
    return res.json();
  },

  async suspendDevice(deviceId: string): Promise<DeviceItem> {
    const res = await fetch(`${API_BASE}/devices/${deviceId}/suspend`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Device suspension failed');
    }
    return res.json();
  },

  async activateDevice(deviceId: string): Promise<DeviceItem> {
    const res = await fetch(`${API_BASE}/devices/${deviceId}/activate`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Device activation failed');
    }
    return res.json();
  },

  async getAlerts(resolved?: boolean, severity?: string): Promise<AlertItem[]> {
    let url = `${API_BASE}/alerts?`;
    if (resolved !== undefined) url += `resolved=${resolved}&`;
    if (severity) url += `severity=${severity}&`;
    const res = await fetch(url, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load alerts');
    return res.json();
  },

  async resolveAlert(alertId: number): Promise<AlertItem> {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/resolve`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error('Failed to resolve alert');
    return res.json();
  },

  async getAuditLogs(severity?: string, eventType?: string): Promise<AuditLogItem[]> {
    let url = `${API_BASE}/audit-logs?limit=100&`;
    if (severity) url += `severity=${severity}&`;
    if (eventType) url += `event_type=${eventType}&`;
    const res = await fetch(url, { headers: getHeaders() });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Access denied to audit logs');
    }
    return res.json();
  },

  async getWeather(): Promise<WeatherInfo> {
    const res = await fetch(`${API_BASE}/weather`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load weather');
    return res.json();
  },

  async getHealth() {
    const res = await fetch('http://localhost:8000/health');
    if (!res.ok) throw new Error('Health check failed');
    return res.json();
  }
};
