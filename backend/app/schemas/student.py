from typing import List, Optional
import datetime
from pydantic import BaseModel

class EnrolmentBrief(BaseModel):
    id: str
    institution_id: str
    institution_name: Optional[str] = None
    course_code: str
    academic_year: str
    admission_date: str
    category: str
    seat_type: str
    status: str

    class Config:
        from_attributes = True

class StudentResponse(BaseModel):
    id: str
    display_apaar_id: str
    student_name: str
    email: Optional[str] = None
    current_institution: Optional[str] = None
    current_course: Optional[str] = None
    current_status: Optional[str] = None

    class Config:
        from_attributes = True

class StudentDetailResponse(StudentResponse):
    enrolments: List[EnrolmentBrief] = []

