from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.validation_issue import ValidationIssueResponse, ValidationIssueUpdate
from backend.app.models.validation_issue import ValidationIssue
from backend.app.services.auth_service import (
    require_roles,
    ROLE_AICTE_ADMIN,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_INSTITUTION_OFFICER,
    ROLE_AUDITOR
)
from backend.app.services.exception_service import get_exceptions_list, resolve_exception

router = APIRouter(prefix="/exceptions", tags=["Exceptions & Review"])

ALLOWED_EXCEPTION_VIEW_ROLES = [
    ROLE_AICTE_ADMIN,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_INSTITUTION_OFFICER,
    ROLE_AUDITOR
]

ALLOWED_EXCEPTION_EDIT_ROLES = [
    ROLE_AICTE_ADMIN,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_INSTITUTION_OFFICER
]

@router.get("", response_model=List[ValidationIssueResponse])
def list_exceptions(
    institution_id: Optional[str] = None,
    rule_code: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_context: dict = Depends(require_roles(ALLOWED_EXCEPTION_VIEW_ROLES))
):
    """Lists exceptions in the centralized queue. Officers only see their own institution's issues."""
    role = user_context["role"]
    inst_filter = institution_id
    if role in [ROLE_INSTITUTION_ADMIN, ROLE_INSTITUTION_APPROVER, ROLE_INSTITUTION_OFFICER] and user_context.get("institution_id"):
        inst_filter = user_context["institution_id"]

    return get_exceptions_list(
        db=db,
        institution_id=inst_filter,
        rule_code=rule_code,
        status_filter=status_filter,
        limit=limit
    )

@router.patch("/{id}", response_model=ValidationIssueResponse)
def update_exception(
    id: str,
    update_data: ValidationIssueUpdate,
    db: Session = Depends(get_db),
    user_context: dict = Depends(require_roles(ALLOWED_EXCEPTION_EDIT_ROLES))
):
    """Adjudicates an exception with mandatory human explanation and logs an audit event."""
    issue = db.query(ValidationIssue).filter(ValidationIssue.id == id).first()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found.")

    role = user_context["role"]
    if role in [ROLE_INSTITUTION_ADMIN, ROLE_INSTITUTION_APPROVER, ROLE_INSTITUTION_OFFICER]:
        if user_context.get("institution_id") != issue.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot adjudicate exceptions belonging to another institution."
            )

    return resolve_exception(
        db=db,
        issue_id=id,
        new_status=update_data.status,
        reviewer_comment=update_data.reviewer_comment,
        user_context=user_context
    )
