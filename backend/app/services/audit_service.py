import datetime

from sqlalchemy.orm import Session

from backend.app.models import AuditLog


def log_security_event(
    db: Session,
    event_type: str,
    actor_type: str,
    actor_id: str,
    action: str,
    resource: str,
    result: str,
    severity: str = "INFO",
    ip_address: str | None = None,
    details: str | None = None
) -> AuditLog:
    """Records an immutable security/audit log event."""
    log_entry = AuditLog(
        timestamp=datetime.datetime.utcnow(),
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        resource=resource,
        result=result,
        severity=severity,
        ip_address=ip_address,
        details=details
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry
