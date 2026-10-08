import datetime

from sqlalchemy.orm import Session

from backend.app.core.security import verify_device_token
from backend.app.models import Alert, Device, SensorReading
from backend.app.schemas import SensorReadingCreate
from backend.app.services.audit_service import log_security_event

# Standard Physical Environmental Range Definitions
PHYSICAL_RANGES = {
    "soil_moisture": {"min": 0.0, "max": 100.0, "unit": "%", "max_jump": 40.0},
    "temperature": {"min": -10.0, "max": 60.0, "unit": "°C", "max_jump": 25.0},
    "humidity": {"min": 0.0, "max": 100.0, "unit": "%", "max_jump": 45.0},
    "water_level": {"min": 0.0, "max": 100.0, "unit": "%", "max_jump": 35.0},
}


class SensorDataValidationService:
    @staticmethod
    def validate_and_sanitize(
        db: Session,
        reading_in: SensorReadingCreate,
        client_ip: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Comprehensive multi-layer validation pipeline:
        1. Device Registration & Spoofing Check
        2. Device Suspension & State Verification
        3. Device Authentication Token Verification
        4. Freshness / Replay Attack Mitigation
        5. Physical Range Boundary Check
        6. Statistical Rate-of-Change Anomaly Check
        """
        device_id = reading_in.device_id
        sensor_type = reading_in.sensor_type
        value = reading_in.value
        timestamp = reading_in.timestamp

        # 1. Device Registration Check (Protection against spoofing by unknown devices)
        device = db.query(Device).filter(Device.id == device_id).first()
        if not device:
            reason = f"SENSOR_SPOOF_DETECTED: Device '{device_id}' is unregistered"
            log_security_event(
                db=db,
                event_type="SENSOR_SPOOF_ATTEMPT",
                actor_type="DEVICE",
                actor_id=device_id,
                action="PUBLISH_TELEMETRY",
                resource=f"sensor:{sensor_type}",
                result="REJECTED",
                severity="CRITICAL",
                ip_address=client_ip,
                details=reason
            )
            # Create Security Alert
            alert = Alert(
                farm_id=reading_in.farm_id,
                device_id=device_id,
                severity="CRITICAL",
                category="SECURITY",
                title="Sensor Spoofing Attempt Detected",
                message=f"Unregistered device ID '{device_id}' attempted to publish telemetry to farm '{reading_in.farm_id}'."
            )
            db.add(alert)
            db.commit()
            return False, reason

        # 2. Device Suspension Check (Protection against compromised / revoked devices)
        if device.status == "suspended":
            reason = f"DEVICE_SUSPENDED: Device '{device_id}' has been administratively suspended"
            log_security_event(
                db=db,
                event_type="SUSPENDED_DEVICE_ATTEMPT",
                actor_type="DEVICE",
                actor_id=device_id,
                action="PUBLISH_TELEMETRY",
                resource=f"sensor:{sensor_type}",
                result="BLOCKED",
                severity="WARNING",
                ip_address=client_ip,
                details=reason
            )
            alert = Alert(
                farm_id=reading_in.farm_id,
                device_id=device_id,
                severity="WARNING",
                category="SECURITY",
                title="Suspended Device Telemetry Blocked",
                message=f"Device '{device_id}' is in SUSPENDED status and its incoming data was discarded."
            )
            db.add(alert)
            db.commit()
            return False, reason

        if device.status != "active":
            reason = f"DEVICE_INACTIVE: Device '{device_id}' is not in active state (current: {device.status})"
            return False, reason

        # 3. Device Authentication Token Verification
        if reading_in.auth_token:
            if not verify_device_token(reading_in.auth_token, device.auth_token_hash):
                reason = f"DEVICE_AUTH_FAILED: Invalid authentication token provided for device '{device_id}'"
                log_security_event(
                    db=db,
                    event_type="DEVICE_AUTH_FAILURE",
                    actor_type="DEVICE",
                    actor_id=device_id,
                    action="AUTHENTICATE_TELEMETRY",
                    resource=f"device:{device_id}",
                    result="REJECTED",
                    severity="CRITICAL",
                    ip_address=client_ip,
                    details=reason
                )
                alert = Alert(
                    farm_id=reading_in.farm_id,
                    device_id=device_id,
                    severity="CRITICAL",
                    category="SECURITY",
                    title="Device Authentication Failure",
                    message=f"Telemetry from '{device_id}' failed cryptographic authentication token check."
                )
                db.add(alert)
                db.commit()
                return False, reason

        # 4. Freshness Verification (Replay Attack Protection)
        now = datetime.datetime.utcnow()
        # Accept reading if within +/- 300 seconds
        time_diff = (now - timestamp).total_seconds()
        if time_diff > 300:
            reason = f"REPLAY_OR_STALE: Reading timestamp is too old ({int(time_diff)}s in past)"
            log_security_event(
                db=db,
                event_type="STALE_DATA_REJECTED",
                actor_type="DEVICE",
                actor_id=device_id,
                action="TIMESTAMP_CHECK",
                resource=f"sensor:{sensor_type}",
                result="REJECTED",
                severity="WARNING",
                ip_address=client_ip,
                details=reason
            )
            return False, reason

        if time_diff < -60:
            reason = f"FUTURE_TIMESTAMP: Reading timestamp is ahead of server clock by {int(-time_diff)}s"
            return False, reason

        # 5. Physical Range Boundary Check (False Environmental Data Protection)
        range_spec = PHYSICAL_RANGES.get(sensor_type)
        if not range_spec:
            reason = f"UNKNOWN_SENSOR_TYPE: '{sensor_type}' is unsupported"
            return False, reason

        if value < range_spec["min"] or value > range_spec["max"]:
            reason = f"FALSE_ENVIRONMENTAL_DATA: Value {value} is out of physical boundary [{range_spec['min']}, {range_spec['max']}] {range_spec['unit']}"
            log_security_event(
                db=db,
                event_type="FALSE_DATA_DETECTED",
                actor_type="DEVICE",
                actor_id=device_id,
                action="RANGE_VALIDATION",
                resource=f"sensor:{sensor_type}",
                result="REJECTED",
                severity="WARNING",
                ip_address=client_ip,
                details=reason
            )
            alert = Alert(
                farm_id=reading_in.farm_id,
                device_id=device_id,
                severity="WARNING",
                category="ENVIRONMENTAL",
                title="Impossible Sensor Value Rejected",
                message=f"Device '{device_id}' sent {sensor_type}={value}{range_spec['unit']}, which violates physical limits."
            )
            db.add(alert)
            db.commit()
            return False, reason

        # 6. Rate-of-Change / Anomaly Spike Detection
        last_reading = (
            db.query(SensorReading)
            .filter(
                SensorReading.device_id == device_id,
                SensorReading.sensor_type == sensor_type,
                SensorReading.is_valid == True
            )
            .order_by(SensorReading.timestamp.desc())
            .first()
        )

        if last_reading:
            delta = abs(value - last_reading.value)
            if delta > range_spec["max_jump"]:
                reason = f"ANOMALY_RATE_OF_CHANGE: Value jumped by {delta:.1f}{range_spec['unit']} from previous {last_reading.value}{range_spec['unit']}"
                log_security_event(
                    db=db,
                    event_type="ANOMALOUS_DATA_DETECTED",
                    actor_type="DEVICE",
                    actor_id=device_id,
                    action="ANOMALY_DETECTION",
                    resource=f"sensor:{sensor_type}",
                    result="REJECTED",
                    severity="WARNING",
                    ip_address=client_ip,
                    details=reason
                )
                alert = Alert(
                    farm_id=reading_in.farm_id,
                    device_id=device_id,
                    severity="WARNING",
                    category="ENVIRONMENTAL",
                    title="Sudden Sensor Anomaly Detected",
                    message=f"Device '{device_id}' registered sudden spike: {last_reading.value} -> {value}{range_spec['unit']}."
                )
                db.add(alert)
                db.commit()
                return False, reason

        # Update Device last_seen timestamp
        device.last_seen = now
        db.commit()

        return True, None
