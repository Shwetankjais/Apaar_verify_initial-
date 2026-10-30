from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.institution import Institution
from backend.app.models.intake import ApprovedIntake
from backend.app.schemas.institution import InstitutionResponse
from backend.app.schemas.intake import InstitutionIntakeSummary
from backend.app.services.auth_service import get_optional_current_user, verify_institution_access
from backend.app.services.intake_service import get_institution_intake_summary

router = APIRouter(prefix="/institutions", tags=["Institutions"])

@router.get("", response_model=List[InstitutionResponse])
def list_institutions(
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_optional_current_user)
):
    """Lists institutions visible to the current role. Officers only see their own institution."""
    query = db.query(Institution)
    role = user_context["role"]
    if role in ["institution_officer", "institution_admin", "institution_approver"] and user_context.get("institution_id"):
        query = query.filter(Institution.id == user_context["institution_id"])
    
    insts = query.all()
    results = []
    for inst in insts:
        courses = [r[0] for r in db.query(ApprovedIntake.course_code).filter(ApprovedIntake.institution_id == inst.id).distinct().all()]
        results.append(InstitutionResponse(
            id=inst.id,
            code=inst.code,
            name=inst.name,
            state=inst.state,
            district=inst.district,
            approval_status=inst.approval_status,
            contact_email=inst.contact_email,
            courses=courses
        ))
    return results

@router.get("/{id}", response_model=InstitutionResponse)
def get_institution(
    id: str,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_optional_current_user)
):
    verify_institution_access(user_context, id)
    inst = db.query(Institution).filter(Institution.id == id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Institution '{id}' not found.")
    
    courses = [r[0] for r in db.query(ApprovedIntake.course_code).filter(ApprovedIntake.institution_id == inst.id).distinct().all()]
    return InstitutionResponse(
        id=inst.id,
        code=inst.code,
        name=inst.name,
        state=inst.state,
        district=inst.district,
        approval_status=inst.approval_status,
        contact_email=inst.contact_email,
        courses=courses
    )

@router.get("/{id}/intake", response_model=InstitutionIntakeSummary)
def get_intake_summary(
    id: str,
    academic_year: str = "2025-2026",
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_optional_current_user)
):
    verify_institution_access(user_context, id)
    intake_details = get_institution_intake_summary(db, id, academic_year)
    return InstitutionIntakeSummary(
        institution_id=id,
        academic_year=academic_year,
        intakes=intake_details
    )

