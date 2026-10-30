from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.audit_event import AuditEvent
from backend.app.schemas.audit_event import AuditEventResponse
from backend.app.services.auth_service import (
    require_roles,
    ROLE_AICTE_ADMIN,
    ROLE_AUDITOR,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_INSTITUTION_OFFICER
)

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

ALLOWED_AUDIT_ROLES = [
    ROLE_AICTE_ADMIN,
    ROLE_AUDITOR,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_INSTITUTION_OFFICER
]

@router.get("", response_model=List[AuditEventResponse])
def list_audit_events(
    institution_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_context: dict = Depends(require_roles(ALLOWED_AUDIT_ROLES))
):
    """
    Returns tamper-evident audit logs.
    Auditors and AICTE admin see national logs.
    Institution staff are strictly restricted to their own institution's events.
    Students and public users are strictly blocked.
    """
    role = user_context["role"]
    query = db.query(AuditEvent)

    if role in [ROLE_INSTITUTION_ADMIN, ROLE_INSTITUTION_APPROVER, ROLE_INSTITUTION_OFFICER] and user_context.get("institution_id"):
        query = query.filter(AuditEvent.institution_id == user_context["institution_id"])
    elif institution_id:
        query = query.filter(AuditEvent.institution_id == institution_id)

    if action:
        query = query.filter(AuditEvent.action == action)

    return query.order_by(AuditEvent.timestamp.desc()).limit(limit).all()
