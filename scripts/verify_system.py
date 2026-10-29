import os
import sys
import json
import sqlite3
import requests

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "apaar_verify.db")
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"

def print_section(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

def verify_database():
    print_section("1. DATABASE VERIFICATION (SQLite: apaar_verify.db)")
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found at: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = [
        "institutions", "approved_intakes", "students", "enrolments",
        "submissions", "validation_issues", "verification_references",
        "academic_events", "audit_events"
    ]
    
    all_ok = True
    for table in tables:
        try:
            cursor.execute(f"SELECT count(*) FROM {table}")
            cnt = cursor.fetchone()[0]
            print(f"  ✓ Table '{table:<24}': {cnt:>4} records")
        except Exception as e:
            print(f"  ❌ Table '{table}': {e}")
            all_ok = False
            
    conn.close()
    return all_ok

def verify_backend_apis():
    print_section("2. FASTAPI BACKEND API VERIFICATION (http://127.0.0.1:8000)")
    
    # 1. Health
    r = requests.get(f"{BACKEND_URL}/health", timeout=5)
    print(f"  ✓ GET /health: HTTP {r.status_code} -> {r.json().get('status')}")
    assert r.status_code == 200

    # 2. Institutions
    r = requests.get(f"{BACKEND_URL}/api/v1/institutions", timeout=5)
    insts = r.json()
    print(f"  ✓ GET /api/v1/institutions: HTTP {r.status_code} -> {len(insts)} institutions loaded")
    assert r.status_code == 200 and len(insts) >= 3

    # 3. Intake Context
    r = requests.get(f"{BACKEND_URL}/api/v1/institutions/DEMO001/intake", timeout=5)
    intake = r.json()
    print(f"  ✓ GET /api/v1/institutions/DEMO001/intake: HTTP {r.status_code} -> {len(intake.get('intakes', []))} courses")
    assert r.status_code == 200

    # 4. Dashboard Summary
    r = requests.get(f"{BACKEND_URL}/api/v1/dashboard/summary", timeout=5)
    dash = r.json()
    print(f"  ✓ GET /api/v1/dashboard/summary: HTTP {r.status_code} -> Active Students: {dash.get('total_active_enrolments')}, Capacity: {dash.get('total_approved_intake')}, Utilization: {dash.get('intake_utilization_pct')}%")
    assert r.status_code == 200

    # 5. Students Roster
    r = requests.get(f"{BACKEND_URL}/api/v1/students?limit=5", timeout=5)
    stds = r.json()
    print(f"  ✓ GET /api/v1/students?limit=5: HTTP {r.status_code} -> {len(stds)} sample records (First: {stds[0]['student_name']} - {stds[0]['display_apaar_id']})")
    assert r.status_code == 200 and len(stds) > 0

    first_student_id = stds[0]["id"]

    # 6. Student Academic Journey
    r = requests.get(f"{BACKEND_URL}/api/v1/academic-journey/{first_student_id}", timeout=5)
    journey = r.json()
    print(f"  ✓ GET /api/v1/academic-journey/{first_student_id[:8]}...: HTTP {r.status_code} -> {len(journey)} milestone events")
    assert r.status_code == 200

    # 7. File Validation Preview (Faulty demo file)
    faulty_csv = os.path.join(BASE_DIR, "data", "faulty_upload_demo.csv")
    with open(faulty_csv, "rb") as f:
        r = requests.post(
            f"{BACKEND_URL}/api/v1/uploads/validate",
            files={"file": ("faulty_upload_demo.csv", f.read(), "text/csv")},
            data={"institution_id": "DEMO001", "academic_year": "2025-2026"},
            timeout=10
        )
    val = r.json()
    print(f"  ✓ POST /api/v1/uploads/validate (Faulty CSV): HTTP {r.status_code} -> Total: {val.get('total_rows')}, Hard Errors: {val.get('rejected_count')}, Flags: {val.get('review_required_count')}, Issues Detected: {len(val.get('issues', []))}")
    assert r.status_code == 200 and val.get("rejected_count") > 0

    # 8. Verification Token Creation & Check
    r = requests.post(
        f"{BACKEND_URL}/api/v1/verification-requests",
        json={"student_id": first_student_id, "purpose": "EMPLOYMENT_VERIFICATION", "expires_in_hours": 48},
        timeout=5
    )
    v_data = r.json()
    ref_code = v_data["reference_code"]
    print(f"  ✓ POST /api/v1/verification-requests: HTTP {r.status_code} -> Generated Ref: {ref_code}")
    assert r.status_code == 200

    r = requests.get(f"{BACKEND_URL}/api/v1/verify/{ref_code}", timeout=5)
    verify_res = r.json()
    print(f"  ✓ GET /api/v1/verify/{ref_code}: HTTP {r.status_code} -> Valid: {verify_res.get('is_valid')}, Status: {verify_res.get('status')}, Signature Verified: {verify_res.get('signature_verified')}")
    assert r.status_code == 200 and verify_res.get("is_valid") is True

    # 9. Policy Handbook Assistant
    r = requests.post(
        f"{BACKEND_URL}/api/v1/policy/query",
        json={"query": "What is the quota rule for supernumerary TFW seats?"},
        timeout=5
    )
    pol = r.json()
    print(f"  ✓ POST /api/v1/policy/query: HTTP {r.status_code} -> Matched: '{pol.get('topic')}' ({pol.get('source_document')})")
    assert r.status_code == 200 and pol.get("has_answer") is True

    # 10. Tamper-Evident Audit Trail
    r = requests.get(f"{BACKEND_URL}/api/v1/audit?limit=5", timeout=5)
    audit = r.json()
    print(f"  ✓ GET /api/v1/audit: HTTP {r.status_code} -> {len(audit)} audit logs chained")
    assert r.status_code == 200 and len(audit) > 0

    return True

def verify_frontend():
    print_section("3. STREAMLIT FRONTEND VERIFICATION (http://127.0.0.1:8501)")
    
    r = requests.get(FRONTEND_URL, timeout=5)
    print(f"  ✓ GET http://127.0.0.1:8501: HTTP {r.status_code} ({len(r.text)} bytes received)")
    assert r.status_code == 200
    
    # Check Streamlit core health
    r_health = requests.get(f"{FRONTEND_URL}/_stcore/health", timeout=5)
    print(f"  ✓ GET http://127.0.0.1:8501/_stcore/health: HTTP {r_health.status_code} -> {r_health.text.strip()}")
    assert r_health.status_code == 200
    
    return True

if __name__ == "__main__":
    db_ok = verify_database()
    api_ok = verify_backend_apis()
    fe_ok = verify_frontend()
    
    print_section("SUMMARY VERIFICATION RESULT")
    if db_ok and api_ok and fe_ok:
        print("🎉 ALL SYSTEMS FULLY OPERATIONAL AND VERIFIED LOCALLY!")
        print(f"  • Frontend Portal:  {FRONTEND_URL}")
        print(f"  • Backend REST API: {BACKEND_URL}")
        print(f"  • Swagger Docs:     {BACKEND_URL}/docs")
    else:
        print("⚠️ Some verification checks did not succeed. Check output above.")

