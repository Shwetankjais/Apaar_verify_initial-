import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from backend.app.database import Base

class VerificationReference(Base):
    __tablename__ = "verification_references"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Opaque URL-safe reference token, e.g. "vref_a8f9c2d1e0"
    reference_code = Column(String(100), unique=True, index=True, nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), index=True, nullable=False)
    enrolment_id = Column(String(36), ForeignKey("enrolments.id"), index=True, nullable=True)
    issuer_institution_id = Column(String(50), ForeignKey("institutions.id"), nullable=False)
    purpose = Column(String(100), default="EMPLOYMENT_OR_ACADEMIC_VERIFICATION")
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    revocation_reason = Column(String(255), nullable=True)
    # Server-generated cryptographic signature
    signature = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

