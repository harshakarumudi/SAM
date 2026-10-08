import datetime

from backend.app.models import AuditLog


def test_suspended_device_telemetry_rejection(client, db_session, admin_token):
    """
    DEMO 10: Device suspension protection.
    A device administratively suspended in the database (DEV_SUSPENDED_01)
    must NOT be able to publish sensor readings.
    """
    payload = {
        "device_id": "DEV_SUSPENDED_01",
        "farm_id": "farm_1",
        "sensor_type": "soil_moisture",
        "value": 45.0,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "suspended_secret_key"
    }

    resp = client.post("/api/sensors/reading", json=payload)
    assert resp.status_code == 400
    assert "DEVICE_SUSPENDED" in resp.json()["detail"]

    # Verify audit log
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type == "SUSPENDED_DEVICE_ATTEMPT",
        AuditLog.actor_id == "DEV_SUSPENDED_01"
    ).first()
    assert audit is not None
    assert audit.result == "BLOCKED"
