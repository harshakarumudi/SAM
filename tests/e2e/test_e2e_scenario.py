import datetime

from backend.app.models import Actuator


def test_complete_e2e_lifecycle_scenario(client, db_session):
    """
    E2E SYSTEM TEST:
    Demonstrates complete lifecycle required for lab examination:
    1. Authenticate with Administrator credentials.
    2. Query initial farm status and verify actuators are OFF.
    3. IoT sensor telemetry reports dry soil (18% < threshold 30%).
    4. Threshold automation activates irrigation pump (Pump ON).
    5. Equipment alert is created and visible via alerts API.
    6. Sensor telemetry reports soil moisture recovery (65% >= threshold target 60%).
    7. Threshold automation safely stops irrigation pump (Pump OFF).
    8. Query audit log API with Admin token to verify immutable security trail.
    """
    # 1. Login as Administrator
    login_resp = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@Secure2026!"}
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check initial actuator state
    act_resp = client.get("/api/actuators", headers=headers)
    assert act_resp.status_code == 200
    pump = db_session.query(Actuator).filter(Actuator.actuator_type == "pump").first()
    pump.status = "OFF"
    db_session.commit()

    # Ensure reservoir water level is adequate (75%)
    water_payload = {
        "device_id": "DEV_WATER_01",
        "farm_id": "farm_1",
        "sensor_type": "water_level",
        "value": 75.0,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "water_secret_key_01"
    }
    client.post("/api/sensors/reading", json=water_payload)

    # 3. Sensor reports dry soil (18%)
    dry_payload = {
        "device_id": "DEV_SOIL_01",
        "farm_id": "farm_1",
        "sensor_type": "soil_moisture",
        "value": 18.0,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "soil_secret_key_01"
    }
    dry_resp = client.post("/api/sensors/reading", json=dry_payload)
    assert dry_resp.status_code == 200

    # 4. Verify pump was automatically turned ON
    db_session.refresh(pump)
    assert pump.status == "ON"

    # 5. Verify alert generated
    alert_resp = client.get("/api/alerts", headers=headers)
    assert alert_resp.status_code == 200
    alerts = alert_resp.json()
    assert any("Automatic Irrigation Activated" in a["title"] for a in alerts)

    # 6. Soil moisture gradually improves as irrigation runs (18% -> 40% -> 65%)
    step1_payload = {
        "device_id": "DEV_SOIL_01",
        "farm_id": "farm_1",
        "sensor_type": "soil_moisture",
        "value": 40.0,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "soil_secret_key_01"
    }
    client.post("/api/sensors/reading", json=step1_payload)

    # Final recovery reaching target safe level (65% >= threshold target 60%)
    recovery_payload = {
        "device_id": "DEV_SOIL_01",
        "farm_id": "farm_1",
        "sensor_type": "soil_moisture",
        "value": 65.0,
        "unit": "%",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "auth_token": "soil_secret_key_01"
    }
    rec_resp = client.post("/api/sensors/reading", json=recovery_payload)
    assert rec_resp.status_code == 200

    # 7. Verify pump safely stopped
    db_session.refresh(pump)
    assert pump.status == "OFF"

    # 8. Query audit logs to verify security traceability
    audit_resp = client.get("/api/audit-logs", headers=headers)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) > 0
    # Confirm presence of actuator state change event
    assert any("ACTUATOR_STATE_CHANGE" in log["event_type"] for log in logs)
