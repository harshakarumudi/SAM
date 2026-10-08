import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import get_current_user, require_role
from backend.app.models import Alert, User
from backend.app.schemas import AlertResponse

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=list[AlertResponse])
def get_alerts(
    farm_id: str = "farm_1",
    resolved: bool | None = None,
    severity: str | None = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """View alerts with optional filters by resolution state and severity"""
    query = db.query(Alert).filter(Alert.farm_id == farm_id)
    if resolved is not None:
        query = query.filter(Alert.resolved == resolved)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
def resolve_alert(
    alert_id: int,
    current_user: User = Depends(require_role(["ADMIN", "OPERATOR"])),
    db: Session = Depends(get_db)
):
    """Resolve an active alert (Admin & Operator only)"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.resolved = True
    alert.resolved_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
