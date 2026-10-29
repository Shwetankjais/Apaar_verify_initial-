from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.models.intake import ApprovedIntake
from backend.app.models.enrolment import Enrolment

def get_institution_intake_summary(db: Session, institution_id: str, academic_year: str) -> List[Dict[str, Any]]:
    """Calculates intake utilization per course for a given institution and academic year."""
    intake_records = db.query(ApprovedIntake).filter(
        ApprovedIntake.institution_id == institution_id,
        ApprovedIntake.academic_year == academic_year
    ).all()

    results = []
    for intake in intake_records:
        # Count active regular admissions
        reg_count = db.query(func.count(Enrolment.id)).filter(
            Enrolment.institution_id == institution_id,
            Enrolment.course_code == intake.course_code,
            Enrolment.academic_year == academic_year,
            Enrolment.seat_type == "REGULAR",
            Enrolment.status == "ACTIVE"
        ).scalar() or 0

        # Count active supernumerary admissions (TFW, PMSSS, NRI, etc.)
        sup_count = db.query(func.count(Enrolment.id)).filter(
            Enrolment.institution_id == institution_id,
            Enrolment.course_code == intake.course_code,
            Enrolment.academic_year == academic_year,
            Enrolment.seat_type != "REGULAR",
            Enrolment.status == "ACTIVE"
        ).scalar() or 0

        utilization = round((reg_count / intake.regular_intake * 100.0), 1) if intake.regular_intake > 0 else 0.0
        
        status_label = "COMPLIANT"
        if reg_count > intake.regular_intake:
            status_label = "EXCEEDED"
        elif utilization >= 90.0:
            status_label = "NEAR_CAPACITY"

        results.append({
            "course_code": intake.course_code,
            "regular_intake": intake.regular_intake,
            "supernumerary_intake": intake.supernumerary_intake,
            "enrolled_regular": reg_count,
            "enrolled_supernumerary": sup_count,
            "utilization_pct": utilization,
            "status": status_label
        })
    return results

def check_intake_capacity(db: Session, institution_id: str, course_code: str, academic_year: str, seat_type: str, candidate_count: int = 1) -> tuple[bool, int, int]:
    """
    Checks if adding candidate_count students would exceed approved capacity.
    Returns: (is_compliant, current_count, approved_capacity)
    """
    intake = db.query(ApprovedIntake).filter(
        ApprovedIntake.institution_id == institution_id,
        ApprovedIntake.course_code == course_code,
        ApprovedIntake.academic_year == academic_year
    ).first()

    if not intake:
        # Default fallback capacity if not specifically configured
        return True, 0, 999

    if seat_type.upper() == "REGULAR":
        current = db.query(func.count(Enrolment.id)).filter(
            Enrolment.institution_id == institution_id,
            Enrolment.course_code == course_code,
            Enrolment.academic_year == academic_year,
            Enrolment.seat_type == "REGULAR",
            Enrolment.status == "ACTIVE"
        ).scalar() or 0
        return (current + candidate_count <= intake.regular_intake), current, intake.regular_intake
    else:
        current = db.query(func.count(Enrolment.id)).filter(
            Enrolment.institution_id == institution_id,
            Enrolment.course_code == course_code,
            Enrolment.academic_year == academic_year,
            Enrolment.seat_type != "REGULAR",
            Enrolment.status == "ACTIVE"
        ).scalar() or 0
        return (current + candidate_count <= intake.supernumerary_intake), current, intake.supernumerary_intake

