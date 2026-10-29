import datetime
import uuid
from sqlalchemy import Column, String, DateTime
from backend.app.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Protected cryptographic lookup token to avoid searching on raw plaintext APAAR
    apaar_lookup_token = Column(String(64), unique=True, index=True, nullable=False)
    # Masked synthetic display identifier, e.g. "DEMO-APAAR-***1"
    display_apaar_id = Column(String(50), nullable=False)
    # Synthetic display name
    student_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

