import datetime
from sqlalchemy import Column, String, DateTime
from backend.app.database import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(50), primary_key=True, index=True) # e.g. "DEMO001"
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    state = Column(String(100), nullable=False)
    district = Column(String(100), nullable=True)
    approval_status = Column(String(50), default="APPROVED")
    contact_email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

