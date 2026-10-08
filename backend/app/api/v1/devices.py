import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, hash_device_token, require_role
from backend.app.models import Device, User
from backend.app.schemas import DeviceCreate, DeviceResponse
from backend.app.services.audit_service import log_security_event

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceResponse])
def get_devices(
    farm_id: str = "farm_1",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all registered devices on the farm"""
    return db.query(Device).filter(Device.farm_id == farm_id).all()


@router.post("", response_model=DeviceResponse)
def register_device(
    device_in: DeviceCreate,
    request: Request,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Register a new IoT device (Admin only)"""
    client_ip = request.client.host if request.client else "unknown"
    existing = db.query(Device).filter(Device.id == device_in.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device ID already registered")

    device = Device(
        id=device_in.id,
        farm_id=device_in.farm_id,
        device_name=device_in.device_name,
        device_type=device_in.device_type,
        status="active",
        auth_token_hash=hash_device_token(device_in.auth_secret),
        created_at=datetime.datetime.utcnow()
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    log_security_event(
        db=db,
        event_type="DEVICE_REGISTER",
        actor_type="USER",
        actor_id=current_user.username,
        action="REGISTER_DEVICE",
        resource=f"device:{device.id}",
        result="SUCCESS",
        severity="INFO",
        ip_address=client_ip,
        details=f"Device {device.id} ({device.device_type}) registered"
    )

    return device


@router.post("/{device_id}/suspend", response_model=DeviceResponse)
def suspend_device(
    device_id: str,
    request: Request,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Administratively suspend a compromised or untrusted device.
    A suspended device cannot submit valid telemetry.
    """
    client_ip = request.client.host if request.client else "unknown"
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = "suspended"
    db.commit()
    db.refresh(device)

    log_security_event(
        db=db,
        event_type="DEVICE_SUSPEND",
        actor_type="USER",
        actor_id=current_user.username,
        action="SUSPEND_DEVICE",
        resource=f"device:{device_id}",
        result="SUCCESS",
        severity="WARNING",
        ip_address=client_ip,
        details=f"Admin {current_user.username} suspended device {device_id}"
    )

    return device


@router.post("/{device_id}/activate", response_model=DeviceResponse)
def activate_device(
    device_id: str,
    request: Request,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """Reactivate a previously suspended device (Admin only)"""
    client_ip = request.client.host if request.client else "unknown"
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.status = "active"
    db.commit()
    db.refresh(device)

    log_security_event(
        db=db,
        event_type="DEVICE_ACTIVATE",
        actor_type="USER",
        actor_id=current_user.username,
        action="ACTIVATE_DEVICE",
        resource=f"device:{device_id}",
        result="SUCCESS",
        severity="INFO",
        ip_address=client_ip,
        details=f"Admin {current_user.username} reactivated device {device_id}"
    )

    return device
