"""
Seed Demo Script for APAAR Verify by Sutrāyukti
Generates:
1. 3 Fictional AICTE-approved Institutions and configured Approved Intakes
2. ~100-110 baseline synthetic students with masked display IDs and active enrolments
3. Academic events for Verified Academic Journey demonstration
4. Sample faulty CSV (data/faulty_upload_demo.csv)
5. Sample valid correction CSV (data/valid_upload_sample.csv)
"""

import os
import sys
import json
import csv
import random
import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal, engine, Base
from backend.app.models.institution import Institution
from backend.app.models.intake import ApprovedIntake
from backend.app.models.student import Student
from backend.app.models.enrolment import Enrolment
from backend.app.models.academic_event import AcademicEvent
from backend.app.models.verification_ref import VerificationReference
from backend.app.models.user import User
from backend.app.models.document_submission import DocumentSubmission
from backend.app.services.auth_service import generate_apaar_lookup_token, mask_apaar_id, hash_password
from backend.app.services.verification_service import sign_verification_payload
from backend.app.config import settings

def seed_all():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing demo data for clean repeatable run
    db.query(DocumentSubmission).delete()
    db.query(AcademicEvent).delete()
    db.query(VerificationReference).delete()
    db.query(Enrolment).delete()
    db.query(User).delete()
    db.query(Student).delete()
    db.query(ApprovedIntake).delete()
    db.query(Institution).delete()
    db.commit()

    print("Seeding Institutions...")
    institutions = [
        Institution(
            id="DEMO001",
            code="DEMO001",
            name="Mysuru Institute of Technology",
            state="Karnataka",
            district="Mysuru",
            approval_status="APPROVED",
            contact_email="principal@mit-demo.ac.in"
        ),
        Institution(
            id="DEMO002",
            code="DEMO002",
            name="Deccan Engineering College",
            state="Maharashtra",
            district="Pune",
            approval_status="APPROVED",
            contact_email="director@dec-demo.ac.in"
        ),
        Institution(
            id="DEMO003",
            code="DEMO003",
            name="Coastal Technical Institute",
            state="Karnataka",
            district="Dakshina Kannada",
            approval_status="APPROVED",
            contact_email="dean@cti-demo.ac.in"
        )
    ]
    db.add_all(institutions)
    db.commit()

    print("Seeding Approved Intakes...")
    intakes = [
        # DEMO001
        ApprovedIntake(institution_id="DEMO001", course_code="CSE", academic_year="2025-2026", regular_intake=40, supernumerary_intake=4),
        ApprovedIntake(institution_id="DEMO001", course_code="ECE", academic_year="2025-2026", regular_intake=30, supernumerary_intake=3),
        # DEMO002
        ApprovedIntake(institution_id="DEMO002", course_code="CSE", academic_year="2025-2026", regular_intake=30, supernumerary_intake=3),
        ApprovedIntake(institution_id="DEMO002", course_code="MECH", academic_year="2025-2026", regular_intake=25, supernumerary_intake=2),
        # DEMO003
        ApprovedIntake(institution_id="DEMO003", course_code="ECE", academic_year="2025-2026", regular_intake=25, supernumerary_intake=2),
        ApprovedIntake(institution_id="DEMO003", course_code="CSE", academic_year="2025-2026", regular_intake=20, supernumerary_intake=2),
    ]
    db.add_all(intakes)
    db.commit()

    print("Seeding Baseline Synthetic Students (~100 students)...")
    student_counter = 1
    
    # 1. Mysuru: 38 regular CSE + 2 supernumerary CSE, 25 regular ECE
    # 2. Deccan: 26 regular CSE + 2 supernumerary CSE, 20 regular MECH
    # 3. Coastal: 20 regular ECE + 2 supernumerary ECE, 14 regular CSE
    
    plan = [
        ("DEMO001", "CSE", 35, "REGULAR"),
        ("DEMO001", "CSE", 3, "TFW"),
        ("DEMO001", "ECE", 25, "REGULAR"),
        ("DEMO002", "CSE", 26, "REGULAR"),
        ("DEMO002", "CSE", 2, "PMSSS"),
        ("DEMO002", "MECH", 18, "REGULAR"),
        ("DEMO003", "ECE", 20, "REGULAR"),
        ("DEMO003", "CSE", 14, "REGULAR"),
    ]

    all_students = []
    all_enrolments = []

    for inst_id, course, count, seat_type in plan:
        for _ in range(count):
            apaar = f"DEMO-APAAR-{student_counter:04d}"
            name = f"Student Demo {student_counter:03d}"
            token = generate_apaar_lookup_token(apaar)
            masked = mask_apaar_id(apaar)
            
            student = Student(
                apaar_lookup_token=token,
                display_apaar_id=masked,
                student_name=name,
                email=f"demo_std_{student_counter:03d}@demo.ac.in"
            )
            db.add(student)
            db.flush()

            enrolment = Enrolment(
                student_id=student.id,
                institution_id=inst_id,
                institution_student_id=f"{inst_id}-{course}-{student_counter:04d}",
                course_code=course,
                academic_year="2025-2026",
                admission_date="2025-08-01",
                category=random.choice(["GENERAL", "OBC", "SC", "ST", "EWS"]),
                seat_type=seat_type,
                status="ACTIVE",
                is_nri_oci_fn=False
            )
            db.add(enrolment)
            db.flush()

            # Seed academic events for Student 10 (key demo student)
            if student_counter == 10:
                ev1 = AcademicEvent(
                    student_id=student.id,
                    institution_id=inst_id,
                    event_type="ADMISSION_CONFIRMED",
                    event_title=f"Admission Confirmed - {course}",
                    term="2025-26 Entry",
                    credits_reported=0.0,
                    credits_validated=0.0,
                    credit_status="REPORTED",
                    issuer_name="Mysuru Institute of Technology",
                    source_reference=f"ADM-2025-{student_counter:04d}",
                    metadata_json=json.dumps({"quota": seat_type, "rank": "KCET-1420"})
                )
                ev2 = AcademicEvent(
                    student_id=student.id,
                    institution_id=inst_id,
                    event_type="ENROLMENT_ACTIVE",
                    event_title="Enrolment Verified & Academic Identity Linked",
                    term="Semester 1",
                    credits_reported=0.0,
                    credits_validated=0.0,
                    credit_status="REPORTED",
                    issuer_name="AICTE Central Verification Authority",
                    source_reference=f"APAAR-REG-{student_counter:04d}",
                    metadata_json=json.dumps({"verified_method": "MockAPAARAdapter"})
                )
                ev3 = AcademicEvent(
                    student_id=student.id,
                    institution_id=inst_id,
                    event_type="SEMESTER_CREDITS",
                    event_title="Semester 1 Academic Credits Validated",
                    term="Semester 1 (Autumn 2025)",
                    credits_reported=22.0,
                    credits_validated=22.0,
                    credit_status="VALIDATED",
                    issuer_name="Mysuru Institute of Technology - Exam Cell",
                    source_reference="EXAM-SEM1-2025",
                    metadata_json=json.dumps({"sgpa": 8.85, "courses_passed": 6})
                )
                db.add_all([ev1, ev2, ev3])

            # Special handling for Student 99 (Legitimate Transfer Case)
            if student_counter == 99:
                enrolment.institution_id = "DEMO002"
                enrolment.academic_year = "2024-2025"
                enrolment.status = "TRANSFERRED"

            student_counter += 1

    db.commit()
    print(f"Database successfully seeded! Total students in database: {student_counter - 1}")

    # Seed User Accounts for RBAC
    print("Seeding RBAC Users...")
    student_10 = db.query(Student).filter(Student.student_name == "Student Demo 010").first()
    default_pwd_hash = hash_password("DemoPass123!")

    users = [
        User(
            email="admin@aicte.gov.in",
            hashed_password=default_pwd_hash,
            full_name="Dr. Ramesh Sharma (AICTE Admin)",
            role="aicte_admin",
            institution_id=None
        ),
        User(
            email="officer@mit-demo.ac.in",
            hashed_password=default_pwd_hash,
            full_name="Prof. Ananya Rao (MIT Nodal Officer)",
            role="institution_admin",
            institution_id="DEMO001"
        ),
        User(
            email="approver@mit-demo.ac.in",
            hashed_password=default_pwd_hash,
            full_name="Dr. Suresh Menon (MIT Verification Cell)",
            role="institution_approver",
            institution_id="DEMO001"
        ),
        User(
            email="officer@dec-demo.ac.in",
            hashed_password=default_pwd_hash,
            full_name="Prof. Rajesh Kulkarni (Deccan Admin)",
            role="institution_admin",
            institution_id="DEMO002"
        ),
        User(
            email="student@demo.ac.in",
            hashed_password=default_pwd_hash,
            full_name="Student Demo 010",
            role="student",
            student_id=student_10.id if student_10 else None
        ),
        User(
            email="auditor@aicte.gov.in",
            hashed_password=default_pwd_hash,
            full_name="Vikramaditya Verma (CAG Auditor)",
            role="auditor",
            institution_id=None
        )
    ]
    db.add_all(users)
    db.commit()
    print(f"Seeded {len(users)} authentication accounts.")

    # Seed Sample Document Submissions
    print("Seeding Sample Document Submissions...")
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    sample_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Demo Academic Document) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    
    file1_name = "demo_marksheet_0010.pdf"
    file1_path = str(settings.STORAGE_DIR / file1_name)
    with open(file1_path, "wb") as f:
        f.write(sample_pdf_bytes)
        
    file2_name = "demo_tc_0010.pdf"
    file2_path = str(settings.STORAGE_DIR / file2_name)
    with open(file2_path, "wb") as f:
        f.write(sample_pdf_bytes)

    import hashlib
    sha256_hash = hashlib.sha256(sample_pdf_bytes).hexdigest()

    doc_submissions = [
        DocumentSubmission(
            application_no="APAAR-DOC-2026-0001",
            student_id=student_10.id if student_10 else None,
            student_name="Student Demo 010",
            student_apaar="DEMO-APAAR-0010",
            institution_id="DEMO001",
            course_code="CSE",
            academic_year="2025-2026",
            document_type="CLASS_12_MARKSHEET",
            file_path=file1_path,
            original_filename="class_12_marksheet_verified.pdf",
            file_size_bytes=len(sample_pdf_bytes),
            mime_type="application/pdf",
            file_hash_sha256=sha256_hash,
            status="SUBMITTED",
            deficiency_notes=None
        ),
        DocumentSubmission(
            application_no="APAAR-DOC-2026-0002",
            student_id=student_10.id if student_10 else None,
            student_name="Student Demo 010",
            student_apaar="DEMO-APAAR-0010",
            institution_id="DEMO001",
            course_code="CSE",
            academic_year="2025-2026",
            document_type="TRANSFER_CERTIFICATE",
            file_path=file2_path,
            original_filename="migration_transfer_cert.pdf",
            file_size_bytes=len(sample_pdf_bytes),
            mime_type="application/pdf",
            file_hash_sha256=sha256_hash,
            status="DEFICIENCY_RAISED",
            deficiency_notes="Seal/signature missing on page 2. Please re-upload verified signed copy from previous college.",
            reviewer_id="approver@mit-demo.ac.in",
            reviewer_comments="Discrepancy noted during initial scrutiny on 2026-10-25."
        )
    ]
    db.add_all(doc_submissions)
    db.commit()
    print(f"Seeded {len(doc_submissions)} document submission records.")

    # Generate CSVs
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(data_dir, exist_ok=True)

    # 1. Faulty Upload Demo CSV (Intentionally contains V001-V007 issues)
    faulty_csv_path = os.path.join(data_dir, "faulty_upload_demo.csv")
    print(f"Creating faulty demo dataset at {faulty_csv_path}...")
    faulty_rows = [
        # Normal row
        {"apaar_id": "DEMO-APAAR-0501", "student_name": "Student Demo 501", "institution_student_id": "DEMO001-CSE-0501", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        # V001: Missing mandatory fields (no roll number, missing course)
        {"apaar_id": "DEMO-APAAR-0502", "student_name": "Student Demo 502", "institution_student_id": "", "course_code": "", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        # V002: Malformed demo identifier (not matching DEMO-APAAR-XXXX format)
        {"apaar_id": "INVALID-ID-XYZ", "student_name": "Student Demo 503", "institution_student_id": "DEMO001-CSE-0503", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        # V003: Intra-batch duplicate identifier (DEMO-APAAR-0504 appears twice in this file)
        {"apaar_id": "DEMO-APAAR-0504", "student_name": "Student Demo 504A", "institution_student_id": "DEMO001-CSE-0504A", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "OBC", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        {"apaar_id": "DEMO-APAAR-0504", "student_name": "Student Demo 504B", "institution_student_id": "DEMO001-CSE-0504B", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "OBC", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        # V004: ID already in database for this institution (DEMO-APAAR-0001 is already enrolled at DEMO001)
        {"apaar_id": "DEMO-APAAR-0001", "student_name": "Student Demo 001", "institution_student_id": "DEMO001-CSE-0001-UPDATE", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        # V005: Admissions exceeding approved regular intake (DEMO001 CSE regular capacity is 40; 35 already exist)
        {"apaar_id": "DEMO-APAAR-0505", "student_name": "Student Demo 505", "institution_student_id": "DEMO001-CSE-0505", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        {"apaar_id": "DEMO-APAAR-0506", "student_name": "Student Demo 506", "institution_student_id": "DEMO001-CSE-0506", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        {"apaar_id": "DEMO-APAAR-0507", "student_name": "Student Demo 507", "institution_student_id": "DEMO001-CSE-0507", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        {"apaar_id": "DEMO-APAAR-0508", "student_name": "Student Demo 508", "institution_student_id": "DEMO001-CSE-0508", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        {"apaar_id": "DEMO-APAAR-0509", "student_name": "Student Demo 509", "institution_student_id": "DEMO001-CSE-0509", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        {"apaar_id": "DEMO-APAAR-0510", "student_name": "Student Demo 510", "institution_student_id": "DEMO001-CSE-0510", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        # V006: Inconsistent category (NRI seat type with SC category)
        {"apaar_id": "DEMO-APAAR-0511", "student_name": "Student Demo 511", "institution_student_id": "DEMO001-ECE-0511", "course_code": "ECE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "SC", "seat_type": "NRI", "is_nri_oci_fn": "true"},
        # V007: Potential simultaneous active enrolment across institutions (DEMO-APAAR-0042 is already ACTIVE at DEMO002)
        {"apaar_id": "DEMO-APAAR-0042", "student_name": "Student Demo 042", "institution_student_id": "DEMO001-ECE-0042", "course_code": "ECE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"},
        # Legitimate Transfer Case: DEMO-APAAR-0099 previously TRANSFERRED from DEMO002, now enrolling at DEMO001
        {"apaar_id": "DEMO-APAAR-0099", "student_name": "Student Demo 099 (Transfer Case)", "institution_student_id": "DEMO001-CSE-0099", "course_code": "CSE", "academic_year": "2025-2026", "admission_date": "2025-08-15", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"}
    ]

    with open(faulty_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(faulty_rows[0].keys()))
        writer.writeheader()
        writer.writerows(faulty_rows)

    # 2. Valid Upload Sample CSV (Clean submission file)
    valid_csv_path = os.path.join(data_dir, "valid_upload_sample.csv")
    print(f"Creating clean valid upload dataset at {valid_csv_path}...")
    valid_rows = [
        {"apaar_id": f"DEMO-APAAR-{700+i:04d}", "student_name": f"Student Demo {700+i:03d}", "institution_student_id": f"DEMO001-ECE-{700+i:04d}", "course_code": "ECE", "academic_year": "2025-2026", "admission_date": "2025-08-18", "category": "GENERAL", "seat_type": "REGULAR", "is_nri_oci_fn": "false"}
        for i in range(1, 4)
    ]
    with open(valid_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(valid_rows[0].keys()))
        writer.writeheader()
        writer.writerows(valid_rows)

    print("Seed complete! Synthetic baseline and demo files generated successfully.")

if __name__ == "__main__":
    seed_all()
