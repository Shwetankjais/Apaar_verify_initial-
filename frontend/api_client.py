import os
import requests
from typing import Optional, Dict, Any, List

LIVE_PRODUCTION_BACKEND = "https://apaar-verify-initial.onrender.com"
LOCAL_DEV_BACKEND = "http://127.0.0.1:8001"

def resolve_api_base_url() -> str:
    """
    Authoritative backend URL resolver for APAAR Verify.
    1. Reads Streamlit secrets (st.secrets["API_BASE_URL"]) if configured.
    2. Reads environment variable (API_BASE_URL) if configured.
    3. Falls back to https://apaar-verify-initial.onrender.com only for production environments
       (e.g. Streamlit Community Cloud or APP_ENV=production).
    4. Preserves http://127.0.0.1:8001 as the local development default.
    """
    # 1. Check Streamlit secrets (Community Cloud)
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            try:
                secret_url = st.secrets.get("API_BASE_URL")
                if secret_url and str(secret_url).strip():
                    return str(secret_url).strip().rstrip("/")
            except Exception:
                pass
    except Exception:
        pass

    # 2. Check environment variable
    env_url = os.getenv("API_BASE_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")

    # 3. Production environment detection
    # Checks standard production flags, Streamlit Cloud indicators, and cloud container environments
    is_production = (
        os.getenv("APP_ENV", "").lower() in ("production", "prod")
        or os.getenv("ENVIRONMENT", "").lower() in ("production", "prod")
        or os.getenv("STREAMLIT_ENV", "").lower() in ("production", "prod")
        or os.getenv("IS_STREAMLIT_CLOUD", "").lower() == "true"
        or os.getenv("STREAMLIT_SHARING_HOST") is not None
        or os.getenv("HOSTNAME", "").startswith("streamlit")
        or os.getenv("USER") == "appuser"
        or (os.path.exists("/app") and not os.path.exists("/Users"))
    )
    if is_production:
        return LIVE_PRODUCTION_BACKEND

    # 4. Local development default
    return LOCAL_DEV_BACKEND

API_BASE_URL = resolve_api_base_url()

