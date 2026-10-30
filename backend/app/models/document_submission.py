import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from backend.app.database import Base

class DocumentSubmission(Base):
    __tablename__ = "document_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_no = Column(String(50), unique=True, index=True, nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=True, index=True)
    student_name = Column(String(150), nullable=False)
    student_apaar = Column(String(50), nullable=False)
    institution_id = Column(String(50), ForeignKey("institutions.id"), nullable=False, index=True)
    course_code = Column(String(50), nullable=False)
    academic_year = Column(String(20), nullable=False)
    document_type = Column(String(100), nullable=False) # CLASS_12_MARKSHEET, TRANSFER_CERTIFICATE, DEGREE_DIPLOMA, IDENTITY_PROOF
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False)
    # Workflow states: DRAFT, SUBMITTED, UNDER_REVIEW, DEFICIENCY_RAISED, RESUBMITTED, APPROVED, REJECTED
    status = Column(String(50), default="SUBMITTED", index=True)
    deficiency_notes = Column(Text, nullable=True)
    reviewer_id = Column(String(100), nullable=True)
    reviewer_comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

