import hashlib
import hmac
from typing import Optional
from fastapi import Header, HTTPException, status
from backend.app.config import settings

# Supported Roles
ROLE_AICTE_ADMIN = "aicte_admin"
ROLE_INSTITUTION_OFFICER = "institution_officer"
ROLE_STUDENT = "student"
ROLE_VERIFIER = "verifier"
ROLE_AUDITOR = "auditor"

def generate_apaar_lookup_token(raw_apaar: str) -> str:
    """Generate a keyed HMAC lookup token to prevent rainbow-table indexing while supporting exact matches."""
    return hmac.new(
        settings.APAAR_SALT.encode("utf-8"),
        raw_apaar.strip().upper().encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def mask_apaar_id(raw_apaar: str) -> str:
    """Mask synthetic APAAR identifier for safe display: DEMO-APAAR-0001 -> DEMO-APAAR-***1"""
    val = raw_apaar.strip()
    if len(val) >= 4:
        return val[:-4] + "***" + val[-1]
    return "***"

def get_current_user(
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_institution_id: Optional[str] = Header(None, alias="X-Institution-Id")
):
    """
    Extracts authenticated user context from request headers.
    In production this verifies a signed JWT or mTLS cert.
    In the demo prototype, explicit synthetic headers allow seamless role-switching.
    """
    role = (x_user_role or ROLE_AICTE_ADMIN).lower()
    user_id = x_user_id or f"{role}@sutrayukti.gov.in"
    institution_id = x_institution_id
    
    return {
        "role": role,
        "user_id": user_id,
        "institution_id": institution_id
    }

def verify_institution_access(user_context: dict, target_institution_id: str):
    """Enforces institution tenant scoping. Institution officers can ONLY access their own institution."""
    role = user_context["role"]
    if role in [ROLE_AICTE_ADMIN, ROLE_AUDITOR]:
        return # Regulators and auditors have cross-institution oversight
    if role == ROLE_INSTITUTION_OFFICER:
        user_inst = user_context.get("institution_id")
        if not user_inst or user_inst != target_institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Institution officer for '{user_inst}' cannot access data for '{target_institution_id}'."
            )

