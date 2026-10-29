import io
import hashlib
import json
import pandas as pd
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.submission import Submission
from backend.app.models.student import Student
from backend.app.models.enrolment import Enrolment
from backend.app.models.validation_issue import ValidationIssue
from backend.app.models.academic_event import AcademicEvent
from backend.app.services.auth_service import generate_apaar_lookup_token, mask_apaar_id
from backend.app.services.validation_service import validate_submission_rows
from backend.app.services.audit_service import record_audit_event

def parse_file_to_rows(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """Safely parses CSV or Excel into normalized row dictionaries."""
    filename_lower = filename.lower()
    try:
        if filename_lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        else:
            raise ValueError("Unsupported file format. Please upload CSV or Excel (.xlsx).")
        
        # Replace NaN with empty string
        df = df.fillna("")
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse upload file: {str(e)}"
        )

def preview_upload_file(
    db: Session,
    institution_id: str,
    academic_year: str,
    file_bytes: bytes,
    filename: str
) -> Dict[str, Any]:
    """Generates preview and validation issue report without modifying database."""
    rows = parse_file_to_rows(file_bytes, filename)
    
    # Compute deterministic batch key from content hash
    content_hash = hashlib.sha256(file_bytes).hexdigest()[:16]
    batch_key = f"bth_{institution_id.lower()}_{academic_year.replace('-', '_')}_{content_hash}"
    
    preview_rows, all_issues, counts = validate_submission_rows(db, institution_id, academic_year, rows)
    
    return {
        "batch_key": batch_key,
        "institution_id": institution_id,
        "academic_year": academic_year,
        "file_name": filename,
        "total_rows": counts["total_rows"],
        "eligible_count": counts["eligible_count"],
        "review_required_count": counts["review_required_count"],
        "rejected_count": counts["rejected_count"],
        "issues": all_issues,
        "rows": preview_rows
    }

def commit_submission_transactional(
    db: Session,
    institution_id: str,
    academic_year: str,
    file_name: str,
    batch_key: str,
    rows: List[Dict[str, Any]],
    user_context: dict
) -> Submission:
    """
    Transactional submission with V008 idempotency check.
    Re-validates rows inside the transaction lock, commits eligible records,
    queues review exceptions, and logs an immutable audit event.
    """
    # V008: Check idempotency key
    existing_sub = db.query(Submission).filter(Submission.batch_key == batch_key).first()
    if existing_sub:
        # Idempotent replay: return existing submission record safely
        return existing_sub

    # Re-run validation inside the database transaction to prevent race conditions
    preview_rows, all_issues, counts = validate_submission_rows(db, institution_id, academic_year, rows)
    
    sub_status = "ACCEPTED"
    if counts["rejected_count"] > 0 and counts["eligible_count"] > 0:
        sub_status = "PARTIALLY_ACCEPTED"
    elif counts["rejected_count"] > 0 and counts["eligible_count"] == 0:
        sub_status = "REJECTED"

    submission = Submission(
        batch_key=batch_key,
        institution_id=institution_id,
        academic_year=academic_year,
        file_name=file_name,
        total_rows=counts["total_rows"],
        eligible_rows=counts["eligible_count"],
        review_required_rows=counts["review_required_count"],
        rejected_rows=counts["rejected_count"],
        status=sub_status
    )
    db.add(submission)
    db.flush() # Flush to get submission.id for foreign keys

    # Persist validation issues (including review flags)
    for iss in all_issues:
        v_issue = ValidationIssue(
            submission_id=submission.id,
            institution_id=institution_id,
            row_number=iss["row_number"],
            rule_code=iss["rule_code"],
            severity=iss["severity"],
            student_apaar=iss.get("student_apaar"),
            field_name=iss.get("field_name"),
            message=iss["message"],
            suggested_correction=iss.get("suggested_correction"),
            status="OPEN"
        )
        db.add(v_issue)

    # Persist eligible and review-required student & enrolment records
    # Note: Hard REJECTED rows are not enrolled; REVIEW_REQUIRED rows can be enrolled in PENDING state or quarantined
    for r in preview_rows:
        if r["outcome"] in ["ELIGIBLE", "REVIEW_REQUIRED"]:
            data = r["data"]
            apaar = data["apaar_id"]
            token = generate_apaar_lookup_token(apaar)
            
            # Find or create student master
            student = db.query(Student).filter(Student.apaar_lookup_token == token).first()
            if not student:
                student = Student(
                    apaar_lookup_token=token,
                    display_apaar_id=mask_apaar_id(apaar),
                    student_name=data["student_name"],
                    email=f"{apaar.lower().replace('-', '_')}@demo.ac.in"
                )
                db.add(student)
                db.flush()

            # Create enrolment record
            enrolment_status = "ACTIVE" if r["outcome"] == "ELIGIBLE" else "PENDING_REVIEW"
            enrolment = Enrolment(
                student_id=student.id,
                institution_id=institution_id,
                institution_student_id=data["institution_student_id"],
                course_code=data["course_code"],
                academic_year=data["academic_year"],
                admission_date=data["admission_date"],
                category=data["category"],
                seat_type=data["seat_type"],
                is_nri_oci_fn=data["is_nri_oci_fn"],
                status=enrolment_status
            )
            db.add(enrolment)
            db.flush()

            # Create initial Academic Journey milestone: Admission Confirmed
            if r["outcome"] == "ELIGIBLE":
                academic_event = AcademicEvent(
                    student_id=student.id,
                    institution_id=institution_id,
                    event_type="ADMISSION_CONFIRMED",
                    event_title=f"Admission Confirmed - {data['course_code']}",
                    term=f"{data['academic_year']} Entry",
                    credits_reported=0.0,
                    credits_validated=0.0,
                    credit_status="REPORTED",
                    issuer_name=institution_id,
                    source_reference=f"ENR-{enrolment.id[:8].upper()}",
                    metadata_json=json.dumps({"seat_type": data["seat_type"], "category": data["category"]})
                )
                db.add(academic_event)

    db.commit()
    db.refresh(submission)

    # Audit event
    record_audit_event(
        db=db,
        actor_role=user_context.get("role", "institution_officer"),
        actor_id=user_context.get("user_id", "officer@demo.edu.in"),
        action="SUBMIT_ENROLMENT_BATCH",
        entity_type="SUBMISSION",
        entity_id=submission.id,
        institution_id=institution_id,
        metadata={
            "batch_key": batch_key,
            "total_rows": submission.total_rows,
            "eligible": submission.eligible_rows,
            "status": submission.status
        }
    )

    return submission

