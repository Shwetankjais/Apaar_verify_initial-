import datetime
import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from backend.app.database import Base

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_key = Column(String(100), unique=True, index=True, nullable=False)
    institution_id = Column(String(50), ForeignKey("institutions.id"), index=True, nullable=False)
    academic_year = Column(String(20), nullable=False)
    file_name = Column(String(255), nullable=False)
    total_rows = Column(Integer, default=0)
    eligible_rows = Column(Integer, default=0)
    review_required_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    # Status: DRAFT, VALIDATING, ACCEPTED, PARTIALLY_ACCEPTED, REJECTED
    status = Column(String(50), default="ACCEPTED", index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

