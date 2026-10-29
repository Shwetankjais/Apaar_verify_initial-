import datetime
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from backend.app.database import Base

class Enrolment(Base):
    __tablename__ = "enrolments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = Column(String(36), ForeignKey("students.id"), index=True, nullable=False)
    institution_id = Column(String(50), ForeignKey("institutions.id"), index=True, nullable=False)
    institution_student_id = Column(String(100), nullable=False)
    course_code = Column(String(50), index=True, nullable=False)
    academic_year = Column(String(20), index=True, nullable=False)
    admission_date = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False, default="GENERAL") # GENERAL, SC, ST, OBC, EWS
    seat_type = Column(String(50), nullable=False, default="REGULAR") # REGULAR, TFW, PMSSS, NRI, SUPERNUMERARY
    status = Column(String(50), default="ACTIVE", index=True) # ACTIVE, TRANSFERRED, WITHDRAWN, COMPLETED
    is_nri_oci_fn = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

