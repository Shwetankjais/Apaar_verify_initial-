import os
import requests
from typing import Optional, Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _headers(self, role: str, institution_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "X-User-Role": role,
            "X-User-Id": user_id or f"{role}@sutrayukti.gov.in"
        }
        if institution_id:
            headers["X-Institution-Id"] = institution_id
        return headers

    def get_health(self) -> Dict[str, Any]:
        res = requests.get(f"{self.base_url}/health", timeout=5)
        return res.json()

    def get_dashboard_summary(self, role: str, academic_year: str = "2025-2026") -> Dict[str, Any]:
        res = requests.get(
            f"{self.base_url}/api/v1/dashboard/summary?academic_year={academic_year}",
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def get_dashboard_institutions(self, role: str, academic_year: str = "2025-2026") -> list:
        res = requests.get(
            f"{self.base_url}/api/v1/dashboard/institutions?academic_year={academic_year}",
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def get_institutions(self, role: str, institution_id: Optional[str] = None) -> list:
        res = requests.get(
            f"{self.base_url}/api/v1/institutions",
            headers=self._headers(role, institution_id),
            timeout=10
        )
        return res.json()

    def get_institution_intake(self, institution_id: str, role: str, academic_year: str = "2025-2026") -> Dict[str, Any]:
        res = requests.get(
            f"{self.base_url}/api/v1/institutions/{institution_id}/intake?academic_year={academic_year}",
            headers=self._headers(role, institution_id),
            timeout=10
        )
        return res.json()

    def validate_file(self, file_bytes: bytes, filename: str, institution_id: str, role: str, academic_year: str = "2025-2026") -> Dict[str, Any]:
        files = {"file": (filename, file_bytes, "text/csv")}
        data = {"institution_id": institution_id, "academic_year": academic_year}
        res = requests.post(
            f"{self.base_url}/api/v1/uploads/validate",
            files=files,
            data=data,
            headers=self._headers(role, institution_id),
            timeout=15
        )
        return res.json()

    def submit_batch(self, batch_key: str, institution_id: str, academic_year: str, filename: str, rows: list, role: str) -> Dict[str, Any]:
        payload = {
            "batch_key": batch_key,
            "institution_id": institution_id,
            "academic_year": academic_year,
            "file_name": filename,
            "rows": rows
        }
        res = requests.post(
            f"{self.base_url}/api/v1/uploads/submit",
            json=payload,
            headers=self._headers(role, institution_id),
            timeout=15
        )
        return res.json()

    def get_submissions(self, role: str, institution_id: Optional[str] = None) -> list:
        res = requests.get(
            f"{self.base_url}/api/v1/uploads",
            headers=self._headers(role, institution_id),
            timeout=10
        )
        return res.json()

    def get_students(self, role: str, institution_id: Optional[str] = None, search: Optional[str] = None) -> list:
        url = f"{self.base_url}/api/v1/students?limit=50"
        if search:
            url += f"&search={search}"
        res = requests.get(
            url,
            headers=self._headers(role, institution_id),
            timeout=10
        )
        return res.json()

    def get_student_detail(self, student_id: str, role: str) -> Dict[str, Any]:
        res = requests.get(
            f"{self.base_url}/api/v1/students/{student_id}",
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def get_student_journey(self, student_id: str, role: str) -> list:
        res = requests.get(
            f"{self.base_url}/api/v1/academic-journey/{student_id}",
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def add_academic_milestone(self, payload: dict, role: str) -> Dict[str, Any]:
        res = requests.post(
            f"{self.base_url}/api/v1/academic-journey/events",
            json=payload,
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def get_exceptions(self, role: str, institution_id: Optional[str] = None, status_filter: Optional[str] = None) -> list:
        url = f"{self.base_url}/api/v1/exceptions"
        if status_filter:
            url += f"?status_filter={status_filter}"
        res = requests.get(
            url,
            headers=self._headers(role, institution_id),
            timeout=10
        )
        return res.json()

    def resolve_exception(self, issue_id: str, new_status: str, comment: str, role: str) -> Dict[str, Any]:
        res = requests.patch(
            f"{self.base_url}/api/v1/exceptions/{issue_id}",
            json={"status": new_status, "reviewer_comment": comment},
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def create_verification_ref(self, student_id: str, role: str, purpose: str = "EMPLOYMENT_VERIFICATION", hours: int = 72) -> Dict[str, Any]:
        res = requests.post(
            f"{self.base_url}/api/v1/verification-requests",
            json={"student_id": student_id, "purpose": purpose, "expires_in_hours": hours},
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def verify_reference(self, reference_code: str, role: str = "verifier") -> Dict[str, Any]:
        res = requests.get(
            f"{self.base_url}/api/v1/verify/{reference_code}",
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def revoke_reference(self, reference_code: str, reason: str, role: str) -> Dict[str, Any]:
        res = requests.post(
            f"{self.base_url}/api/v1/verify/{reference_code}/revoke?reason={reason}",
            headers=self._headers(role),
            timeout=10
        )
        return res.json()

    def get_audit_trail(self, role: str, institution_id: Optional[str] = None) -> list:
        res = requests.get(
            f"{self.base_url}/api/v1/audit",
            headers=self._headers(role, institution_id),
            timeout=10
        )
        return res.json()

    def search_edupath(self, query: Optional[str] = None, state: Optional[str] = None) -> list:
        url = f"{self.base_url}/api/v1/edupath/colleges"
        params = []
        if query: params.append(f"query={query}")
        if state: params.append(f"state={state}")
        if params: url += "?" + "&".join(params)
        res = requests.get(url, timeout=5)
        return res.json()

    def match_scholarships(self, family_income: float, is_female: bool, has_disability: bool) -> list:
        res = requests.post(
            f"{self.base_url}/api/v1/edupath/scholarships/match",
            json={"family_income": family_income, "is_female": is_female, "has_disability": has_disability},
            timeout=5
        )
        return res.json()

    def ask_policy(self, query: str) -> Dict[str, Any]:
        res = requests.post(
            f"{self.base_url}/api/v1/policy/query",
            json={"query": query},
            timeout=5
        )
        return res.json()

