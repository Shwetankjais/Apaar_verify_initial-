from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.institution import Institution
from backend.app.models.intake import ApprovedIntake
from backend.app.models.enrolment import Enrolment
from backend.app.models.submission import Submission
from backend.app.models.validation_issue import ValidationIssue

def get_dashboard_summary(db: Session, academic_year: str = "2025-2026") -> Dict[str, Any]:
    """Computes national aggregate KPIs directly from database queries."""
    total_institutions = db.query(func.count(Institution.id)).scalar() or 0
    
    total_active_enrolments = db.query(func.count(Enrolment.id)).filter(
        Enrolment.status == "ACTIVE",
        Enrolment.academic_year == academic_year
    ).scalar() or 0

    total_regular_capacity = db.query(func.sum(ApprovedIntake.regular_intake)).filter(
        ApprovedIntake.academic_year == academic_year
    ).scalar() or 0

    total_supernumerary_capacity = db.query(func.sum(ApprovedIntake.supernumerary_intake)).filter(
        ApprovedIntake.academic_year == academic_year
    ).scalar() or 0

    total_capacity = total_regular_capacity + total_supernumerary_capacity
    utilization_pct = round((total_active_enrolments / total_capacity * 100.0), 1) if total_capacity > 0 else 0.0

    total_submissions = db.query(func.count(Submission.id)).filter(
        Submission.academic_year == academic_year
    ).scalar() or 0

    open_exceptions = db.query(func.count(ValidationIssue.id)).filter(
        ValidationIssue.status == "OPEN"
    ).scalar() or 0

    review_required_count = db.query(func.count(ValidationIssue.id)).filter(
        ValidationIssue.severity == "REVIEW_REQUIRED",
        ValidationIssue.status == "OPEN"
    ).scalar() or 0

    rejected_rows_count = db.query(func.sum(Submission.rejected_rows)).filter(
        Submission.academic_year == academic_year
    ).scalar() or 0

    return {
        "academic_year": academic_year,
        "total_institutions": total_institutions,
        "total_active_enrolments": total_active_enrolments,
        "total_approved_intake": total_capacity,
        "regular_capacity": total_regular_capacity,
        "supernumerary_capacity": total_supernumerary_capacity,
        "intake_utilization_pct": utilization_pct,
        "total_submissions": total_submissions,
        "open_exceptions": open_exceptions,
        "review_required_count": review_required_count,
        "rejected_rows_count": rejected_rows_count,
        "synthetic_data_indicator": True
    }

def get_institutions_breakdown(db: Session, academic_year: str = "2025-2026") -> List[Dict[str, Any]]:
    """Calculates per-institution breakdown and compliance status."""
    institutions = db.query(Institution).all()
    results = []

    for inst in institutions:
        intake_cap = db.query(func.sum(ApprovedIntake.regular_intake + ApprovedIntake.supernumerary_intake)).filter(
            ApprovedIntake.institution_id == inst.id,
            ApprovedIntake.academic_year == academic_year
        ).scalar() or 0

        active_enrolled = db.query(func.count(Enrolment.id)).filter(
            Enrolment.institution_id == inst.id,
            Enrolment.academic_year == academic_year,
            Enrolment.status == "ACTIVE"
        ).scalar() or 0

        exceptions = db.query(func.count(ValidationIssue.id)).filter(
            ValidationIssue.institution_id == inst.id,
            ValidationIssue.status == "OPEN"
        ).scalar() or 0

        batches = db.query(func.count(Submission.id)).filter(
            Submission.institution_id == inst.id,
            Submission.academic_year == academic_year
        ).scalar() or 0

        utilization = round((active_enrolled / intake_cap * 100.0), 1) if intake_cap > 0 else 0.0

        compliance_status = "COMPLIANT"
        if active_enrolled > intake_cap and intake_cap > 0:
            compliance_status = "EXCEEDED"
        elif exceptions > 0:
            compliance_status = "FLAGGED"

        results.append({
            "institution_id": inst.id,
            "institution_code": inst.code,
            "institution_name": inst.name,
            "state": inst.state,
            "district": inst.district,
            "approval_status": inst.approval_status,
            "approved_intake": intake_cap,
            "active_enrolment": active_enrolled,
            "utilization_pct": utilization,
            "open_exceptions": exceptions,
            "batches_submitted": batches,
            "compliance_status": compliance_status
        })
    return results

