import datetime
import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from backend.app.database import Base

class AcademicEvent(Base):
    __tablename__ = "academic_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id"), index=True, nullable=False)
    institution_id = Column(String(50), ForeignKey("institutions.id"), index=True, nullable=False)
    # Event types: ADMISSION_CONFIRMED, ENROLMENT_ACTIVE, SEMESTER_CREDITS, TRANSFER, QUALIFICATION_ISSUED
    event_type = Column(String(50), nullable=False, index=True)
    event_title = Column(String(200), nullable=False)
    term = Column(String(50), nullable=True) # e.g. "Semester 1", "2025-26 Term 1"
    credits_reported = Column(Float, default=0.0)
    credits_validated = Column(Float, default=0.0)
    # Credit status: REPORTED, VALIDATED, EARNED, ACCEPTED
    credit_status = Column(String(50), default="VALIDATED")
    issuer_name = Column(String(200), nullable=False)
    source_reference = Column(String(100), nullable=False)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

