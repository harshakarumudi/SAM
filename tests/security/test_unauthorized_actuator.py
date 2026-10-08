from backend.app.models import Actuator, AuditLog


def test_viewer_unauthorized_actuator_command_rejection(client, db_session, viewer_token):
    """
    DEMO 7: Protection against unauthorized actuator control.
    A user with VIEWER role attempts to start/stop the water pump.
    The backend MUST reject the command with HTTP 403 Forbidden and record an audit log.
    """
    resp = client.post(
        "/api/actuators/ACT_PUMP_01/command",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"command": "START", "reason": "Unauthorized attempt"}
    )
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]

    # Verify audit log captures unauthorized access
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type == "UNAUTHORIZED_ACCESS",
        AuditLog.actor_id == "viewer"
    ).first()
    assert audit is not None
    assert audit.result == "BLOCKED"


def test_admin_authorized_actuator_control(client, db_session, admin_token):
    """
    DEMO 8: Authorized administrator control.
    Farm administrator issues START command. Command is validated, executed, and logged.
    """
    resp = client.post(
        "/api/actuators/ACT_FAN_01/command",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"command": "START", "reason": "Admin cooling override"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "EXECUTED"

    # Verify actuator state was updated
    fan = db_session.query(Actuator).filter(Actuator.id == "ACT_FAN_01").first()
    assert fan.status == "ON"

    # Verify audit log recorded successful admin action
    audit = db_session.query(AuditLog).filter(
        AuditLog.event_type == "ACTUATOR_COMMAND",
        AuditLog.actor_id == "admin"
    ).first()
    assert audit is not None
    assert audit.result == "SUCCESS"