class ApiClient:
    """
    Centralized API client for APAAR Verify.
    Communicates with FastAPI backend on port 8001 locally or https://apaar-verify-initial.onrender.com in production.
    Features robust connection error handling, automatic retry fallback, and graceful degradation.
    """
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = (base_url or resolve_api_base_url()).rstrip("/")
        self.token = token
        self.last_error: Optional[str] = None
        self.is_offline: bool = False

    def set_token(self, token: Optional[str]):
        self.token = token

    def _headers(
        self,
        role: Optional[str] = None,
        institution_id: Optional[str] = None,
        user_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        active_token = token or self.token
        if active_token:
            headers["Authorization"] = f"Bearer {active_token}"
        
        if role:
            headers["X-User-Role"] = role
            headers["X-User-Id"] = user_id or f"{role}@sutrayukti.gov.in"
        if institution_id:
            headers["X-Institution-Id"] = institution_id
            
        return headers

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Any] = None,
        files: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ) -> Optional[requests.Response]:
        """
        Internal centralized HTTP dispatcher.
        Catches connection errors, socket failures, and timeouts gracefully.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            res = requests.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=headers,
                timeout=timeout
            )
            self.is_offline = False
            self.last_error = None
            return res
        except requests.exceptions.RequestException as e:
            self.is_offline = True
            self.last_error = str(e)
            return None
        except Exception as e:
            self.is_offline = True
            self.last_error = str(e)
            return None

    def get_health(self) -> Dict[str, Any]:
        """Check backend health status on configured base_url."""
        # Render cloud free-tier instances may sleep on idle and require up to 15s for cold start
        timeout = 15 if "onrender.com" in self.base_url else 4
        res = self._request("GET", "/health", timeout=timeout)
        if res is not None and res.status_code == 200:
            try:
                data = res.json()
                self.is_offline = False
                return data
            except Exception:
                pass
        
        # Only do localhost / 127.0.0.1 swap if the configured base_url is actually local
        if "127.0.0.1" in self.base_url or "localhost" in self.base_url:
            alt_base = "http://localhost:8001" if "127.0.0.1" in self.base_url else "http://127.0.0.1:8001"
            try:
                alt_res = requests.get(f"{alt_base}/health", timeout=2)
                if alt_res.status_code == 200:
                    self.base_url = alt_base
                    self.is_offline = False
                    self.last_error = None
                    return alt_res.json()
            except Exception:
                pass

        self.is_offline = True
        return {
            "status": "offline",
            "service": "APAAR Verify Core API",
            "database": "disconnected",
            "error": self.last_error or f"FastAPI engine unreachable on {self.base_url}"
        }

    # --- Authentication & Session ---
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user against backend, returning JWT access token and user profile."""
        payload = {"email": email.strip(), "password": password.strip()}
        res = self._request("POST", "/api/v1/auth/login", json=payload, timeout=12)
        if res is None:
            is_local = "127.0.0.1" in self.base_url or "localhost" in self.base_url
            hint = "Ensure uvicorn is running: python -m uvicorn backend.app.main:app --port 8001" if is_local else "The live backend on Render may be waking up. Please retry in 15-20 seconds."
            return {
                "status_code": 503,
                "error": True,
                "data": {
                    "detail": f"Backend Verification Engine unreachable on {self.base_url}. {hint}"
                }
            }
        try:
            data = res.json()
            if res.status_code == 200 and "access_token" in data:
                self.token = data["access_token"]
            return {"status_code": res.status_code, "data": data}
        except Exception as e:
            return {"status_code": res.status_code, "data": {"detail": str(e)}}

    def get_me(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Fetch current authenticated user profile."""
        headers = self._headers(token=token)
        res = self._request("GET", "/api/v1/auth/me", headers=headers, timeout=5)
        if res is None:
            return {"status_code": 503, "data": {"detail": "Backend service unreachable."}}
        try:
            return {"status_code": res.status_code, "data": res.json()}
        except Exception as e:
            return {"status_code": res.status_code, "data": {"detail": str(e)}}

    # --- Direct Document Workflow ---
    def submit_document(
        self,
        student_name: str,
        student_apaar: str,
        institution_id: str,
        course_code: str,
        academic_year: str,
        document_type: str,
        file_bytes: bytes,
        filename: str,
        role: str = "student",
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit an academic credential directly with magic bytes validation and private storage."""
        files = {"file": (filename, file_bytes)}
        data = {
            "student_name": student_name,
            "student_apaar": student_apaar,
            "institution_id": institution_id,
            "course_code": course_code,
            "academic_year": academic_year,
            "document_type": document_type
        }
        headers = self._headers(role=role, token=token)
        res = self._request(
            "POST",
            "/api/v1/documents/submit",
            data=data,
            files=files,
            headers=headers,
            timeout=15
        )
        if res is None:
            return {
                "status_code": 503,
                "data": {
                    "detail": f"Backend Verification Engine unreachable on {self.base_url}. Please ensure uvicorn is running."
                }
            }
        try:
            return {"status_code": res.status_code, "data": res.json()}
        except Exception as e:
            return {"status_code": res.status_code, "data": {"detail": str(e)}}

    def get_documents(
        self,
        role: str,
        institution_id: Optional[str] = None,
        status_filter: Optional[str] = None,
        student_apaar: Optional[str] = None,
        token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve submitted documents scoped to caller's role and institution."""
        params = {}
        if status_filter:
            params["status_filter"] = status_filter
        if student_apaar:
            params["student_apaar"] = student_apaar
        
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("GET", "/api/v1/documents", params=params, headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def transition_document(
        self,
        document_id: str,
        new_status: str,
        notes: Optional[str] = None,
        role: str = "institution_approver",
        institution_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute state transition on document submission."""
        payload = {"status": new_status, "reviewer_notes": notes}
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request(
            "POST",
            f"/api/v1/documents/{document_id}/transition",
            json=payload,
            headers=headers,
            timeout=8
        )
        if res is None:
            return {"status_code": 503, "data": {"detail": "Backend service unreachable."}}
        try:
            return {"status_code": res.status_code, "data": res.json()}
        except Exception as e:
            return {"status_code": res.status_code, "data": {"detail": str(e)}}

    def get_document_file(self, document_id: str, role: str, institution_id: Optional[str] = None, token: Optional[str] = None):
        """Download or stream raw document bytes securely."""
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        return self._request("GET", f"/api/v1/documents/{document_id}/file", headers=headers, timeout=15)

    # --- Core Governance & Regulatory Analytics ---
    def get_dashboard_summary(self, role: str, academic_year: str = "2025-2026", token: Optional[str] = None) -> Dict[str, Any]:
        headers = self._headers(role=role, token=token)
        res = self._request("GET", f"/api/v1/dashboard/summary?academic_year={academic_year}", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return {
            "total_approved_intake": 0,
            "total_enrolled": 0,
            "total_verified_apaar": 0,
            "unverified_flagged": 0,
            "flagged_exceptions": 0,
            "institution_count": 0,
            "offline": True,
            "error": True
        }

    def get_dashboard_institutions(self, role: str, academic_year: str = "2025-2026", token: Optional[str] = None) -> list:
        headers = self._headers(role=role, token=token)
        res = self._request("GET", f"/api/v1/dashboard/institutions?academic_year={academic_year}", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def get_institutions(self, role: str = "public", institution_id: Optional[str] = None, token: Optional[str] = None) -> list:
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("GET", "/api/v1/institutions", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def get_institution_intake(self, institution_id: str, role: str, academic_year: str = "2025-2026", token: Optional[str] = None) -> Dict[str, Any]:
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("GET", f"/api/v1/institutions/{institution_id}/intake?academic_year={academic_year}", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return {}

    def validate_file(self, file_bytes: bytes, filename: str, institution_id: str, role: str, academic_year: str = "2025-2026", token: Optional[str] = None) -> Dict[str, Any]:
        files = {"file": (filename, file_bytes, "text/csv")}
        data = {"institution_id": institution_id, "academic_year": academic_year}
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("POST", "/api/v1/uploads/validate", files=files, data=data, headers=headers, timeout=15)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return {
            "is_valid": False,
            "summary": {"total_records": 0, "passed": 0, "failed": 0},
            "errors": [{"row": 0, "field": "Connection", "error": f"Backend Verification Engine offline at {self.base_url}"}],
            "records": []
        }

    def submit_batch(self, batch_key: str, institution_id: str, academic_year: str, filename: str, rows: list, role: str, token: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "batch_key": batch_key,
            "institution_id": institution_id,
            "academic_year": academic_year,
            "file_name": filename,
            "rows": rows
        }
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("POST", "/api/v1/uploads/submit", json=payload, headers=headers, timeout=15)
        if res is not None and res.status_code in (200, 201):
            try:
                return res.json()
            except Exception:
                pass
        return {"status": "error", "message": f"Backend Verification Engine offline at {self.base_url}"}

    def get_submissions(self, role: str, institution_id: Optional[str] = None, token: Optional[str] = None) -> list:
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("GET", "/api/v1/uploads", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def get_students(self, role: str, institution_id: Optional[str] = None, search: Optional[str] = None, token: Optional[str] = None) -> list:
        path = "/api/v1/students?limit=50"
        if search:
            path += f"&search={search}"
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("GET", path, headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def get_student_detail(self, student_id: str, role: str, token: Optional[str] = None) -> Dict[str, Any]:
        headers = self._headers(role=role, token=token)
        res = self._request("GET", f"/api/v1/students/{student_id}", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return {}

    def get_student_journey(self, student_id: str, role: str, token: Optional[str] = None) -> list:
        headers = self._headers(role=role, token=token)
        res = self._request("GET", f"/api/v1/academic-journey/{student_id}", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def add_academic_milestone(self, payload: dict, role: str, token: Optional[str] = None) -> Dict[str, Any]:
        headers = self._headers(role=role, token=token)
        res = self._request("POST", "/api/v1/academic-journey/events", json=payload, headers=headers, timeout=8)
        if res is not None and res.status_code in (200, 201):
            try:
                return res.json()
            except Exception:
                pass
        return {"error": True, "detail": "Backend Verification Engine offline"}

    def get_exceptions(self, role: str, institution_id: Optional[str] = None, status_filter: Optional[str] = None, token: Optional[str] = None) -> list:
        path = "/api/v1/exceptions"
        if status_filter:
            path += f"?status_filter={status_filter}"
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("GET", path, headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def resolve_exception(self, issue_id: str, new_status: str, comment: str, role: str, token: Optional[str] = None) -> Dict[str, Any]:
        payload = {"status": new_status, "reviewer_comment": comment}
        headers = self._headers(role=role, token=token)
        res = self._request("PATCH", f"/api/v1/exceptions/{issue_id}", json=payload, headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return {"error": True, "detail": "Backend service unreachable."}

    def create_verification_ref(self, student_id: str, role: str, purpose: str = "EMPLOYMENT_VERIFICATION", hours: int = 72, token: Optional[str] = None) -> Dict[str, Any]:
        payload = {"student_id": student_id, "purpose": purpose, "expires_in_hours": hours}
        headers = self._headers(role=role, token=token)
        res = self._request("POST", "/api/v1/verification-requests", json=payload, headers=headers, timeout=8)
        if res is not None and res.status_code in (200, 201):
            try:
                return res.json()
            except Exception:
                pass
        return {"error": True, "detail": f"Backend Verification Engine offline on {self.base_url}"}

    def verify_reference(self, reference_code: str, role: str = "verifier", token: Optional[str] = None) -> Dict[str, Any]:
        headers = self._headers(role=role, token=token)
        res = self._request("GET", f"/api/v1/verify/{reference_code}", headers=headers, timeout=8)
        if res is not None:
            try:
                return res.json()
            except Exception:
                pass
        return {
            "is_valid": False,
            "status": "BACKEND_OFFLINE",
            "detail": f"Backend Verification Engine is currently offline or unreachable on {self.base_url}."
        }

    def revoke_reference(self, reference_code: str, reason: str, role: str, token: Optional[str] = None) -> Dict[str, Any]:
        headers = self._headers(role=role, token=token)
        res = self._request("POST", f"/api/v1/verify/{reference_code}/revoke?reason={reason}", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return {"error": True, "detail": "Backend service unreachable."}

    def get_audit_trail(self, role: str, institution_id: Optional[str] = None, token: Optional[str] = None) -> list:
        headers = self._headers(role=role, institution_id=institution_id, token=token)
        res = self._request("GET", "/api/v1/audit", headers=headers, timeout=8)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def search_edupath(self, query: Optional[str] = None, state: Optional[str] = None) -> list:
        params = []
        if query:
            params.append(f"query={query}")
        if state:
            params.append(f"state={state}")
        path = "/api/v1/edupath/colleges" + (("?" + "&".join(params)) if params else "")
        res = self._request("GET", path, timeout=6)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def match_scholarships(self, family_income: float, is_female: bool, has_disability: bool) -> list:
        payload = {"family_income": family_income, "is_female": is_female, "has_disability": has_disability}
        res = self._request("POST", "/api/v1/edupath/scholarships/match", json=payload, timeout=6)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return []

    def ask_policy(self, query: str) -> Dict[str, Any]:
        payload = {"query": query}
        res = self._request("POST", "/api/v1/policy/query", json=payload, timeout=6)
        if res is not None and res.status_code == 200:
            try:
                return res.json()
            except Exception:
                pass
        return {
            "answer": "Regulatory AI Assistant is temporarily unreachable. Please ensure the backend is running on port 8001.",
            "confidence": "offline",
            "sources": []
        }
