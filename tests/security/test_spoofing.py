import datetime

from backend.app.models import Alert, AuditLog


def test_sensor_spoofing_unregistered_device_rejection(client, db_session):
    """
    DEMO 5: Sensor spoofing protection.
    An unauthorized/unregistered rogue client (DEV_ROGUE_99) attempts to inject sensor telemetry.
    The system MUST reject the reading, raise a security alert, and record the event in audit logs.
    """
    payload = {
        "device_id": "DEV_ROGUE_99",
        "farm_id": "farm_1",
        "sensor_type": "soil_moisture",
        "value": 25.0,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "unauthorized_token"
    }

    resp = client.post("/api/sensors/reading", json=payload)
    assert resp.status_code == 400
    assert "SENSOR_SPOOF_DETECTED" in resp.json()["detail"]

    # Verify immutable audit log recorded the attack attempt
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type == "SENSOR_SPOOF_ATTEMPT",
        AuditLog.actor_id == "DEV_ROGUE_99"
    ).first()
    assert audit is not None
    assert audit.result == "REJECTED"
    assert audit.severity == "CRITICAL"

    # Verify security alert was generated
    alert = db_session.query(Alert).filter(
        Alert.device_id == "DEV_ROGUE_99",
        Alert.category == "SECURITY"
    ).first()
    assert alert is not None
    assert alert.severity == "CRITICAL"
