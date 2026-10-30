from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.student import Student
from backend.app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    ROLE_AICTE_ADMIN,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_STUDENT,
    ROLE_AUDITOR
)
from backend.app.services.audit_service import record_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])

class LoginRequest(BaseModel):
    email: str
    password: str

class UserProfileResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    institution_id: Optional[str] = None
    student_id: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str
    institution_id: Optional[str] = None
    student_id: Optional[str] = None
    user: Optional[UserProfileResponse] = None

@router.post("/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates a user and issues an authenticated session token.
    Enforces password verification against securely stored password hashes.
    """
    email_clean = credentials.email.lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. Please check your credentials."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact AICTE administrator."
        )

    token_data = {
        "sub": user.id,
        "email": user.email,
        "name": user.full_name,
        "role": user.role,
        "institution_id": user.institution_id,
        "student_id": user.student_id
    }
    token = create_access_token(token_data)

    # Log successful authentication in audit trail
    record_audit_event(
        db=db,
        actor_role=user.role,
        actor_id=user.email,
        action="USER_LOGIN_SUCCESS",
        entity_type="USER",
        entity_id=user.id,
        institution_id=user.institution_id,
        metadata={"client": "web_portal"}
    )

    user_prof = UserProfileResponse(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        institution_id=user.institution_id,
        student_id=user.student_id
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        institution_id=user.institution_id,
        student_id=user.student_id,
        user=user_prof
    )

@router.get("/me", response_model=UserProfileResponse)
def get_authenticated_profile(current_user: dict = Depends(get_current_user)):
    """Returns currently authenticated user profile and permissions."""
    return UserProfileResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=current_user.get("full_name", "User"),
        role=current_user["role"],
        institution_id=current_user.get("institution_id"),
        student_id=current_user.get("student_id")
    )
