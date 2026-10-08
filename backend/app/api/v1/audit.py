
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import require_role
from backend.app.models import AuditLog, User
from backend.app.schemas import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(
    event_type: str | None = None,
    severity: str | None = None,
    limit: int = 100,
    current_user: User = Depends(require_role(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Access security audit logs.
    Strictly restricted to ADMIN role.
    Viewers and Operators receive 403 Forbidden.
    """
    query = db.query(AuditLog)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if severity:
        query = query.filter(AuditLog.severity == severity.upper())
    return query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
