from typing import Optional
import datetime
from pydantic import BaseModel

class AcademicEventResponse(BaseModel):
    id: str
    student_id: str
    institution_id: str
    event_type: str
    event_title: str
    term: Optional[str] = None
    credits_reported: float = 0.0
    credits_validated: float = 0.0
    credit_status: str
    issuer_name: str
    source_reference: str
    metadata_json: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

