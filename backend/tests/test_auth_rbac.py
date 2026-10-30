import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.app.main import app

client = TestClient(app)

def test_login_success():
    payload = {"email": "admin@aicte.gov.in", "password": "DemoPass123!"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "aicte_admin"
    assert data["user"]["email"] == "admin@aicte.gov.in"

def test_login_invalid_credentials():
    payload = {"email": "admin@aicte.gov.in", "password": "WrongPassword!"}
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_auth_me_without_token():
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401

def test_auth_me_with_token():
    login_res = client.post("/api/v1/auth/login", json={"email": "officer@mit-demo.ac.in", "password": "DemoPass123!"})
    token = login_res.json()["access_token"]
    
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["email"] == "officer@mit-demo.ac.in"
    assert user_data["role"] == "institution_admin"
    assert user_data["institution_id"] == "DEMO001"

def test_student_forbidden_from_admin_dashboard():
    # Login as student
    login_res = client.post("/api/v1/auth/login", json={"email": "student@demo.ac.in", "password": "DemoPass123!"})
    student_token = login_res.json()["access_token"]
    
    # Attempt to access dashboard summary
    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {student_token}"}
    )
    # Must be 403 Forbidden because student is not permitted
    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower() or "forbidden" in response.json()["detail"].lower()

def test_institution_tenant_isolation():
    # MIT Officer belongs to DEMO001
    login_res = client.post("/api/v1/auth/login", json={"email": "officer@mit-demo.ac.in", "password": "DemoPass123!"})
    mit_token = login_res.json()["access_token"]

    # Attempt to validate uploads for DEMO002
    csv_content = (
        "apaar_id,student_name,institution_student_id,course_code,academic_year,admission_date,category,seat_type,is_nri_oci_fn\n"
        "DEMO-APAAR-0991,Student T1,TEST-0991,CSE,2025-2026,2025-08-10,GENERAL,REGULAR,false\n"
    )
    files = {"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")}
    data = {"institution_id": "DEMO002", "academic_year": "2025-2026"}

    response = client.post(
        "/api/v1/uploads/validate",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {mit_token}"}
    )
    # Must be 403 Forbidden because MIT officer has no authority over DEMO002
    assert response.status_code == 403
    assert "cannot access" in response.json()["detail"].lower() or "forbidden" in response.json()["detail"].lower()
