import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.app.database import Base

class ApprovedIntake(Base):
    __tablename__ = "approved_intakes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    institution_id = Column(String(50), ForeignKey("institutions.id"), index=True, nullable=False)
    course_code = Column(String(50), index=True, nullable=False) # e.g. "CSE", "ECE"
    academic_year = Column(String(20), index=True, nullable=False) # e.g. "2025-2026"
    regular_intake = Column(Integer, nullable=False, default=30)
    supernumerary_intake = Column(Integer, nullable=False, default=3)
    rule_version = Column(String(50), default="APH-2024-2027-V1")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

