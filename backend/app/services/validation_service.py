import re
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.student import Student
from backend.app.models.enrolment import Enrolment
from backend.app.services.auth_service import generate_apaar_lookup_token
from backend.app.services.intake_service import check_intake_capacity

DEMO_APAAR_REGEX = re.compile(r"^DEMO-APAAR-\d{4}$")
MANDATORY_FIELDS = [
    "apaar_id",
    "student_name",
    "institution_student_id",
    "course_code",
    "academic_year",
    "admission_date",
    "category",
    "seat_type"
]

def validate_submission_rows(
    db: Session,
    institution_id: str,
    academic_year: str,
    rows: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
    """
    Evaluates rows against deterministic rules V001 - V010.
    Returns: (preview_rows, all_issues, summary_counts)
    """
    preview_rows = []
    all_issues = []
    seen_in_batch_apaar = set()
    seen_in_batch_roll = set()
    
    # Counts of candidates per course for intake calculation
    batch_regular_course_counts = {}

    for idx, raw_row in enumerate(rows):
        row_num = idx + 1
        row_issues = []
        outcome = "ELIGIBLE"
        
        # Clean string keys
        row = {k.strip().lower(): (str(v).strip() if v is not None else "") for k, v in raw_row.items()}
        
        # Support aliases for column names
        apaar_id = row.get("apaar_id") or row.get("apaar") or row.get("student_apaar") or ""
        name = row.get("student_name") or row.get("name") or ""
        roll = row.get("institution_student_id") or row.get("roll_no") or row.get("student_id") or ""
        course = (row.get("course_code") or row.get("course") or row.get("programme") or "").upper()
        acad_yr = row.get("academic_year") or academic_year
        adm_date = row.get("admission_date") or row.get("admission") or ""
        category = (row.get("category") or "GENERAL").upper()
        seat_type = (row.get("seat_type") or "REGULAR").upper()
        is_nri_str = str(row.get("is_nri_oci_fn", "false")).lower()
        is_nri = is_nri_str in ["true", "1", "yes"]

        # V001: Required field missing
        missing_fields = []
        if not apaar_id: missing_fields.append("apaar_id")
        if not name: missing_fields.append("student_name")
        if not roll: missing_fields.append("institution_student_id")
        if not course: missing_fields.append("course_code")
        if not acad_yr: missing_fields.append("academic_year")
        if not adm_date: missing_fields.append("admission_date")

        if missing_fields:
            issue = {
                "row_number": row_num,
                "rule_code": "V001",
                "severity": "ERROR",
                "student_apaar": apaar_id or "MISSING",
                "field_name": ", ".join(missing_fields),
                "message": f"Mandatory fields missing: {', '.join(missing_fields)}.",
                "suggested_correction": "Provide all mandatory student enrolment fields."
            }
            row_issues.append(issue)
            outcome = "REJECTED"

        # V002: Malformed demo identifier (Format check only; not authoritative external identity verification)
        if apaar_id and not DEMO_APAAR_REGEX.match(apaar_id):
            issue = {
                "row_number": row_num,
                "rule_code": "V002",
                "severity": "ERROR",
                "student_apaar": apaar_id,
                "field_name": "apaar_id",
                "message": f"Identifier '{apaar_id}' does not conform to demo prototype format 'DEMO-APAAR-XXXX'. (Note: format check only, not external verification).",
                "suggested_correction": "Format must be synthetic DEMO-APAAR-0000 format."
            }
            row_issues.append(issue)
            outcome = "REJECTED"

        # V003: Duplicate identifier within this upload batch
        if apaar_id:
            if apaar_id in seen_in_batch_apaar:
                issue = {
                    "row_number": row_num,
                    "rule_code": "V003",
                    "severity": "ERROR",
                    "student_apaar": apaar_id,
                    "field_name": "apaar_id",
                    "message": f"Duplicate APAAR identifier '{apaar_id}' detected multiple times within the same upload batch.",
                    "suggested_correction": "Remove or consolidate duplicate rows in the source spreadsheet."
                }
                row_issues.append(issue)
                outcome = "REJECTED"
            else:
                seen_in_batch_apaar.add(apaar_id)

        if roll:
            if roll in seen_in_batch_roll:
                issue = {
                    "row_number": row_num,
                    "rule_code": "V003",
                    "severity": "ERROR",
                    "student_apaar": apaar_id,
                    "field_name": "institution_student_id",
                    "message": f"Duplicate institutional student ID / Roll No '{roll}' within the batch.",
                    "suggested_correction": "Ensure institutional student IDs are unique."
                }
                row_issues.append(issue)
                outcome = "REJECTED"
            else:
                seen_in_batch_roll.add(roll)

        # V006: Inconsistent category / seat fields
        if seat_type in ["NRI", "FN", "OCI"] and not is_nri:
            is_nri = True
        if seat_type == "NRI" and category in ["SC", "ST"]:
            issue = {
                "row_number": row_num,
                "rule_code": "V006",
                "severity": "REVIEW_REQUIRED",
                "student_apaar": apaar_id,
                "field_name": "seat_type",
                "message": f"Inconsistent seat category: seat_type is '{seat_type}' with domestic reserved category '{category}'.",
                "suggested_correction": "Verify whether student is admitted under Supernumerary NRI quota or domestic reserved quota."
            }
            row_issues.append(issue)
            if outcome != "REJECTED":
                outcome = "REVIEW_REQUIRED"

        # Database-dependent checks if syntax passed
        if apaar_id and DEMO_APAAR_REGEX.match(apaar_id):
            lookup_token = generate_apaar_lookup_token(apaar_id)
            existing_student = db.query(Student).filter(Student.apaar_lookup_token == lookup_token).first()
            
            if existing_student:
                # Find their enrolments
                enrolments = db.query(Enrolment).filter(Enrolment.student_id == existing_student.id).all()
                
                # Check for active enrolment in ANOTHER institution (V007)
                active_cross_inst = [
                    e for e in enrolments 
                    if e.institution_id != institution_id 
                    and e.academic_year == acad_yr 
                    and e.status == "ACTIVE"
                ]
                if active_cross_inst:
                    other_inst = active_cross_inst[0].institution_id
                    issue = {
                        "row_number": row_num,
                        "rule_code": "V007",
                        "severity": "REVIEW_REQUIRED",
                        "student_apaar": apaar_id,
                        "field_name": "institution_id",
                        "message": f"Potential simultaneous active enrolment: Student is already registered as ACTIVE at '{other_inst}' for academic year {acad_yr}. Review transfer history.",
                        "suggested_correction": "Request and verify Transfer Certificate (TC) or migration clearance from previous institution."
                    }
                    row_issues.append(issue)
                    if outcome != "REJECTED":
                        outcome = "REVIEW_REQUIRED"
                else:
                    # V004: Identifier already exists in database (update vs re-enrolment)
                    same_inst_enrolment = [
                        e for e in enrolments 
                        if e.institution_id == institution_id and e.academic_year == acad_yr
                    ]
                    if same_inst_enrolment:
                        issue = {
                            "row_number": row_num,
                            "rule_code": "V004",
                            "severity": "REVIEW_REQUIRED",
                            "student_apaar": apaar_id,
                            "field_name": "apaar_id",
                            "message": f"Student '{apaar_id}' already has an active enrolment record for this academic year at your institution. Re-submission requires re-review (V009).",
                            "suggested_correction": "Review whether this is a revised course update or a duplicate record."
                        }
                        row_issues.append(issue)
                        if outcome != "REJECTED":
                            outcome = "REVIEW_REQUIRED"

        # V005: Intake capacity check
        if course:
            reg_so_far = batch_regular_course_counts.get(course, 0)
            if seat_type == "REGULAR":
                batch_regular_course_counts[course] = reg_so_far + 1
                is_comp, cur_cnt, max_cap = check_intake_capacity(db, institution_id, course, acad_yr, seat_type, candidate_count=reg_so_far + 1)
                if not is_comp:
                    issue = {
                        "row_number": row_num,
                        "rule_code": "V005",
                        "severity": "REVIEW_REQUIRED",
                        "student_apaar": apaar_id,
                        "field_name": "course_code",
                        "message": f"Approved regular intake capacity for '{course}' exceeded ({cur_cnt + reg_so_far + 1} enrolled vs {max_cap} approved).",
                        "suggested_correction": "Admit under approved supernumerary slot or obtain AICTE intake enhancement approval."
                    }
                    row_issues.append(issue)
                    if outcome != "REJECTED":
                        outcome = "REVIEW_REQUIRED"

        # Final outcome determination
        if any(iss["severity"] == "ERROR" for iss in row_issues):
            outcome = "REJECTED"
        elif any(iss["severity"] == "REVIEW_REQUIRED" for iss in row_issues):
            outcome = "REVIEW_REQUIRED"
        else:
            outcome = "ELIGIBLE"

        all_issues.extend(row_issues)
        preview_rows.append({
            "row_number": row_num,
            "data": {
                "apaar_id": apaar_id,
                "student_name": name,
                "institution_student_id": roll,
                "course_code": course,
                "academic_year": acad_yr,
                "admission_date": adm_date,
                "category": category,
                "seat_type": seat_type,
                "is_nri_oci_fn": is_nri
            },
            "outcome": outcome,
            "issues": row_issues
        })

    # V010: Check for batch anomaly
    total_rows = len(rows)
    rejected_count = sum(1 for r in preview_rows if r["outcome"] == "REJECTED")
    if total_rows > 0 and (rejected_count / total_rows) >= 0.5:
        all_issues.append({
            "row_number": 0,
            "rule_code": "V010",
            "severity": "WARNING",
            "student_apaar": "BATCH-LEVEL",
            "field_name": "batch_error_rate",
            "message": f"Anomaly Alert: Over 50% ({rejected_count}/{total_rows}) of records in this batch failed validation. Administrative scrutiny recommended.",
            "suggested_correction": "Audit institutional SIS data extraction process before resubmission."
        })

    counts = {
        "total_rows": total_rows,
        "eligible_count": sum(1 for r in preview_rows if r["outcome"] == "ELIGIBLE"),
        "review_required_count": sum(1 for r in preview_rows if r["outcome"] == "REVIEW_REQUIRED"),
        "rejected_count": rejected_count
    }

    return preview_rows, all_issues, counts

