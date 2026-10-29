from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.academic_event import AcademicEventResponse
from backend.app.services.auth_service import get_current_user
from backend.app.services.academic_journey_service import get_student_journey, add_academic_milestone

router = APIRouter(prefix="/academic-journey", tags=["Academic Journey"])

class AddMilestoneRequest(BaseModel):
    student_id: str
    institution_id: str
    event_type: str # ADMISSION_CONFIRMED, ENROLMENT_ACTIVE, SEMESTER_CREDITS, TRANSFER, QUALIFICATION_ISSUED
    event_title: str
    term: Optional[str] = None
    credits_reported: float = 0.0
    credits_validated: float = 0.0
    credit_status: str = "VALIDATED"
    issuer_name: str
    source_reference: str
    metadata_json: Optional[str] = None

@router.get("/{student_id}", response_model=List[AcademicEventResponse])
def get_journey(
    student_id: str,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Retrieves chronological Verified Academic Journey milestones for a student."""
    return get_student_journey(db, student_id)

@router.post("/events", response_model=AcademicEventResponse)
def create_milestone(
    req: AddMilestoneRequest,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Appends an issuer-originated academic milestone with credit status distinction."""
    return add_academic_milestone(
        db=db,
        student_id=req.student_id,
        institution_id=req.institution_id,
        event_type=req.event_type,
        event_title=req.event_title,
        term=req.term,
        credits_reported=req.credits_reported,
        credits_validated=req.credits_validated,
        credit_status=req.credit_status,
        issuer_name=req.issuer_name,
        source_reference=req.source_reference,
        metadata_json=req.metadata_json,
        user_context=user_context
    )

