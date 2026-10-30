import datetime
import hashlib
import os
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.document_submission import DocumentSubmission
from backend.app.models.student import Student
from backend.app.models.institution import Institution
from backend.app.services.audit_service import record_audit_event
from backend.app.services.auth_service import generate_apaar_lookup_token

# Magic bytes signatures for defensive content validation
MAGIC_BYTES = {
    ".pdf": b"%PDF",
    ".jpeg": b"\xff\xd8\xff",
    ".jpg": b"\xff\xd8\xff",
    ".png": b"\x89PNG\r\n\x1a\n"
}

ALLOWED_TRANSITIONS = {
    "DRAFT": ["SUBMITTED"],
    "SUBMITTED": ["UNDER_REVIEW"],
    "UNDER_REVIEW": ["DEFICIENCY_RAISED", "APPROVED", "REJECTED"],
    "DEFICIENCY_RAISED": ["RESUBMITTED"],
    "RESUBMITTED": ["UNDER_REVIEW", "APPROVED", "REJECTED"],
    "APPROVED": [], # Terminal
    "REJECTED": ["RESUBMITTED"] # Allowed to appeal/resubmit
}

def validate_file_content(file_bytes: bytes, original_filename: str) -> tuple[str, str]:
    """Defensively validates file extension, file size, and magic byte signatures."""
    # 1. Size check
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
        )

    # 2. Extension check
    ext = Path(original_filename).suffix.lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed formats: PDF, JPEG, PNG."
        )

    # 3. Magic Bytes Content Inspection
    expected_magic = MAGIC_BYTES.get(ext)
    if expected_magic and not file_bytes.startswith(expected_magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MIME signature mismatch. File content does not match '{ext}' format. Upload rejected."
        )

    mime_map = {
        ".pdf": "application/pdf",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".png": "image/png"
    }
    return ext, mime_map.get(ext, "application/octet-stream")

def create_document_submission(
    db: Session,
    student_name: str,
    student_apaar: str,
    institution_id: str,
    course_code: str,
    academic_year: str,
    document_type: str,
    file_bytes: bytes,
    original_filename: str,
    user_context: dict
) -> DocumentSubmission:
    """Saves document in private storage, computes SHA-256 hash, and creates submission record."""
    # Defensively validate file
    ext, mime_type = validate_file_content(file_bytes, original_filename)
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    # Verify institution exists
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Institution '{institution_id}' not found.")

    # Match student if already registered in platform
    token = generate_apaar_lookup_token(student_apaar)
    student = db.query(Student).filter(Student.apaar_lookup_token == token).first()

    submission_id = str(uuid.uuid4())
    stored_filename = f"{submission_id}{ext}"
    private_file_path = str(settings.STORAGE_DIR / stored_filename)

    # Save to private filesystem storage
    with open(private_file_path, "wb") as f:
        f.write(file_bytes)

    # Generate sequential application number
    count = db.query(DocumentSubmission).count() + 1
    app_no = f"APAAR-DOC-2026-{count:04d}"

    doc_sub = DocumentSubmission(
        id=submission_id,
        application_no=app_no,
        student_id=student.id if student else None,
        student_name=student_name.strip(),
        student_apaar=student_apaar.strip(),
        institution_id=institution_id,
        course_code=course_code.upper().strip(),
        academic_year=academic_year.strip(),
        document_type=document_type,
        file_path=private_file_path,
        original_filename=Path(original_filename).name,
        file_size_bytes=len(file_bytes),
        mime_type=mime_type,
        file_hash_sha256=file_hash,
        status="SUBMITTED"
    )
    db.add(doc_sub)
    db.commit()
    db.refresh(doc_sub)

    # Log in audit trail
    record_audit_event(
        db=db,
        actor_role=user_context.get("role", "student"),
        actor_id=user_context.get("email", "student@demo.ac.in"),
        action="SUBMIT_ACADEMIC_DOCUMENT",
        entity_type="DOCUMENT_SUBMISSION",
        entity_id=doc_sub.id,
        institution_id=institution_id,
        metadata={
            "app_no": app_no,
            "document_type": document_type,
            "file_hash": file_hash,
            "file_size": len(file_bytes)
        }
    )

    return doc_sub

def get_document_submissions(
    db: Session,
    user_context: dict,
    status_filter: Optional[str] = None,
    limit: int = 50
) -> List[DocumentSubmission]:
    """Retrieves document submissions strictly scoped by caller's role and institution tenant."""
    role = user_context["role"]
    query = db.query(DocumentSubmission)

    if role == "student":
        # Students can only view their own submissions
        student_id = user_context.get("student_id")
        user_email = user_context.get("email", "")
        if student_id:
            query = query.filter(DocumentSubmission.student_id == student_id)
        else:
            query = query.filter(DocumentSubmission.student_name.ilike(f"%{user_email.split('@')[0]}%"))
    elif role in ["institution_admin", "institution_approver", "institution_officer"]:
        # Institution staff can only see their assigned institution
        user_inst = user_context.get("institution_id")
        if user_inst:
            query = query.filter(DocumentSubmission.institution_id == user_inst)
    # AICTE admin and auditors see all

    if status_filter:
        query = query.filter(DocumentSubmission.status == status_filter)

    return query.order_by(DocumentSubmission.created_at.desc()).limit(limit).all()

def transition_document_status(
    db: Session,
    submission_id: str,
    new_status: str,
    reviewer_comments: str,
    deficiency_notes: Optional[str],
    user_context: dict
) -> DocumentSubmission:
    """Executes state machine transition with role authorization and audit logging."""
    role = user_context["role"]
    # Enforce separation of duties: only institutional approvers/admins or aicte_admin can approve/reject
    if role not in ["aicte_admin", "institution_admin", "institution_approver", "institution_officer"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to adjudicate academic documents."
        )

    doc = db.query(DocumentSubmission).filter(DocumentSubmission.id == submission_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document submission not found.")

    # Check institution boundary if caller is institution staff
    if role in ["institution_admin", "institution_approver", "institution_officer"]:
        if user_context.get("institution_id") != doc.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: You cannot adjudicate documents for another institution."
            )

    curr_status = doc.status
    allowed = ALLOWED_TRANSITIONS.get(curr_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition from '{curr_status}' to '{new_status}'. Allowed: {allowed}"
        )

    # Mandatory notes for deficiency or rejection
    if new_status == "DEFICIENCY_RAISED" and not (deficiency_notes or reviewer_comments):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deficiency explanation notes are mandatory when raising a deficiency."
        )
    if new_status == "REJECTED" and not reviewer_comments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer comments explaining the reason for rejection are mandatory."
        )

    doc.status = new_status
    doc.reviewer_id = user_context.get("email", "reviewer@demo.ac.in")
    doc.reviewer_comments = reviewer_comments
    if deficiency_notes:
        doc.deficiency_notes = deficiency_notes
    doc.reviewed_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(doc)

    # Record tamper-evident audit event
    record_audit_event(
        db=db,
        actor_role=role,
        actor_id=user_context.get("email", "reviewer@demo.ac.in"),
        action=f"DOCUMENT_TRANSITION_{new_status}",
        entity_type="DOCUMENT_SUBMISSION",
        entity_id=doc.id,
        institution_id=doc.institution_id,
        metadata={
            "app_no": doc.application_no,
            "old_status": curr_status,
            "new_status": new_status,
            "comments": reviewer_comments
        }
    )

    return doc

