import datetime
import hmac
import hashlib
import io
import uuid
import base64
import qrcode
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.config import settings
from backend.app.models.student import Student
from backend.app.models.enrolment import Enrolment
from backend.app.models.institution import Institution
from backend.app.models.verification_ref import VerificationReference
from backend.app.services.audit_service import record_audit_event

def sign_verification_payload(payload_str: str) -> str:
    """Signs canonical verification payload with server secret key."""
    return hmac.new(
        settings.SIGNING_SECRET.encode("utf-8"),
        payload_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def generate_qr_base64(url: str) -> str:
    """Generates a QR code image as base64 data URI."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0F2B48", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_b64}"

def create_verification_reference(
    db: Session,
    student_id: str,
    purpose: str,
    expires_in_hours: int,
    user_context: dict,
    base_verify_url: str = "http://localhost:8000/api/v1/verify"
) -> Dict[str, Any]:
    """Generates an opaque, expiring verification reference token."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student ID '{student_id}' not found."
        )

    # Find primary active enrolment
    enrolment = db.query(Enrolment).filter(
        Enrolment.student_id == student.id,
        Enrolment.status == "ACTIVE"
    ).order_by(Enrolment.admission_date.desc()).first()

    issuer_inst = enrolment.institution_id if enrolment else "AICTE-CENTRAL"

    # Generate high-entropy opaque reference code
    ref_code = f"vref_{uuid.uuid4().hex[:12]}"
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours)

    canonical_data = f"{ref_code}|{student.id}|{issuer_inst}|{expires_at.isoformat()}"
    signature = sign_verification_payload(canonical_data)

    vref = VerificationReference(
        reference_code=ref_code,
        student_id=student.id,
        enrolment_id=enrolment.id if enrolment else None,
        issuer_institution_id=issuer_inst,
        purpose=purpose,
        expires_at=expires_at,
        is_revoked=False,
        signature=signature
    )
    db.add(vref)
    db.commit()
    db.refresh(vref)

    full_url = f"{base_verify_url}/{ref_code}"
    qr_b64 = generate_qr_base64(full_url)

    # Log audit event
    record_audit_event(
        db=db,
        actor_role=user_context.get("role", "student"),
        actor_id=user_context.get("user_id", "user@sutrayukti.gov.in"),
        action="CREATE_VERIFICATION_REFERENCE",
        entity_type="VERIFICATION_REFERENCE",
        entity_id=ref_code,
        institution_id=issuer_inst,
        metadata={"expires_at": expires_at.isoformat(), "purpose": purpose}
    )

    return {
        "reference_code": ref_code,
        "verification_url": full_url,
        "qr_data_url": qr_b64,
        "expires_at": expires_at,
        "status": "ACTIVE"
    }

def verify_reference_code(db: Session, reference_code: str, user_context: dict) -> Dict[str, Any]:
    """
    Evaluates verification reference. Checks expiry, revocation, and signature.
    Returns strictly permitted disclosure fields only.
    """
    now = datetime.datetime.utcnow()
    vref = db.query(VerificationReference).filter(VerificationReference.reference_code == reference_code).first()

    # Log verification attempt in audit trail
    record_audit_event(
        db=db,
        actor_role=user_context.get("role", "verifier"),
        actor_id=user_context.get("user_id", "verifier@company.org"),
        action="INSPECT_VERIFICATION_REFERENCE",
        entity_type="VERIFICATION_REFERENCE",
        entity_id=reference_code,
        institution_id=vref.issuer_institution_id if vref else None,
        metadata={"timestamp": now.isoformat()}
    )

    if not vref:
        return {
            "reference_code": reference_code,
            "is_valid": False,
            "status": "NOT_FOUND",
            "rejection_reason": "Verification reference does not exist.",
            "verified_at": now,
            "permitted_fields": None,
            "signature_verified": False,
            "signature": "",
            "issuer_institution": None
        }

    # Check Revocation
    if vref.is_revoked:
        return {
            "reference_code": reference_code,
            "is_valid": False,
            "status": "REVOKED",
            "rejection_reason": f"Credential reference was revoked by issuer. Reason: {vref.revocation_reason or 'Superseded'}",
            "verified_at": now,
            "permitted_fields": None,
            "signature_verified": True,
            "signature": vref.signature,
            "issuer_institution": vref.issuer_institution_id
        }

    # Check Expiration
    if vref.expires_at < now:
        return {
            "reference_code": reference_code,
            "is_valid": False,
            "status": "EXPIRED",
            "rejection_reason": f"Verification reference expired on {vref.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}.",
            "verified_at": now,
            "permitted_fields": None,
            "signature_verified": True,
            "signature": vref.signature,
            "issuer_institution": vref.issuer_institution_id
        }

    # Check Cryptographic Signature
    canonical_data = f"{vref.reference_code}|{vref.student_id}|{vref.issuer_institution_id}|{vref.expires_at.isoformat()}"
    expected_sig = sign_verification_payload(canonical_data)
    if not hmac.compare_digest(expected_sig, vref.signature):
        return {
            "reference_code": reference_code,
            "is_valid": False,
            "status": "TAMPERED",
            "rejection_reason": "Cryptographic signature mismatch. Token altered or forged.",
            "verified_at": now,
            "permitted_fields": None,
            "signature_verified": False,
            "signature": vref.signature,
            "issuer_institution": vref.issuer_institution_id
        }

    # Fetch permitted fields only
    student = db.query(Student).filter(Student.id == vref.student_id).first()
    enrolment = db.query(Enrolment).filter(Enrolment.id == vref.enrolment_id).first() if vref.enrolment_id else None
    institution = db.query(Institution).filter(Institution.id == vref.issuer_institution_id).first()

    permitted_fields = {
        "record_type": "AICTE_VERIFIED_STUDENT_ENROLMENT",
        "display_apaar_id": student.display_apaar_id if student else "DEMO-APAAR-****",
        "student_name": student.student_name if student else "Synthetic Demo Student",
        "institution_name": institution.name if institution else vref.issuer_institution_id,
        "institution_code": institution.code if institution else vref.issuer_institution_id,
        "programme_course": enrolment.course_code if enrolment else "Engineering",
        "academic_year": enrolment.academic_year if enrolment else "2025-2026",
        "enrolment_status": enrolment.status if enrolment else "ACTIVE",
        "verification_authority": "APAAR Verify by Sutrāyukti (AICTE Engine)",
        "synthetic_data_indicator": True
    }

    return {
        "reference_code": reference_code,
        "is_valid": True,
        "status": "VALID",
        "rejection_reason": None,
        "verified_at": now,
        "permitted_fields": permitted_fields,
        "signature_verified": True,
        "signature": vref.signature,
        "issuer_institution": institution.name if institution else vref.issuer_institution_id
    }

def revoke_verification_reference(db: Session, reference_code: str, reason: str, user_context: dict) -> VerificationReference:
    """Revokes an active verification reference."""
    vref = db.query(VerificationReference).filter(VerificationReference.reference_code == reference_code).first()
    if not vref:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reference not found.")

    vref.is_revoked = True
    vref.revocation_reason = reason
    db.commit()
    db.refresh(vref)

    record_audit_event(
        db=db,
        actor_role=user_context.get("role", "institution_officer"),
        actor_id=user_context.get("user_id", "officer@demo.edu.in"),
        action="REVOKE_VERIFICATION_REFERENCE",
        entity_type="VERIFICATION_REFERENCE",
        entity_id=reference_code,
        institution_id=vref.issuer_institution_id,
        metadata={"reason": reason}
    )
    return vref

