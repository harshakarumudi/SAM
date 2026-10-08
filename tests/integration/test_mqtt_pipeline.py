import datetime

from backend.app.models import AuditLog, SensorReading
from backend.app.services.mqtt_service import mqtt_manager


def test_mqtt_telemetry_ingestion_pipeline(db_session):
    """
    INTEGRATION TEST:
    Sensor -> MQTT message -> Backend validation -> Database storage -> Automation trigger.
    """
    topic = "farm/farm_1/device/DEV_SOIL_01/sensor"
    payload = {
        "device_id": "DEV_SOIL_01",
        "farm_id": "farm_1",
        "sensor_type": "soil_moisture",
        "value": 52.5,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "soil_secret_key_01"
    }

    # Simulate ingestion handler
    mqtt_manager._process_sensor_payload("farm_1", "DEV_SOIL_01", payload, db_session=db_session)

    # Check reading was stored in database
    latest = (
        db_session.query(SensorReading)
        .filter(
            SensorReading.device_id == "DEV_SOIL_01",
            SensorReading.sensor_type == "soil_moisture"
        )
        .order_by(SensorReading.timestamp.desc())
        .first()
    )
    assert latest is not None
    assert latest.value == 52.5
    assert latest.is_valid is True


def test_mqtt_topic_spoofing_mismatch_rejection(db_session):
    """
    INTEGRATION TEST:
    Topic is for DEV_SOIL_01, but payload attempts to impersonate DEV_ENV_01 or DEV_ROGUE_99.
    Topic/payload integrity check MUST reject the message and log SENSOR_SPOOF_ATTEMPT.
    """
    topic_device = "DEV_SOIL_01"
    payload = {
        "device_id": "DEV_ROGUE_99",  # Mismatched!
        "farm_id": "farm_1",
        "sensor_type": "soil_moisture",
        "value": 33.0,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    mqtt_manager._process_sensor_payload("farm_1", topic_device, payload, db_session=db_session)

    # Verify audit log caught topic mismatch
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type == "SENSOR_SPOOF_ATTEMPT",
        AuditLog.resource == "mqtt:sensor"
    ).first()
    assert audit is not None
    assert audit.result == "REJECTED"
