import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.database import Base
from backend.app.models.institution import Institution
from backend.app.models.intake import ApprovedIntake
from backend.app.models.student import Student
from backend.app.models.enrolment import Enrolment
from backend.app.services.auth_service import generate_apaar_lookup_token, mask_apaar_id
from backend.app.services.validation_service import validate_submission_rows

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed test institutions & intakes
    inst = Institution(id="TEST_INST_1", code="TEST001", name="Test Engineering College", state="Karnataka")
    db.add(inst)
    intake = ApprovedIntake(institution_id="TEST_INST_1", course_code="CSE", academic_year="2025-2026", regular_intake=5, supernumerary_intake=2)
    db.add(intake)

    # Seed 1 existing student in another institution for cross-institution test
    st2 = Student(
        apaar_lookup_token=generate_apaar_lookup_token("DEMO-APAAR-8888"),
        display_apaar_id=mask_apaar_id("DEMO-APAAR-8888"),
        student_name="Existing Student"
    )
    db.add(st2)
    db.flush()
    enr2 = Enrolment(
        student_id=st2.id,
        institution_id="OTHER_INST",
        institution_student_id="OTHER-001",
        course_code="CSE",
        academic_year="2025-2026",
        admission_date="2025-08-01",
        category="GENERAL",
        seat_type="REGULAR",
        status="ACTIVE"
    )
    db.add(enr2)
    db.commit()

    yield db
    db.close()

def test_v001_missing_required_fields(test_db):
    rows = [
        {"apaar_id": "DEMO-APAAR-0001", "student_name": "Incomplete Student", "institution_student_id": "", "course_code": ""}
    ]
    preview, issues, counts = validate_submission_rows(test_db, "TEST_INST_1", "2025-2026", rows)
    assert counts["rejected_count"] == 1
    assert any(i["rule_code"] == "V001" for i in issues)

def test_v002_malformed_identifier(test_db):
    rows = [
        {
            "apaar_id": "NOT-A-VALID-APAAR",
            "student_name": "Test Student",
            "institution_student_id": "ROLL-001",
            "course_code": "CSE",
            "academic_year": "2025-2026",
            "admission_date": "2025-08-01",
            "category": "GENERAL",
            "seat_type": "REGULAR"
        }
    ]
    preview, issues, counts = validate_submission_rows(test_db, "TEST_INST_1", "2025-2026", rows)
    assert counts["rejected_count"] == 1
    assert any(i["rule_code"] == "V002" for i in issues)

def test_v003_intra_batch_duplicate(test_db):
    rows = [
        {
            "apaar_id": "DEMO-APAAR-1001",
            "student_name": "Student A",
            "institution_student_id": "ROLL-001",
            "course_code": "CSE",
            "academic_year": "2025-2026",
            "admission_date": "2025-08-01"
        },
        {
            "apaar_id": "DEMO-APAAR-1001",
            "student_name": "Student B",
            "institution_student_id": "ROLL-002",
            "course_code": "CSE",
            "academic_year": "2025-2026",
            "admission_date": "2025-08-01"
        }
    ]
    preview, issues, counts = validate_submission_rows(test_db, "TEST_INST_1", "2025-2026", rows)
    assert any(i["rule_code"] == "V003" for i in issues)
    assert counts["rejected_count"] >= 1

def test_v007_cross_institution_active_conflict(test_db):
    rows = [
        {
            "apaar_id": "DEMO-APAAR-8888",
            "student_name": "Existing Student",
            "institution_student_id": "ROLL-TEST-8888",
            "course_code": "CSE",
            "academic_year": "2025-2026",
            "admission_date": "2025-08-01",
            "category": "GENERAL",
            "seat_type": "REGULAR"
        }
    ]
    preview, issues, counts = validate_submission_rows(test_db, "TEST_INST_1", "2025-2026", rows)
    assert any(i["rule_code"] == "V007" for i in issues)
    assert counts["review_required_count"] == 1

def test_v005_intake_capacity_check(test_db):
    # Capacity is 5; submit 6 regular students
    rows = [
        {
            "apaar_id": f"DEMO-APAAR-{2000+i:04d}",
            "student_name": f"Student {i}",
            "institution_student_id": f"ROLL-{i}",
            "course_code": "CSE",
            "academic_year": "2025-2026",
            "admission_date": "2025-08-01",
            "category": "GENERAL",
            "seat_type": "REGULAR"
        }
        for i in range(1, 7)
    ]
    preview, issues, counts = validate_submission_rows(test_db, "TEST_INST_1", "2025-2026", rows)
    assert any(i["rule_code"] == "V005" for i in issues)
    assert counts["review_required_count"] >= 1

