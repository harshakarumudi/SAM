import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import Alert, Device
from backend.app.schemas import HealthResponse
from backend.app.services.mqtt_service import mqtt_manager

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint reporting database, MQTT, and system status.
    Designed for Kubernetes and Docker container liveness/readiness probes.
    """
    # Test database connectivity
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    mqtt_status = "connected" if mqtt_manager.is_connected else "offline_or_reconnecting"

    active_devices = db.query(Device).filter(Device.status == "active").count()
    active_alerts = db.query(Alert).filter(Alert.resolved == False).count()

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.datetime.utcnow(),
        database=db_status,
        mqtt=mqtt_status,
        active_devices_count=active_devices,
        active_alerts_count=active_alerts
    )
