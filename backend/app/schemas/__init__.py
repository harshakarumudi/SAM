import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Auth & User Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field("VIEWER", pattern="^(ADMIN|OPERATOR|VIEWER)$")


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Sensor Reading Schemas ---
class SensorReadingCreate(BaseModel):
    device_id: str = Field(..., min_length=2, max_length=50)
    farm_id: str = Field(..., min_length=2, max_length=50)
    sensor_type: str = Field(..., pattern="^(soil_moisture|temperature|humidity|water_level)$")
    value: float
    unit: str = Field(..., max_length=20)
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    auth_token: str | None = None  # Device authentication token / signature

    @field_validator("value")
    @classmethod
    def validate_physical_bounds(cls, v: float, info):
        # We also do deep contextual validation in validation_service
        if v is None:
            raise ValueError("Sensor value cannot be None")
        return v


class SensorReadingResponse(BaseModel):
    id: int
    device_id: str
    farm_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime.datetime
    is_valid: bool
    rejection_reason: str | None = None

    class Config:
        from_attributes = True


# --- Threshold Schemas ---
class ThresholdUpdate(BaseModel):
    soil_moisture_min: float = Field(..., ge=0.0, le=100.0, description="Minimum soil moisture (%)")
    soil_moisture_target: float = Field(..., ge=0.0, le=100.0, description="Target safe soil moisture (%)")
    temperature_min: float = Field(..., ge=-20.0, le=60.0, description="Lower temp threshold (°C)")
    temperature_max: float = Field(..., ge=-20.0, le=60.0, description="Upper temp threshold (°C)")
    humidity_min: float = Field(..., ge=0.0, le=100.0, description="Lower humidity (%)")
    humidity_max: float = Field(..., ge=0.0, le=100.0, description="Upper humidity (%)")
    water_level_safe_min: float = Field(..., ge=0.0, le=100.0, description="Minimum water level safety interlock (%)")
    max_pump_runtime_seconds: int = Field(600, ge=30, le=7200, description="Maximum continuous pump runtime (s)")

    @field_validator("soil_moisture_target")
    @classmethod
    def validate_soil_moisture_logic(cls, v: float, info):
        min_val = info.data.get("soil_moisture_min")
        if min_val is not None and v <= min_val:
            raise ValueError("Target soil moisture must be strictly greater than minimum threshold")
        return v

    @field_validator("temperature_max")
    @classmethod
    def validate_temp_logic(cls, v: float, info):
        min_val = info.data.get("temperature_min")
        if min_val is not None and v <= min_val:
            raise ValueError("Maximum temperature must be strictly greater than minimum temperature")
        return v

    @field_validator("humidity_max")
    @classmethod
    def validate_humidity_logic(cls, v: float, info):
        min_val = info.data.get("humidity_min")
        if min_val is not None and v <= min_val:
            raise ValueError("Maximum humidity must be strictly greater than minimum humidity")
        return v


class ThresholdResponse(BaseModel):
    id: int
    farm_id: str
    soil_moisture_min: float
    soil_moisture_target: float
    temperature_min: float
    temperature_max: float
    humidity_min: float
    humidity_max: float
    water_level_safe_min: float
    max_pump_runtime_seconds: int
    updated_at: datetime.datetime
    updated_by: str | None = None

    class Config:
        from_attributes = True


# --- Actuator Schemas ---
class ActuatorCommandRequest(BaseModel):
    command: str = Field(..., pattern="^(START|STOP)$")
    reason: str | None = Field("Manual control command", max_length=200)


class ActuatorResponse(BaseModel):
    id: str
    device_id: str
    farm_id: str
    actuator_type: str
    status: str
    mode: str
    current_runtime_seconds: int
    last_activated_at: datetime.datetime | None = None
    last_deactivated_at: datetime.datetime | None = None
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


class ActuatorCommandResponse(BaseModel):
    id: int
    actuator_id: str
    command: str
    issuer_type: str
    issuer_id: str
    status: str
    reason: str | None = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


# --- Device Schemas ---
class DeviceCreate(BaseModel):
    id: str = Field(..., min_length=3, max_length=50, pattern="^[A-Za-z0-9_\\-]+$")
    farm_id: str = Field(..., min_length=2, max_length=50)
    device_name: str = Field(..., min_length=2, max_length=100)
    device_type: str = Field(..., pattern="^(soil_moisture|environmental|water_level|actuator)$")
    auth_secret: str = Field(..., min_length=8, max_length=100, description="Pre-shared secret/token for device auth")


class DeviceUpdate(BaseModel):
    device_name: str | None = Field(None, min_length=2, max_length=100)
    status: str | None = Field(None, pattern="^(active|inactive|suspended)$")


class DeviceResponse(BaseModel):
    id: str
    farm_id: str
    device_name: str
    device_type: str
    status: str
    last_seen: datetime.datetime | None = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Alert Schemas ---
class AlertResponse(BaseModel):
    id: int
    farm_id: str
    device_id: str | None = None
    severity: str
    category: str
    title: str
    message: str
    resolved: bool
    created_at: datetime.datetime
    resolved_at: datetime.datetime | None = None

    class Config:
        from_attributes = True


class AlertResolve(BaseModel):
    resolved: bool = True


# --- Audit Log Schemas ---
class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime.datetime
    event_type: str
    actor_type: str
    actor_id: str
    action: str
    resource: str
    result: str
    severity: str
    ip_address: str | None = None
    details: str | None = None

    class Config:
        from_attributes = True


# --- Weather & Health Schemas ---
class WeatherResponse(BaseModel):
    location: str
    temperature: float
    humidity: float
    condition: str
    wind_speed_kmh: float
    rainfall_probability: float
    solar_radiation_w_m2: float
    timestamp: datetime.datetime
    is_simulated: bool


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime.datetime
    database: str
    mqtt: str
    active_devices_count: int
    active_alerts_count: int
