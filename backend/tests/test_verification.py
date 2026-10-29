import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app

client = TestClient(app)

def test_verification_lifecycle():
    # 1. Fetch student list to get a valid student ID
    st_res = client.get("/api/v1/students?limit=1")
    assert st_res.status_code == 200
    students = st_res.json()
    assert len(students) > 0
    student_id = students[0]["id"]

    # 2. Create verification request
    v_req = client.post(
        "/api/v1/verification-requests",
        json={"student_id": student_id, "purpose": "EMPLOYMENT_BACKGROUND_CHECK", "expires_in_hours": 24}
    )
    assert v_req.status_code == 200
    v_data = v_req.json()
    ref_code = v_data["reference_code"]
    assert ref_code.startswith("vref_")
    assert "qr_data_url" in v_data

    # 3. Verify valid reference
    verify_res = client.get(f"/api/v1/verify/{ref_code}")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["is_valid"] is True
    assert verify_data["status"] == "VALID"
    assert verify_data["signature_verified"] is True
    assert "permitted_fields" in verify_data
    # Ensure raw sensitive info (e.g. Aadhaar) is NOT present
    assert "aadhaar" not in verify_data["permitted_fields"]

    # 4. Revoke the reference
    revoke_res = client.post(f"/api/v1/verify/{ref_code}/revoke?reason=TestRevocation")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["status"] == "REVOKED"

    # 5. Check verification again - must now show REVOKED
    recheck_res = client.get(f"/api/v1/verify/{ref_code}")
    assert recheck_res.status_code == 200
    recheck_data = recheck_res.json()
    assert recheck_data["is_valid"] is False
    assert recheck_data["status"] == "REVOKED"
    assert "TestRevocation" in recheck_data["rejection_reason"]

def test_invalid_reference():
    res = client.get("/api/v1/verify/vref_non_existent_code")
    assert res.status_code == 200
    data = res.json()
    assert data["is_valid"] is False
    assert data["status"] == "NOT_FOUND"

