from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.student import Student
from backend.app.models.enrolment import Enrolment
from backend.app.models.institution import Institution
from backend.app.schemas.student import StudentResponse, StudentDetailResponse, EnrolmentBrief
from backend.app.services.auth_service import get_current_user, verify_institution_access

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("", response_model=List[StudentResponse])
def list_students(
    institution_id: Optional[str] = None,
    search: Optional[str] = None,
    course_code: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    """Lists students with masked identifiers. Scoped by institution if user is an institution officer."""
    role = user_context["role"]
    query = db.query(Enrolment).join(Student, Enrolment.student_id == Student.id)

    if role == "institution_officer" and user_context.get("institution_id"):
        query = query.filter(Enrolment.institution_id == user_context["institution_id"])
    elif institution_id:
        query = query.filter(Enrolment.institution_id == institution_id)

    if course_code:
        query = query.filter(Enrolment.course_code == course_code)
    if status_filter:
        query = query.filter(Enrolment.status == status_filter)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (Student.student_name.ilike(s)) | 
            (Student.display_apaar_id.ilike(s)) | 
            (Enrolment.institution_student_id.ilike(s))
        )

    enrolments = query.offset(offset).limit(limit).all()
    results = []
    for enr in enrolments:
        student = db.query(Student).filter(Student.id == enr.student_id).first()
        if student:
            results.append(StudentResponse(
                id=student.id,
                display_apaar_id=student.display_apaar_id,
                student_name=student.student_name,
                email=student.email,
                current_institution=enr.institution_id,
                current_course=enr.course_code,
                current_status=enr.status
            ))
    return results

@router.get("/{id}", response_model=StudentDetailResponse)
def get_student(
    id: str,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_current_user)
):
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student '{id}' not found.")

    enrolments = db.query(Enrolment).filter(Enrolment.student_id == student.id).all()
    
    # Institution officer check: must have at least one enrolment in user's institution
    role = user_context["role"]
    if role == "institution_officer" and user_context.get("institution_id"):
        has_enrolment = any(e.institution_id == user_context["institution_id"] for e in enrolments)
        if not has_enrolment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Student does not have an enrolment record at your institution."
            )

    enr_briefs = []
    current_inst = None
    current_course = None
    current_status = None

    for e in enrolments:
        inst = db.query(Institution).filter(Institution.id == e.institution_id).first()
        enr_briefs.append(EnrolmentBrief(
            id=e.id,
            institution_id=e.institution_id,
            institution_name=inst.name if inst else e.institution_id,
            course_code=e.course_code,
            academic_year=e.academic_year,
            admission_date=e.admission_date,
            category=e.category,
            seat_type=e.seat_type,
            status=e.status
        ))
        if e.status == "ACTIVE":
            current_inst = e.institution_id
            current_course = e.course_code
            current_status = e.status

    return StudentDetailResponse(
        id=student.id,
        display_apaar_id=student.display_apaar_id,
        student_name=student.student_name,
        email=student.email,
        current_institution=current_inst or (enrolments[0].institution_id if enrolments else "N/A"),
        current_course=current_course or (enrolments[0].course_code if enrolments else "N/A"),
        current_status=current_status or "INACTIVE",
        enrolments=enr_briefs
    )

