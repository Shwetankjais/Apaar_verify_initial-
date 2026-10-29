from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.submission import Submission
from backend.app.schemas.submission import (
    SubmissionPreviewResponse,
    SubmissionCommitRequest,
    SubmissionResponse
)
from backend.app.services.auth_service import get_current_user, verify_institution_access
from backend.app.services.import_service import preview_upload_file, commit_submission_transactional

router = APIRouter(prefix="/uploads", tags=["Uploads & Ingestion"])

@router.post("/validate", response_model=SubmissionPreviewResponse)
async def validate_file_preview(
    file: UploadFile = File(...),
    institution_id: str = Form(...),
    academic_year: str = Form("2025-2026"),
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """
    Previews imported spreadsheet rows and evaluates deterministic validation rules.
    Strictly read-only; DOES NOT mutate database state.
    """
    verify_institution_access(user_context, institution_id)
    content = await file.read()
    preview = preview_upload_file(
        db=db,
        institution_id=institution_id,
        academic_year=academic_year,
        file_bytes=content,
        filename=file.filename or "upload.csv"
    )
    return preview

@router.post("/submit", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_batch_commit(
    request: SubmissionCommitRequest,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """
    Commits eligible rows inside an atomic database transaction.
    Idempotent on batch_key to prevent duplicate submissions.
    """
    verify_institution_access(user_context, request.institution_id)
    submission = commit_submission_transactional(
        db=db,
        institution_id=request.institution_id,
        academic_year=request.academic_year,
        file_name=request.file_name,
        batch_key=request.batch_key,
        rows=request.rows,
        user_context=user_context
    )
    return submission

@router.get("", response_model=List[SubmissionResponse])
def list_submissions(
    institution_id: Optional[str] = None,
    academic_year: Optional[str] = None,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    query = db.query(Submission)
    role = user_context["role"]
    if role == "institution_officer" and user_context.get("institution_id"):
        query = query.filter(Submission.institution_id == user_context["institution_id"])
    elif institution_id:
        query = query.filter(Submission.institution_id == institution_id)

    if academic_year:
        query = query.filter(Submission.academic_year == academic_year)

    return query.order_by(Submission.created_at.desc()).all()

@router.get("/{id}", response_model=SubmissionResponse)
def get_submission(
    id: str,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    sub = db.query(Submission).filter(Submission.id == id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")
    verify_institution_access(user_context, sub.institution_id)
    return sub

