from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.validation_issue import ValidationIssueResponse, ValidationIssueUpdate
from backend.app.services.auth_service import get_current_user
from backend.app.services.exception_service import get_exceptions_list, resolve_exception

router = APIRouter(prefix="/exceptions", tags=["Exceptions & Review"])

@router.get("", response_model=List[ValidationIssueResponse])
def list_exceptions(
    institution_id: Optional[str] = None,
    rule_code: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Lists exceptions in the centralized queue. Officers only see their own institution's issues."""
    role = user_context["role"]
    inst_filter = institution_id
    if role == "institution_officer" and user_context.get("institution_id"):
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
    user_context: dict = Depends(get_current_user)
):
    """Adjudicates an exception with mandatory human explanation and logs an audit event."""
    return resolve_exception(
        db=db,
        issue_id=id,
        new_status=update_data.status,
        reviewer_comment=update_data.reviewer_comment,
        user_context=user_context
    )

