from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas.verification import (
    VerificationCreateRequest,
    VerificationCreateResponse,
    VerificationCheckResponse
)
from backend.app.services.auth_service import get_current_user
from backend.app.services.verification_service import (
    create_verification_reference,
    verify_reference_code,
    revoke_verification_reference
)

router = APIRouter(tags=["Verification & QR"])

@router.post("/api/v1/verification-requests", response_model=VerificationCreateResponse)
def request_verification_token(
    request: VerificationCreateRequest,
    req: Request,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Generates an opaque, expiring verification reference with a QR code data URL."""
    base_url = str(req.base_url).rstrip("/") + "/api/v1/verify"
    return create_verification_reference(
        db=db,
        student_id=request.student_id,
        purpose=request.purpose,
        expires_in_hours=request.expires_in_hours,
        user_context=user_context,
        base_verify_url=base_url
    )

@router.get("/api/v1/verify/{reference}", response_model=VerificationCheckResponse)
def check_verification_reference(
    reference: str,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """
    Publicly accessible verification endpoint.
    Returns strictly limited, permitted academic fields.
    Validates cryptographic signature, expiry, and revocation.
    """
    return verify_reference_code(db, reference, user_context)

@router.post("/api/v1/verify/{reference}/revoke")
def revoke_reference(
    reference: str,
    reason: str = "Superseded by updated academic record",
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Revokes an active verification reference."""
    vref = revoke_verification_reference(db, reference, reason, user_context)
    return {"status": "REVOKED", "reference_code": vref.reference_code, "reason": reason}

