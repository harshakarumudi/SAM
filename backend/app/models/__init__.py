import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="VIEWER", nullable=False)  # ADMIN, OPERATOR, VIEWER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Farm(Base):
    __tablename__ = "farms"

    id = Column(String(50), primary_key=True, index=True)  # e.g., "farm_1"
    name = Column(String(100), nullable=False)
    location = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    devices = relationship("Device", back_populates="farm", cascade="all, delete-orphan")
    thresholds = relationship("Threshold", back_populates="farm", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(50), primary_key=True, index=True)  # e.g., "DEV_SOIL_01"
    farm_id = Column(String(50), ForeignKey("farms.id"), nullable=False, index=True)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)  # soil_moisture, environmental, water_level, actuator
    status = Column(String(20), default="active", nullable=False)  # active, inactive, suspended
    auth_token_hash = Column(String(255), nullable=False)
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    farm = relationship("Farm", back_populates="devices")
    readings = relationship("SensorReading", back_populates="device", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(50), ForeignKey("devices.id"), nullable=False, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    sensor_type = Column(String(50), nullable=False)  # soil_moisture, temperature, humidity, water_level
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    is_valid = Column(Boolean, default=True, nullable=False)
    rejection_reason = Column(String(255), nullable=True)

    device = relationship("Device", back_populates="readings")


class Threshold(Base):
    __tablename__ = "thresholds"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String(50), ForeignKey("farms.id"), unique=True, nullable=False)
    soil_moisture_min = Column(Float, default=30.0, nullable=False)  # Below this, irrigation starts
    soil_moisture_target = Column(Float, default=60.0, nullable=False)  # At this, irrigation stops
    temperature_min = Column(Float, default=18.0, nullable=False)  # Below this, heater ON
    temperature_max = Column(Float, default=32.0, nullable=False)  # Above this, fan ON
    humidity_min = Column(Float, default=40.0, nullable=False)
    humidity_max = Column(Float, default=85.0, nullable=False)
    water_level_safe_min = Column(Float, default=15.0, nullable=False)  # Safety interlock
    max_pump_runtime_seconds = Column(Integer, default=600, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    updated_by = Column(String(50), nullable=True)

    farm = relationship("Farm", back_populates="thresholds")


class Actuator(Base):
    __tablename__ = "actuators"

    id = Column(String(50), primary_key=True, index=True)  # e.g., "ACT_PUMP_01", "ACT_FAN_01"
    device_id = Column(String(50), nullable=False)
    farm_id = Column(String(50), nullable=False, index=True)
    actuator_type = Column(String(50), nullable=False)  # pump, fan, heater, ventilation
    status = Column(String(10), default="OFF", nullable=False)  # ON, OFF
    mode = Column(String(10), default="AUTO", nullable=False)  # AUTO, MANUAL
    last_activated_at = Column(DateTime, nullable=True)
    last_deactivated_at = Column(DateTime, nullable=True)
    current_runtime_seconds = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class ActuatorCommand(Base):
    __tablename__ = "actuator_commands"

    id = Column(Integer, primary_key=True, index=True)
    actuator_id = Column(String(50), ForeignKey("actuators.id"), nullable=False, index=True)
    command = Column(String(20), nullable=False)  # START, STOP
    issuer_type = Column(String(20), nullable=False)  # USER, AUTO_SYSTEM
    issuer_id = Column(String(50), nullable=False)
    status = Column(String(20), default="ISSUED", nullable=False)  # ISSUED, EXECUTED, FAILED, REJECTED
    reason = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    device_id = Column(String(50), nullable=True, index=True)
    severity = Column(String(20), nullable=False)  # INFO, WARNING, CRITICAL
    category = Column(String(30), nullable=False)  # SECURITY, ENVIRONMENTAL, EQUIPMENT, AVAILABILITY
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    event_type = Column(String(60), nullable=False, index=True)
    actor_type = Column(String(20), nullable=False)  # USER, DEVICE, SYSTEM
    actor_id = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    resource = Column(String(100), nullable=False)
    result = Column(String(20), nullable=False)  # SUCCESS, FAILURE, REJECTED, BLOCKED
    severity = Column(String(20), default="INFO", nullable=False)  # INFO, WARNING, CRITICAL
    ip_address = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
