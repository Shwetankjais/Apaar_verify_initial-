from typing import List, Dict, Any, Optional
import datetime
from pydantic import BaseModel
from backend.app.schemas.validation_issue import ValidationIssueResponse

class SubmissionRowPreview(BaseModel):
    row_number: int
    data: Dict[str, Any]
    outcome: str # ELIGIBLE, REVIEW_REQUIRED, REJECTED
    issues: List[ValidationIssueResponse] = []

class SubmissionPreviewResponse(BaseModel):
    batch_key: str
    institution_id: str
    academic_year: str
    total_rows: int
    eligible_count: int
    review_required_count: int
    rejected_count: int
    issues: List[ValidationIssueResponse]
    rows: List[SubmissionRowPreview]

class SubmissionCommitRequest(BaseModel):
    batch_key: str
    institution_id: str
    academic_year: str
    file_name: str
    rows: List[Dict[str, Any]]

class SubmissionResponse(BaseModel):
    id: str
    batch_key: str
    institution_id: str
    academic_year: str
    file_name: str
    total_rows: int
    eligible_rows: int
    review_required_rows: int
    rejected_rows: int
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

