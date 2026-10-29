from typing import Optional
from pydantic import BaseModel

class EnrolmentRow(BaseModel):
    apaar_id: str
    student_name: str
    institution_student_id: str
    course_code: str
    academic_year: str
    admission_date: str
    category: str = "GENERAL"
    seat_type: str = "REGULAR"
    is_nri_oci_fn: bool = False

