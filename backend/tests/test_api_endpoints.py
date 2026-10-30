import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "APAAR Verify" in response.json()["message"]

def test_institutions_list():
    response = client.get("/api/v1/institutions")
    assert response.status_code == 200
    institutions = response.json()
    assert len(institutions) >= 3
    assert any(inst["id"] == "DEMO001" for inst in institutions)

def test_institution_intake():
    response = client.get("/api/v1/institutions/DEMO001/intake")
    assert response.status_code == 200
    data = response.json()
    assert data["institution_id"] == "DEMO001"
    assert len(data["intakes"]) >= 2

def test_dashboard_summary():
    response = client.get("/api/v1/dashboard/summary", headers={"X-User-Role": "aicte_admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_institutions"] >= 3
    assert data["total_active_enrolments"] >= 100
    assert data["intake_utilization_pct"] > 0

def test_upload_validate_preview():
    csv_content = (
        "apaar_id,student_name,institution_student_id,course_code,academic_year,admission_date,category,seat_type,is_nri_oci_fn\n"
        "DEMO-APAAR-0991,Student T1,TEST-0991,CSE,2025-2026,2025-08-10,GENERAL,REGULAR,false\n"
        "INVALID-ID,Student T2,,CSE,2025-2026,2025-08-10,GENERAL,REGULAR,false\n"
    )
    files = {"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")}
    data = {"institution_id": "DEMO001", "academic_year": "2025-2026"}
    
    response = client.post(
        "/api/v1/uploads/validate",
        files=files,
        data=data,
        headers={"X-User-Role": "institution_admin", "X-Institution-Id": "DEMO001"}
    )
    assert response.status_code == 200
    res = response.json()
    assert res["total_rows"] == 2
    assert res["rejected_count"] == 1
    assert res["eligible_count"] == 1
    assert len(res["issues"]) >= 2 # V001 (missing roll) + V002 (invalid ID)

def test_policy_assistant_query():
    response = client.post("/api/v1/policy/query", json={"query": "What are the rules for supernumerary TFW seats?"})
    assert response.status_code == 200
    data = response.json()
    assert data["has_answer"] is True
    assert "Supernumerary Seats" in data["topic"]
    assert "Approval Process Handbook" in data["source_document"]
