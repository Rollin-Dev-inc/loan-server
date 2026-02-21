from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.deps import CurrentAdmin, DBSession
from app.models.audit import AuditLog

router = APIRouter(prefix="/audits", tags=["Audits"])

@router.get("/")
def get_audits(db: DBSession, admin: CurrentAdmin) -> List[dict]:
    # Mengambil top 200 audit log terbaru (diurutkan berdasarkan created_at secara menurun)
    audits = db.scalars(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    ).all()
    
    # Map raw ORM result to dict needed for simplistic response 
    # (Since we didn't define a Pydantic schema for AuditLog outbound response)
    result = []
    for audit in audits:
        result.append({
            "id": audit.id,
            "user_id": audit.user_id,
            "username": audit.username,
            "action": audit.action,
            "target_type": audit.target_type,
            "target_id": audit.target_id,
            "details": audit.details,
            "timestamp": audit.created_at.isoformat() if audit.created_at else None
        })
        
    return result
