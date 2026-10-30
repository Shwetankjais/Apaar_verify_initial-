from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.analytics_service import get_dashboard_summary, get_institutions_breakdown
from backend.app.services.auth_service import (
    get_current_user,
    require_roles,
    ROLE_AICTE_ADMIN,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_INSTITUTION_OFFICER,
    ROLE_AUDITOR
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

ALLOWED_ANALYTICS_ROLES = [
    ROLE_AICTE_ADMIN,
    ROLE_INSTITUTION_ADMIN,
    ROLE_INSTITUTION_APPROVER,
    ROLE_INSTITUTION_OFFICER,
    ROLE_AUDITOR
]

@router.get("/summary", response_model=Dict[str, Any])
def dashboard_summary(
    academic_year: str = "2025-2026",
    db: Session = Depends(get_db),
    user_context: dict = Depends(require_roles(ALLOWED_ANALYTICS_ROLES))
):
    """
    Returns database-backed aggregate KPIs.
    Students are strictly forbidden from accessing national regulator analytics.
    """
    return get_dashboard_summary(db, academic_year)

@router.get("/institutions", response_model=List[Dict[str, Any]])
def dashboard_institutions(
    academic_year: str = "2025-2026",
    db: Session = Depends(get_db),
    user_context: dict = Depends(require_roles(ALLOWED_ANALYTICS_ROLES))
):
    """
    Returns institution-level intake utilization and exception metrics.
    Institution staff only receive aggregates for their own institution.
    """
    all_data = get_institutions_breakdown(db, academic_year)
    role = user_context["role"]
    if role in [ROLE_INSTITUTION_ADMIN, ROLE_INSTITUTION_APPROVER, ROLE_INSTITUTION_OFFICER]:
        inst_id = user_context.get("institution_id")
        return [item for item in all_data if item["institution_id"] == inst_id]
    
    return all_data
