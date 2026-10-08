import datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_role
from backend.app.models import Threshold, User
from backend.app.schemas import ThresholdResponse, ThresholdUpdate
from backend.app.services.audit_service import log_security_event

router = APIRouter(prefix="/thresholds", tags=["Thresholds"])


@router.get("", response_model=ThresholdResponse)
def get_farm_thresholds(
    farm_id: str = "farm_1",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View farm thresholds (Accessible to all authenticated roles)"""
    threshold = db.query(Threshold).filter(Threshold.farm_id == farm_id).first()
    if not threshold:
        # Create default thresholds if not present
        threshold = Threshold(
            farm_id=farm_id,
            soil_moisture_min=30.0,
            soil_moisture_target=60.0,
            temperature_min=18.0,
            temperature_max=32.0,
            humidity_min=40.0,
            humidity_max=85.0,
            water_level_safe_min=15.0,
            max_pump_runtime_seconds=600,
            updated_by="SYSTEM_DEFAULT"
        )
        db.add(threshold)
        db.commit()
        db.refresh(threshold)
    return threshold


@router.put("/{farm_id}", response_model=ThresholdResponse)
def update_farm_thresholds(
    farm_id: str,
    threshold_in: ThresholdUpdate,
    request: Request,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Update farm thresholds.
    Strictly restricted to ADMIN role.
    Logged to immutable audit log.
    """
    client_ip = request.client.host if request.client else "unknown"
    threshold = db.query(Threshold).filter(Threshold.farm_id == farm_id).first()
    if not threshold:
        threshold = Threshold(farm_id=farm_id)
        db.add(threshold)

    old_values = {
        "soil_moisture_min": threshold.soil_moisture_min,
        "soil_moisture_target": threshold.soil_moisture_target,
        "temperature_min": threshold.temperature_min,
        "temperature_max": threshold.temperature_max,
        "humidity_min": threshold.humidity_min,
        "humidity_max": threshold.humidity_max,
        "water_level_safe_min": threshold.water_level_safe_min,
    }

    # Apply validated updates
    threshold.soil_moisture_min = threshold_in.soil_moisture_min
    threshold.soil_moisture_target = threshold_in.soil_moisture_target
    threshold.temperature_min = threshold_in.temperature_min
    threshold.temperature_max = threshold_in.temperature_max
    threshold.humidity_min = threshold_in.humidity_min
    threshold.humidity_max = threshold_in.humidity_max
    threshold.water_level_safe_min = threshold_in.water_level_safe_min
    threshold.max_pump_runtime_seconds = threshold_in.max_pump_runtime_seconds
    threshold.updated_at = datetime.datetime.utcnow()
    threshold.updated_by = current_user.username

    db.commit()
    db.refresh(threshold)

    # Immutable Audit Log
    log_security_event(
        db=db,
        event_type="THRESHOLD_CONFIG_MODIFIED",
        actor_type="USER",
        actor_id=current_user.username,
        action="UPDATE_THRESHOLDS",
        resource=f"farm:{farm_id}:thresholds",
        result="SUCCESS",
        severity="INFO",
        ip_address=client_ip,
        details=f"Thresholds modified. Old: {old_values} -> New: {threshold_in.dict()}"
    )

    return threshold
