from sqlalchemy.orm import Session
from app.models.audit import AuditLog

def record_audit(
    db: Session,
    user_id: int,
    username: str,
    action: str,
    target_type: str,
    target_id: int,
    details: str | None = None
) -> None:
    """
    Helper function to record an audit log entry.
    """
    audit_entry = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details
    )
    db.add(audit_entry)
    # We do NOT commit here. The caller should commit its own transaction
    # which will then include this audit log insertion atomically.
