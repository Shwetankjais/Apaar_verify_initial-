import datetime
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    # Roles: aicte_admin, institution_admin, institution_approver, student, auditor
    role = Column(String(50), nullable=False, index=True)
    # Tenant scoping: if institution staff, which institution they belong to
    institution_id = Column(String(50), ForeignKey("institutions.id"), nullable=True)
    # If student, link to student master record
    student_id = Column(String(36), ForeignKey("students.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

