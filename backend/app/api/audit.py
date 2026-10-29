from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.audit_event import AuditEvent
from backend.app.schemas.audit_event import AuditEventResponse
from backend.app.services.auth_service import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("", response_model=List[AuditEventResponse])
def list_audit_events(
    institution_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Returns tamper-evident audit logs. Scoped by institution if user is an institutional officer."""
    role = user_context["role"]
    query = db.query(AuditEvent)

    if role == "institution_officer" and user_context.get("institution_id"):
        query = query.filter(AuditEvent.institution_id == user_context["institution_id"])
    elif institution_id:
        query = query.filter(AuditEvent.institution_id == institution_id)

    if action:
        query = query.filter(AuditEvent.action == action)

    return query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()

