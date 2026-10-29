from typing import List
from pydantic import BaseModel

class CourseIntakeDetail(BaseModel):
    course_code: str
    regular_intake: int
    supernumerary_intake: int
    enrolled_regular: int
    enrolled_supernumerary: int
    utilization_pct: float
    status: str # COMPLIANT, WARNING, EXCEEDED

class InstitutionIntakeSummary(BaseModel):
    institution_id: str
    academic_year: str
    intakes: List[CourseIntakeDetail]

