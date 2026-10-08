from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user
from backend.app.models import Device, SensorReading, Threshold, User
from backend.app.schemas import SensorReadingCreate, SensorReadingResponse
from backend.app.services.threshold_engine import ThresholdEngine
from backend.app.services.validation_service import SensorDataValidationService

router = APIRouter(prefix="/sensors", tags=["Sensors"])


def compute_sensor_state(sensor_type: str, value: float, threshold: Threshold | None) -> str:
    """Computes whether reading is NORMAL, WARNING, or CRITICAL"""
    if not threshold:
        return "NORMAL"

    if sensor_type == "soil_moisture":
        if value < threshold.soil_moisture_min:
            return "WARNING"
        return "NORMAL"
    elif sensor_type == "water_level":
        if value < threshold.water_level_safe_min:
            return "CRITICAL"
        elif value < threshold.water_level_safe_min + 10.0:
            return "WARNING"
        return "NORMAL"
    elif sensor_type == "temperature":
        if value > threshold.temperature_max or value < threshold.temperature_min:
            return "WARNING"
        return "NORMAL"
    elif sensor_type == "humidity":
        if value > threshold.humidity_max or value < threshold.humidity_min:
            return "WARNING"
        return "NORMAL"

    return "NORMAL"


@router.get("", response_model=list[dict[str, Any]])
def get_latest_sensor_readings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns latest readings for each active sensor, including status badge
    (NORMAL / WARNING / CRITICAL).
    """
    devices = db.query(Device).filter(Device.device_type.in_(["soil_moisture", "environmental", "water_level"])).all()
    results = []

    for dev in devices:
        threshold = db.query(Threshold).filter(Threshold.farm_id == dev.farm_id).first()
        readings = (
            db.query(SensorReading)
            .filter(SensorReading.device_id == dev.id, SensorReading.is_valid == True)
            .order_by(SensorReading.timestamp.desc())
            .limit(5)
            .all()
        )
        latest = readings[0] if readings else None

        status_state = "NORMAL"
        val = None
        unit = ""
        stype = dev.device_type
        if latest:
            val = latest.value
            unit = latest.unit
            stype = latest.sensor_type
            status_state = compute_sensor_state(stype, val, threshold)

        results.append({
            "device_id": dev.id,
            "device_name": dev.device_name,
            "farm_id": dev.farm_id,
            "device_status": dev.status,
            "sensor_type": stype,
            "current_value": val,
            "unit": unit,
            "state": status_state,
            "last_seen": dev.last_seen,
            "recent_readings": [{"value": r.value, "timestamp": r.timestamp} for r in readings]
        })

    return results


@router.get("/{device_id}/readings", response_model=list[SensorReadingResponse])
def get_sensor_history(
    device_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns historical readings for a specific device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == device_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )
    return readings


@router.post("/reading", response_model=SensorReadingResponse)
def submit_sensor_reading(
    request: Request,
    reading_in: SensorReadingCreate,
    db: Session = Depends(get_db)
):
    """
    Direct endpoint for sensor ingestion (validated through security pipeline).
    Does not require user JWT because devices authenticate via auth_token in payload.
    """
    client_ip = request.client.host if request.client else "unknown"

    # Multi-layer validation
    is_valid, reason = SensorDataValidationService.validate_and_sanitize(
        db=db,
        reading_in=reading_in,
        client_ip=client_ip
    )

    reading = SensorReading(
        device_id=reading_in.device_id,
        farm_id=reading_in.farm_id,
        sensor_type=reading_in.sensor_type,
        value=reading_in.value,
        unit=reading_in.unit,
        timestamp=reading_in.timestamp,
        is_valid=is_valid,
        rejection_reason=reason
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sensor reading rejected: {reason}"
        )

    # Evaluate thresholds
    ThresholdEngine.evaluate(
        db=db,
        farm_id=reading_in.farm_id,
        sensor_type=reading_in.sensor_type,
        current_value=reading_in.value
    )

    return reading
