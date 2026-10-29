from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.services.analytics_service import get_dashboard_summary, get_institutions_breakdown
from backend.app.services.auth_service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

@router.get("/summary", response_model=Dict[str, Any])
def dashboard_summary(
    academic_year: str = "2025-2026",
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Returns database-backed national aggregate KPIs for AICTE administration."""
    return get_dashboard_summary(db, academic_year)

@router.get("/institutions", response_model=List[Dict[str, Any]])
def dashboard_institutions(
    academic_year: str = "2025-2026",
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Returns institution-level intake utilization and exception metrics."""
    return get_institutions_breakdown(db, academic_year)

