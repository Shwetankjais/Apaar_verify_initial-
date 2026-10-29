import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from backend.app.database import Base

class ValidationIssue(Base):
    __tablename__ = "validation_issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("submissions.id"), index=True, nullable=True)
    institution_id = Column(String(50), ForeignKey("institutions.id"), index=True, nullable=False)
    row_number = Column(Integer, nullable=False)
    rule_code = Column(String(20), index=True, nullable=False) # e.g. V001 to V010
    severity = Column(String(20), index=True, nullable=False) # ERROR, REVIEW_REQUIRED, WARNING
    student_apaar = Column(String(50), nullable=True)
    field_name = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    suggested_correction = Column(Text, nullable=True)
    # Status: OPEN, IN_REVIEW, RESOLVED, DISMISSED
    status = Column(String(50), default="OPEN", index=True)
    reviewer_comment = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

