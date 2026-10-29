from typing import List, Optional
from pydantic import BaseModel

class InstitutionBase(BaseModel):
    id: str
    code: str
    name: str
    state: str
    district: Optional[str] = None
    approval_status: str = "APPROVED"
    contact_email: Optional[str] = None

class InstitutionResponse(InstitutionBase):
    courses: List[str] = []

    class Config:
        from_attributes = True

