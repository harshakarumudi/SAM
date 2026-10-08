import datetime

from backend.app.models import AuditLog, SensorReading


def test_false_environmental_data_rejection(client, db_session):
    """
    DEMO 6: Protection against false environmental data.
    Sensor sends physical absurdity (e.g. Temperature = 999°C).
    System rejects value and logs security warning.
    """
    payload = {
        "device_id": "DEV_ENV_01",
        "farm_id": "farm_1",
        "sensor_type": "temperature",
        "value": 999.0,
        "unit": "°C",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "env_secret_key_01"
    }

    resp = client.post("/api/sensors/reading", json=payload)
    assert resp.status_code == 400
    assert "FALSE_ENVIRONMENTAL_DATA" in resp.json()["detail"]

    # Verify audit event
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type == "FALSE_DATA_DETECTED",
        AuditLog.actor_id == "DEV_ENV_01"
    ).first()
    assert audit is not None
    assert audit.result == "REJECTED"


def test_rate_of_change_anomaly_detection(client, db_session):
    """
    Protection against sudden physical sensor jump anomalies.
    Normal temperature is 24°C, sudden next reading is 55°C (+31°C jump).
    """
    now = datetime.datetime.utcnow()
    # Baseline valid reading
    r1 = SensorReading(
        device_id="DEV_ENV_01",
        farm_id="farm_1",
        sensor_type="temperature",
        value=24.0,
        unit="°C",
        timestamp=now - datetime.timedelta(seconds=10),
        is_valid=True
    )
    db_session.add(r1)
    db_session.commit()

    # Sudden jump to 55°C (delta 31°C > max_jump 25°C)
    payload = {
        "device_id": "DEV_ENV_01",
        "farm_id": "farm_1",
        "sensor_type": "temperature",
        "value": 55.0,
        "unit": "°C",
        "timestamp": now.isoformat(),
        "auth_token": "env_secret_key_01"
    }

    resp = client.post("/api/sensors/reading", json=payload)
    assert resp.status_code == 400
    assert "ANOMALY_RATE_OF_CHANGE" in resp.json()["detail"]

    # Verify anomaly audit event
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type == "ANOMALOUS_DATA_DETECTED",
        AuditLog.actor_id == "DEV_ENV_01"
    ).first()
    assert audit is not None
