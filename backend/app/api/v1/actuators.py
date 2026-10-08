import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_role
from backend.app.models import Actuator, ActuatorCommand, SensorReading, Threshold, User
from backend.app.schemas import (
    ActuatorCommandRequest,
    ActuatorCommandResponse,
    ActuatorResponse,
)
from backend.app.services.audit_service import log_security_event
from backend.app.services.mqtt_service import mqtt_manager

router = APIRouter(prefix="/actuators", tags=["Actuators"])


@router.get("", response_model=list[ActuatorResponse])
def get_actuators(
    farm_id: str = "farm_1",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View status of all farm actuators (pumps, fans, heaters)"""
    actuators = db.query(Actuator).filter(Actuator.farm_id == farm_id).all()
    if not actuators:
        # Initialize default actuators if missing
        defaults = [
            Actuator(id="ACT_PUMP_01", device_id="DEV_PUMP_01", farm_id=farm_id, actuator_type="pump", status="OFF", mode="AUTO"),
            Actuator(id="ACT_FAN_01", device_id="DEV_FAN_01", farm_id=farm_id, actuator_type="fan", status="OFF", mode="AUTO"),
            Actuator(id="ACT_HEATER_01", device_id="DEV_HEATER_01", farm_id=farm_id, actuator_type="heater", status="OFF", mode="AUTO"),
        ]
        for a in defaults:
            db.add(a)
        db.commit()
        actuators = db.query(Actuator).filter(Actuator.farm_id == farm_id).all()
    return actuators


@router.post("/{actuator_id}/command", response_model=ActuatorCommandResponse)
def execute_actuator_command(
    actuator_id: str,
    cmd_in: ActuatorCommandRequest,
    request: Request,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"])),
    db: Session = Depends(get_db)
):
    """
    Execute manual control on an actuator.
    STRICT RBAC: Allowed only for ADMIN and OPERATOR. VIEWER is rejected.
    Enforces physical safety interlocks (e.g. low water level pump lockout).
    Dispatches command to device via secure MQTT topic.
    """
    client_ip = request.client.host if request.client else "unknown"
    actuator = db.query(Actuator).filter(Actuator.id == actuator_id).first()
    if not actuator:
        raise HTTPException(status_code=404, detail="Actuator not found")

    target_state = "ON" if cmd_in.command == "START" else "OFF"

    # Safety Interlock Check for Pump Activation
    if actuator.actuator_type == "pump" and target_state == "ON":
        threshold = db.query(Threshold).filter(Threshold.farm_id == actuator.farm_id).first()
        safe_water_min = threshold.water_level_safe_min if threshold else 15.0

        latest_water = (
            db.query(SensorReading)
            .filter(
                SensorReading.farm_id == actuator.farm_id,
                SensorReading.sensor_type == "water_level",
                SensorReading.is_valid == True
            )
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        current_water = latest_water.value if latest_water else 50.0

        if current_water < safe_water_min:
            reason = f"SAFETY INTERLOCK: Water reservoir ({current_water}%) is below safe minimum ({safe_water_min}%). Manual start blocked."
            log_security_event(
                db=db,
                event_type="SAFETY_INTERLOCK_TRIGGERED",
                actor_type="USER",
                actor_id=current_user.username,
                action="MANUAL_START_PUMP",
                resource=f"actuator:{actuator_id}",
                result="BLOCKED",
                severity="WARNING",
                ip_address=client_ip,
                details=reason
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=reason
            )

    now = datetime.datetime.utcnow()
    actuator.status = target_state
    actuator.mode = "MANUAL"
    actuator.updated_at = now
    if target_state == "ON":
        actuator.last_activated_at = now
        actuator.current_runtime_seconds = 0
    else:
        actuator.last_deactivated_at = now
        actuator.current_runtime_seconds = 0

    cmd_record = ActuatorCommand(
        actuator_id=actuator.id,
        command=cmd_in.command,
        issuer_type="USER",
        issuer_id=current_user.username,
        status="EXECUTED",
        reason=cmd_in.reason,
        timestamp=now
    )
    db.add(cmd_record)

    log_security_event(
        db=db,
        event_type="ACTUATOR_COMMAND",
        actor_type="USER",
        actor_id=current_user.username,
        action=f"MANUAL_{cmd_in.command}",
        resource=f"actuator:{actuator_id}",
        result="SUCCESS",
        severity="INFO",
        ip_address=client_ip,
        details=f"User {current_user.username} executed {cmd_in.command} on {actuator_id}. Reason: {cmd_in.reason}"
    )

    db.commit()
    db.refresh(cmd_record)

    # Secure cloud-to-device MQTT dispatch
    mqtt_manager.publish_actuator_command(actuator.farm_id, actuator.device_id, cmd_in.command)

    return cmd_record
