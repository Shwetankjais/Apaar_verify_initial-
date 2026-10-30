import os
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.document_submission import DocumentSubmission
from backend.app.services.auth_service import get_current_user, get_optional_current_user
from backend.app.services.document_service import (
    create_document_submission,
    get_document_submissions,
    transition_document_status
)

router = APIRouter(prefix="/documents", tags=["Student & Institution Document Governance"])

class DocumentTransitionRequest(BaseModel):
    new_status: Optional[str] = None # UNDER_REVIEW, DEFICIENCY_RAISED, RESUBMITTED, APPROVED, REJECTED
    status: Optional[str] = None # Alias for new_status
    reviewer_comments: Optional[str] = ""
    reviewer_notes: Optional[str] = None # Alias for reviewer_comments
    deficiency_notes: Optional[str] = None

class DocumentSubmissionResponse(BaseModel):
    id: str
    application_no: str
    student_id: Optional[str] = None
    student_name: str
    student_apaar: str
    institution_id: str
    course_code: str
    academic_year: str
    document_type: str
    original_filename: str
    file_size_bytes: int
    mime_type: str
    file_hash_sha256: str
    status: str
    deficiency_notes: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_comments: Optional[str] = None
    created_at: Optional[str] = None

@router.post("/submit", response_model=DocumentSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_document(
    file: UploadFile = File(...),
    student_name: str = Form(...),
    student_apaar: str = Form(...),
    institution_id: str = Form(...),
    course_code: str = Form(...),
    academic_year: str = Form("2025-2026"),
    document_type: str = Form("CLASS_12_MARKSHEET"),
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_optional_current_user)
):
    """
    Genuine document ingestion endpoint.
    Defensively validates MIME magic bytes, file size, saves to private storage,
    and logs a tamper-evident audit event.
    """
    file_bytes = await file.read()
    doc_sub = create_document_submission(
        db=db,
        student_name=student_name,
        student_apaar=student_apaar,
        institution_id=institution_id,
        course_code=course_code,
        academic_year=academic_year,
        document_type=document_type,
        file_bytes=file_bytes,
        original_filename=file.filename or "uploaded_document.pdf",
        user_context=user_context
    )

    return DocumentSubmissionResponse(
        id=doc_sub.id,
        application_no=doc_sub.application_no,
        student_id=doc_sub.student_id,
        student_name=doc_sub.student_name,
        student_apaar=doc_sub.student_apaar,
        institution_id=doc_sub.institution_id,
        course_code=doc_sub.course_code,
        academic_year=doc_sub.academic_year,
        document_type=doc_sub.document_type,
        original_filename=doc_sub.original_filename,
        file_size_bytes=doc_sub.file_size_bytes,
        mime_type=doc_sub.mime_type,
        file_hash_sha256=doc_sub.file_hash_sha256,
        status=doc_sub.status,
        deficiency_notes=doc_sub.deficiency_notes,
        reviewer_id=doc_sub.reviewer_id,
        reviewer_comments=doc_sub.reviewer_comments,
        created_at=doc_sub.created_at.isoformat() if doc_sub.created_at else None
    )

@router.get("", response_model=List[DocumentSubmissionResponse])
def list_documents(
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Lists document submissions strictly scoped by role and institution tenant."""
    docs = get_document_submissions(db=db, user_context=user_context, status_filter=status_filter, limit=limit)
    return [
        DocumentSubmissionResponse(
            id=d.id,
            application_no=d.application_no,
            student_id=d.student_id,
            student_name=d.student_name,
            student_apaar=d.student_apaar,
            institution_id=d.institution_id,
            course_code=d.course_code,
            academic_year=d.academic_year,
            document_type=d.document_type,
            original_filename=d.original_filename,
            file_size_bytes=d.file_size_bytes,
            mime_type=d.mime_type,
            file_hash_sha256=d.file_hash_sha256,
            status=d.status,
            deficiency_notes=d.deficiency_notes,
            reviewer_id=d.reviewer_id,
            reviewer_comments=d.reviewer_comments,
            created_at=d.created_at.isoformat() if d.created_at else None
        )
        for d in docs
    ]

@router.get("/{id}/file")
def download_document_file(
    id: str,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Protected file download endpoint with resource-level access control."""
    doc = db.query(DocumentSubmission).filter(DocumentSubmission.id == id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Access control
    role = user_context["role"]
    if role == "student":
        student_id = user_context.get("student_id")
        if student_id and doc.student_id != student_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    elif role in ["institution_admin", "institution_approver", "institution_officer"]:
        if user_context.get("institution_id") != doc.institution_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Physical document file missing.")

    return FileResponse(
        path=doc.file_path,
        media_type=doc.mime_type,
        filename=doc.original_filename
    )

@router.post("/{id}/transition", response_model=DocumentSubmissionResponse)
def transition_status(
    id: str,
    req: DocumentTransitionRequest,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Executes state machine transition with role authorization and audit logging."""
    target_status = (req.new_status or req.status or "").upper()
    if not target_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required target status.")
    
    comments = req.reviewer_comments or req.reviewer_notes or ""
    deficiency = req.deficiency_notes or (comments if target_status == "DEFICIENCY_RAISED" else None)

    doc = transition_document_status(
        db=db,
        submission_id=id,
        new_status=target_status,
        reviewer_comments=comments,
        deficiency_notes=deficiency,
        user_context=user_context
    )
    return DocumentSubmissionResponse(
        id=doc.id,
        application_no=doc.application_no,
        student_id=doc.student_id,
        student_name=doc.student_name,
        student_apaar=doc.student_apaar,
        institution_id=doc.institution_id,
        course_code=doc.course_code,
        academic_year=doc.academic_year,
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        file_size_bytes=doc.file_size_bytes,
        mime_type=doc.mime_type,
        file_hash_sha256=doc.file_hash_sha256,
        status=doc.status,
        deficiency_notes=doc.deficiency_notes,
        reviewer_id=doc.reviewer_id,
        reviewer_comments=doc.reviewer_comments,
        created_at=doc.created_at.isoformat() if doc.created_at else None
    )
