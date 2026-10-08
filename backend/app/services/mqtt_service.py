import datetime
import json
import logging
import threading

import paho.mqtt.client as mqtt

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models import Device, SensorReading
from backend.app.schemas import SensorReadingCreate
from backend.app.services.audit_service import log_security_event
from backend.app.services.threshold_engine import ThresholdEngine
from backend.app.services.validation_service import SensorDataValidationService

logger = logging.getLogger("MQTTService")


class MQTTService:
    def __init__(self):
        self.client: mqtt.Client | None = None
        self.is_connected = False
        self._lock = threading.Lock()

    def start(self):
        """Starts the MQTT client background loop."""
        try:
            # Use CallbackAPIVersion.VERSION2 for paho-mqtt >= 2.0 compatibility
            try:
                self.client = mqtt.Client(
                    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                    client_id=settings.MQTT_CLIENT_ID
                )
            except (AttributeError, TypeError):
                self.client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)

            if settings.MQTT_USER and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            logger.info(f"Connecting to MQTT Broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}...")
            self.client.connect_async(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, settings.MQTT_KEEPALIVE)
            self.client.loop_start()
        except Exception as e:
            logger.warning(f"MQTT connection initialization failed (will retry or run offline): {e}")

    def stop(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc.value if hasattr(rc, "value") else rc
        if rc_code == 0:
            self.is_connected = True
            logger.info("Successfully connected to MQTT Broker with authentication.")
            # Subscribe to sensor telemetry and actuator acks
            client.subscribe("farm/+/device/+/sensor", qos=1)
            client.subscribe("farm/+/device/+/status", qos=1)
            client.subscribe("farm/+/device/+/ack", qos=1)
        else:
            self.is_connected = False
            logger.error(f"MQTT Broker connection failed with return code {rc_code}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.is_connected = False
        logger.warning(f"Disconnected from MQTT Broker (rc={rc})")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode("utf-8", errors="ignore")

        try:
            data = json.loads(payload_str)
        except json.JSONDecodeError:
            logger.warning(f"Malformed JSON received on topic {topic}")
            return

        # Extract topic parts: farm/{farm_id}/device/{device_id}/{subtopic}
        parts = topic.split("/")
        if len(parts) >= 5 and parts[4] == "sensor":
            farm_id = parts[1]
            topic_device_id = parts[3]
            self._process_sensor_payload(farm_id, topic_device_id, data)
        elif len(parts) >= 5 and parts[4] == "status":
            topic_device_id = parts[3]
            self._process_device_heartbeat(topic_device_id, data)

    def _process_sensor_payload(self, farm_id: str, topic_device_id: str, data: dict, db_session=None):
        db = db_session if db_session is not None else SessionLocal()
        close_on_finish = db_session is None
        try:
            payload_device_id = data.get("device_id")

            # Anti-Spoofing Topic vs Payload Integrity Check
            if payload_device_id != topic_device_id:
                reason = f"DEVICE_MISMATCH: Topic device '{topic_device_id}' != Payload device '{payload_device_id}'"
                log_security_event(
                    db=db,
                    event_type="SENSOR_SPOOF_ATTEMPT",
                    actor_type="DEVICE",
                    actor_id=str(topic_device_id),
                    action="TOPIC_INTEGRITY_CHECK",
                    resource="mqtt:sensor",
                    result="REJECTED",
                    severity="CRITICAL",
                    details=reason
                )
                return

            # Parse timestamp if present, default to now
            ts = data.get("timestamp")
            if ts:
                try:
                    parsed_ts = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    parsed_ts = datetime.datetime.utcnow()
            else:
                parsed_ts = datetime.datetime.utcnow()

            reading_in = SensorReadingCreate(
                device_id=payload_device_id,
                farm_id=farm_id,
                sensor_type=data.get("sensor_type", "unknown"),
                value=float(data.get("value", 0.0)),
                unit=data.get("unit", ""),
                timestamp=parsed_ts,
                auth_token=data.get("auth_token")
            )

            # Security & Validation Pipeline
            is_valid, rejection_reason = SensorDataValidationService.validate_and_sanitize(
                db=db,
                reading_in=reading_in
            )

            # Record reading in database
            reading = SensorReading(
                device_id=reading_in.device_id,
                farm_id=reading_in.farm_id,
                sensor_type=reading_in.sensor_type,
                value=reading_in.value,
                unit=reading_in.unit,
                timestamp=reading_in.timestamp,
                is_valid=is_valid,
                rejection_reason=rejection_reason
            )
            db.add(reading)
            db.commit()

            # If reading is valid, trigger Threshold/Automation Engine
            if is_valid:
                ThresholdEngine.evaluate(
                    db=db,
                    farm_id=reading_in.farm_id,
                    sensor_type=reading_in.sensor_type,
                    current_value=reading_in.value
                )

        except Exception as e:
            logger.error(f"Error handling sensor telemetry: {e}")
            db.rollback()
        finally:
            if close_on_finish:
                db.close()

    def _process_device_heartbeat(self, device_id: str, data: dict):
        db = SessionLocal()
        try:
            device = db.query(Device).filter(Device.id == device_id).first()
            if device and device.status == "active":
                device.last_seen = datetime.datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Error updating device heartbeat: {e}")
        finally:
            db.close()

    def publish_actuator_command(self, farm_id: str, device_id: str, command: str) -> bool:
        """Publishes an authenticated control command to device topic"""
        if not self.client or not self.is_connected:
            logger.warning("Cannot publish command: MQTT client is disconnected")
            return False

        topic = f"farm/{farm_id}/device/{device_id}/command"
        payload = json.dumps({
            "device_id": device_id,
            "command": command,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "issuer": "CLOUD_BACKEND"
        })
        info = self.client.publish(topic, payload, qos=1)
        return info.rc == mqtt.MQTT_ERR_SUCCESS


mqtt_manager = MQTTService()
