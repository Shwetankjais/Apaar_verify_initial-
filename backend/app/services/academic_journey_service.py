from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.student import Student
from backend.app.models.academic_event import AcademicEvent
from backend.app.services.audit_service import record_audit_event

def get_student_journey(db: Session, student_id: str) -> List[AcademicEvent]:
    """Retrieves chronological timeline of academic milestones for a student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{student_id}' not found."
        )

    return db.query(AcademicEvent).filter(
        AcademicEvent.student_id == student.id
    ).order_by(AcademicEvent.timestamp.asc()).all()

def add_academic_milestone(
    db: Session,
    student_id: str,
    institution_id: str,
    event_type: str,
    event_title: str,
    term: Optional[str],
    credits_reported: float,
    credits_validated: float,
    credit_status: str,
    issuer_name: str,
    source_reference: str,
    metadata_json: Optional[str],
    user_context: dict
) -> AcademicEvent:
    """Adds an issuer-originated academic milestone with credit status accounting."""
    event = AcademicEvent(
        student_id=student_id,
        institution_id=institution_id,
        event_type=event_type,
        event_title=event_title,
        term=term,
        credits_reported=credits_reported,
        credits_validated=credits_validated,
        credit_status=credit_status,
        issuer_name=issuer_name,
        source_reference=source_reference,
        metadata_json=metadata_json
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    record_audit_event(
        db=db,
        actor_role=user_context.get("role", "institution_officer"),
        actor_id=user_context.get("user_id", "officer@demo.edu.in"),
        action=f"ADD_ACADEMIC_EVENT_{event_type}",
        entity_type="ACADEMIC_EVENT",
        entity_id=event.id,
        institution_id=institution_id,
        metadata={"term": term, "credits_validated": credits_validated, "credit_status": credit_status}
    )
    return event

