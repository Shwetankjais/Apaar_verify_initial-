import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Text
from backend.app.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_role = Column(String(50), nullable=False) # e.g. aicte_admin, institution_officer, verifier
    actor_id = Column(String(100), nullable=False) # username or email
    action = Column(String(100), nullable=False) # e.g. UPLOAD_BATCH, RESOLVE_EXCEPTION, VERIFY_RECORD
    entity_type = Column(String(50), nullable=False) # SUBMISSION, ENROLMENT, EXCEPTION, VERIFICATION_REF
    entity_id = Column(String(100), nullable=False)
    institution_id = Column(String(50), nullable=True)
    previous_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)
    metadata_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

