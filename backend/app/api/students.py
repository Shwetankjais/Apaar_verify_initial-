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
    """
    Lists students with masked identifiers.
    Students can ONLY see their own record.
    Institution staff can ONLY see students in their own institution.
    """
    role = user_context["role"]
    query = db.query(Enrolment).join(Student, Enrolment.student_id == Student.id)

    if role == "student":
        # Strict student isolation
        std_id = user_context.get("student_id")
        if std_id:
            query = query.filter(Student.id == std_id)
        else:
            # Look up by email if student_id not explicitly set
            query = query.filter(Student.email == user_context.get("email"))
    elif role in ["institution_admin", "institution_approver", "institution_officer"]:
        inst_id = user_context.get("institution_id")
        if inst_id:
            query = query.filter(Enrolment.institution_id == inst_id)
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
    seen_student_ids = set()

    for enr in enrolments:
        if enr.student_id in seen_student_ids:
            continue
        seen_student_ids.add(enr.student_id)

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
    role = user_context["role"]
    student = db.query(Student).filter(Student.id == id).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student '{id}' not found.")

    # Student isolation check
    if role == "student":
        caller_student_id = user_context.get("student_id")
        if caller_student_id and caller_student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students are strictly permitted to view only their own academic records."
            )
        elif not caller_student_id and student.email != user_context.get("email"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students are strictly permitted to view only their own academic records."
            )

    enrolments = db.query(Enrolment).filter(Enrolment.student_id == student.id).all()
    
    # Institution officer check: must have at least one enrolment in user's institution
    if role in ["institution_admin", "institution_approver", "institution_officer"]:
        user_inst = user_context.get("institution_id")
        if user_inst and not any(e.institution_id == user_inst for e in enrolments):
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
