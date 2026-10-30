import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.main import app

client = TestClient(app)

def test_document_submission_magic_bytes_validation():
    # Attempt to upload a fake PDF containing plain text (not matching %PDF signature)
    fake_pdf_bytes = b"This is not a real PDF document at all."
    files = {"file": ("malicious.pdf", fake_pdf_bytes, "application/pdf")}
    data = {
        "student_name": "Student Demo 010",
        "student_apaar": "DEMO-APAAR-0010",
        "institution_id": "DEMO001",
        "course_code": "CSE",
        "academic_year": "2025-2026",
        "document_type": "CLASS_12_MARKSHEET"
    }

    response = client.post("/api/v1/documents/submit", files=files, data=data)
    assert response.status_code == 400
    assert "MIME signature mismatch" in response.json()["detail"]

def test_document_submission_valid():
    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Authentic Marksheet) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {"file": ("valid_marksheet.pdf", valid_pdf_bytes, "application/pdf")}
    data = {
        "student_name": "Student Demo 010",
        "student_apaar": "DEMO-APAAR-0010",
        "institution_id": "DEMO001",
        "course_code": "CSE",
        "academic_year": "2025-2026",
        "document_type": "CLASS_12_MARKSHEET"
    }

    response = client.post("/api/v1/documents/submit", files=files, data=data)
    assert response.status_code in [200, 201]
    res_data = response.json()
    assert res_data["application_no"].startswith("APAAR-DOC-2026-")
    assert res_data["status"] == "SUBMITTED"
    assert len(res_data["file_hash_sha256"]) == 64

def test_document_transition_lifecycle():
    # 1. Submit a fresh document
    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Title (Transfer Cert) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    files = {"file": ("transfer_cert.pdf", valid_pdf_bytes, "application/pdf")}
    data = {
        "student_name": "Student Demo 010",
        "student_apaar": "DEMO-APAAR-0010",
        "institution_id": "DEMO001",
        "course_code": "CSE",
        "academic_year": "2025-2026",
        "document_type": "TRANSFER_CERTIFICATE"
    }
    submit_res = client.post("/api/v1/documents/submit", files=files, data=data)
    assert submit_res.status_code in [200, 201]
    doc_id = submit_res.json()["id"]

    # 2. Login as student and try to approve document (Negative test -> 403 Forbidden)
    std_login = client.post("/api/v1/auth/login", json={"email": "student@demo.ac.in", "password": "DemoPass123!"})
    std_token = std_login.json()["access_token"]
    forbidden_res = client.post(
        f"/api/v1/documents/{doc_id}/transition",
        json={"status": "APPROVED", "reviewer_notes": "Student trying to self-approve"},
        headers={"Authorization": f"Bearer {std_token}"}
    )
    assert forbidden_res.status_code == 403

    # 3. Login as MIT Approver (DEMO001)
    appr_login = client.post("/api/v1/auth/login", json={"email": "approver@mit-demo.ac.in", "password": "DemoPass123!"})
    appr_token = appr_login.json()["access_token"]

    # 4. Valid transition: SUBMITTED -> UNDER_REVIEW
    t1_res = client.post(
        f"/api/v1/documents/{doc_id}/transition",
        json={"status": "UNDER_REVIEW", "reviewer_notes": "Beginning scrutiny"},
        headers={"Authorization": f"Bearer {appr_token}"}
    )
    assert t1_res.status_code == 200
    assert t1_res.json()["status"] == "UNDER_REVIEW"

    # 5. Valid transition: UNDER_REVIEW -> DEFICIENCY_RAISED
    t2_res = client.post(
        f"/api/v1/documents/{doc_id}/transition",
        json={"status": "DEFICIENCY_RAISED", "reviewer_notes": "Principal signature missing"},
        headers={"Authorization": f"Bearer {appr_token}"}
    )
    assert t2_res.status_code == 200
    assert t2_res.json()["status"] == "DEFICIENCY_RAISED"

    # 6. Invalid transition: DEFICIENCY_RAISED -> APPROVED (Must be RESUBMITTED first)
    invalid_res = client.post(
        f"/api/v1/documents/{doc_id}/transition",
        json={"status": "APPROVED", "reviewer_notes": "Illegal jump"},
        headers={"Authorization": f"Bearer {appr_token}"}
    )
    assert invalid_res.status_code == 400
    assert "Invalid state transition" in invalid_res.json()["detail"]
