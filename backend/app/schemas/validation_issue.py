from typing import Optional
import datetime
from pydantic import BaseModel

class ValidationIssueResponse(BaseModel):
    id: Optional[str] = None
    submission_id: Optional[str] = None
    institution_id: Optional[str] = None
    row_number: int
    rule_code: str
    severity: str
    student_apaar: Optional[str] = None
    field_name: Optional[str] = None
    message: str
    suggested_correction: Optional[str] = None
    status: str = "OPEN"
    reviewer_comment: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime.datetime] = None
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class ValidationIssueUpdate(BaseModel):
    status: str # RESOLVED, DISMISSED, IN_REVIEW
    reviewer_comment: str
