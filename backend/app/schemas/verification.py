from typing import Optional, Dict, Any
import datetime
from pydantic import BaseModel

class VerificationCreateRequest(BaseModel):
    student_id: str
    purpose: str = "EMPLOYMENT_OR_ACADEMIC_VERIFICATION"
    expires_in_hours: int = 72

class VerificationCreateResponse(BaseModel):
    reference_code: str
    verification_url: str
    qr_data_url: Optional[str] = None
    expires_at: datetime.datetime
    status: str

class VerificationCheckResponse(BaseModel):
    reference_code: str
    is_valid: bool
    status: str # VALID, EXPIRED, REVOKED, NOT_FOUND, TAMPERED
    rejection_reason: Optional[str] = None
    verified_at: datetime.datetime
    # Limited permitted disclosure fields only
    permitted_fields: Optional[Dict[str, Any]] = None
    signature_verified: bool
    signature: str
    issuer_institution: Optional[str] = None

