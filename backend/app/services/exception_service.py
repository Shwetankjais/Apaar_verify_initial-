import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.validation_issue import ValidationIssue
from backend.app.services.audit_service import record_audit_event

def get_exceptions_list(
    db: Session,
    institution_id: Optional[str] = None,
    rule_code: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100
) -> List[ValidationIssue]:
    query = db.query(ValidationIssue)
    if institution_id:
        query = query.filter(ValidationIssue.institution_id == institution_id)
    if rule_code:
        query = query.filter(ValidationIssue.rule_code == rule_code)
    if status_filter:
        query = query.filter(ValidationIssue.status == status_filter)
    return query.order_by(ValidationIssue.created_at.desc()).limit(limit).all()

def resolve_exception(
    db: Session,
    issue_id: str,
    new_status: str,
    reviewer_comment: str,
    user_context: dict
) -> ValidationIssue:
    issue = db.query(ValidationIssue).filter(ValidationIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation exception with ID '{issue_id}' not found."
        )

    issue.status = new_status
    issue.reviewer_comment = reviewer_comment
    issue.resolved_by = user_context.get("user_id", "admin@aicte.gov.in")
    issue.resolved_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(issue)

    # Record tamper-evident audit event
    record_audit_event(
        db=db,
        actor_role=user_context.get("role", "aicte_admin"),
        actor_id=user_context.get("user_id", "admin@aicte.gov.in"),
        action=f"RESOLVE_EXCEPTION_{new_status}",
        entity_type="VALIDATION_ISSUE",
        entity_id=issue.id,
        institution_id=issue.institution_id,
        metadata={
            "rule_code": issue.rule_code,
            "comment": reviewer_comment,
            "new_status": new_status
        }
    )

    return issue

