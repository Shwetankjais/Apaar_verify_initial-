import os
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_PATH = str(BASE_DIR / "frontend" / "app.py")

def test_frontend_home_page():
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert not at.exception, f"Home page threw exception: {at.exception}"

def test_frontend_doc_submit_page():
    at = AppTest.from_file(APP_PATH)
    at.session_state["current_nav"] = "nav_doc_submit"
    at.run()
    assert not at.exception, f"Submit Documents page threw exception: {at.exception}"

def test_frontend_doc_track_page():
    at = AppTest.from_file(APP_PATH)
    at.session_state["current_nav"] = "nav_doc_track"
    at.run()
    assert not at.exception, f"Track Document Status page threw exception: {at.exception}"

def test_frontend_verification_page():
    at = AppTest.from_file(APP_PATH)
    at.session_state["current_nav"] = "nav_verification"
    at.run()
    assert not at.exception, f"Verification & QR page threw exception: {at.exception}"

def test_frontend_student_journey_page():
    at = AppTest.from_file(APP_PATH)
    at.session_state["current_nav"] = "nav_student_journey"
    at.run()
    assert not at.exception, f"Student Journey page threw exception: {at.exception}"

def test_frontend_edupath_page():
    at = AppTest.from_file(APP_PATH)
    at.session_state["current_nav"] = "nav_edupath"
    at.run()
    assert not at.exception, f"EduPath Advisory page threw exception: {at.exception}"

def test_frontend_regulatory_page():
    at = AppTest.from_file(APP_PATH)
    at.session_state["current_nav"] = "nav_regulatory"
    at.run()
    assert not at.exception, f"Regulatory page threw exception: {at.exception}"

def test_frontend_admin_dashboard():
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = {
        "id": "u-admin",
        "email": "admin@aicte.gov.in",
        "full_name": "Dr. Ramesh Sharma",
        "role": "aicte_admin",
        "institution_id": None
    }
    at.session_state["auth_token"] = "mock_admin_token"
    at.session_state["current_nav"] = "nav_dashboard"
    at.run()
    assert not at.exception, f"Admin Dashboard threw exception: {at.exception}"

def test_frontend_admin_exceptions():
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = {
        "id": "u-admin",
        "email": "admin@aicte.gov.in",
        "full_name": "Dr. Ramesh Sharma",
        "role": "aicte_admin",
        "institution_id": None
    }
    at.session_state["auth_token"] = "mock_admin_token"
    at.session_state["current_nav"] = "nav_exceptions"
    at.run()
    assert not at.exception, f"Exceptions Desk threw exception: {at.exception}"

def test_frontend_admin_audit_trail():
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = {
        "id": "u-admin",
        "email": "admin@aicte.gov.in",
        "full_name": "Dr. Ramesh Sharma",
        "role": "aicte_admin",
        "institution_id": None
    }
    at.session_state["auth_token"] = "mock_admin_token"
    at.session_state["current_nav"] = "nav_audit"
    at.run()
    assert not at.exception, f"Audit Trail threw exception: {at.exception}"

def test_frontend_institution_portal():
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = {
        "id": "u-officer",
        "email": "officer@mit-demo.ac.in",
        "full_name": "Prof. S. K. Kulkarni",
        "role": "institution_officer",
        "institution_id": "DEMO001"
    }
    at.session_state["auth_token"] = "mock_inst_token"
    at.session_state["current_nav"] = "nav_institution"
    at.run()
    assert not at.exception, f"Institution Intake Portal threw exception: {at.exception}"

def test_frontend_institution_students_directory():
    at = AppTest.from_file(APP_PATH)
    at.session_state["auth_user"] = {
        "id": "u-officer",
        "email": "officer@mit-demo.ac.in",
        "full_name": "Prof. S. K. Kulkarni",
        "role": "institution_officer",
        "institution_id": "DEMO001"
    }
    at.session_state["auth_token"] = "mock_inst_token"
    at.session_state["current_nav"] = "nav_students"
    at.run()
    assert not at.exception, f"Students Directory threw exception: {at.exception}"
