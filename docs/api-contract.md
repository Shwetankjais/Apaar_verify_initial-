# API Contract Specification
**Project:** APAAR Verify by Sutrāyukti  
**Base URL:** `http://localhost:8000` (or configured `API_BASE_URL`)  
**Specification Standard:** OpenAPI 3.1 / JSON REST

---

## 1. System Endpoints

### `GET /health`
- **Description:** Verifies service health, database connectivity, and engine version.
- **Response:** `200 OK`
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "service": "APAAR Verify Core API",
    "database": "connected",
    "timestamp": "2026-10-30T00:30:00Z"
  }
  ```

---

## 2. Institutions & Intake Endpoints

### `GET /api/v1/institutions`
- **Headers:** `X-User-Role: aicte_admin | institution_officer | verifier | auditor`  
  `X-Institution-Id: DEMO001` (optional / scoped)
- **Description:** Returns list of institutions accessible to current role.
- **Response:** `200 OK`
  ```json
  [
    {
      "id": "DEMO001",
      "code": "DEMO001",
      "name": "Mysuru Institute of Technology",
      "state": "Karnataka",
      "approval_status": "APPROVED",
      "contact_email": "admin@mit-demo.edu.in",
      "courses": ["CSE", "ECE", "MECH"]
    }
  ]
  ```

### `GET /api/v1/institutions/{id}/intake`
- **Description:** Returns approved intake figures (regular + supernumerary) and current active enrolment counts.
- **Response:** `200 OK`
  ```json
  {
    "institution_id": "DEMO001",
    "academic_year": "2025-2026",
    "intakes": [
      {
        "course_code": "CSE",
        "regular_intake": 40,
        "supernumerary_intake": 4,
        "enrolled_regular": 38,
        "enrolled_supernumerary": 2,
        "utilization_pct": 95.0,
        "status": "COMPLIANT"
      }
    ]
  }
  ```

---

## 3. Upload & Validation Endpoints

### `POST /api/v1/uploads/validate`
- **Body:** `multipart/form-data` with `file: (CSV/XLSX)`, `institution_id: string`, `academic_year: string`
- **Description:** Previews file rows, applies rules V001–V010, and reports row-level issues. **Mutates no database state.**
- **Response:** `200 OK`
  ```json
  {
    "batch_key": "bth_9f2a08...",
    "total_rows": 12,
    "eligible_count": 8,
    "review_required_count": 2,
    "rejected_count": 2,
    "issues": [
      {
        "row_number": 3,
        "rule_code": "V002",
        "severity": "ERROR",
        "field": "apaar_id",
        "explanation": "Malformed synthetic APAAR format",
        "suggested_correction": "Use format DEMO-APAAR-XXXX"
      }
    ],
    "preview_rows": [...]
  }
  ```

### `POST /api/v1/uploads/submit`
- **Body:** `JSON` `{ "batch_key": string, "institution_id": string, "academic_year": string, "rows": [...] }`
- **Description:** Atomic transactional submission. Re-validates within database transaction. Idempotent on `batch_key`. Commits eligible rows, queues exceptions, writes audit event.
- **Response:** `201 Created` or `200 OK` (if idempotently replayed)

### `GET /api/v1/uploads/{id}`
- **Description:** Returns details of a specific batch submission.

---

## 4. Student Records & Journey Endpoints

### `GET /api/v1/students`
- **Params:** `institution_id`, `search`, `academic_year`, `limit`, `offset`
- **Description:** Lists student master records with masked identifiers. Scoped by institution if caller is institutional officer.

### `GET /api/v1/students/{id}`
- **Description:** Detailed view of student identity and enrolment history.

### `GET /api/v1/students/{id}/journey`
- **Description:** Verified Academic Journey timeline (admission, enrolment, credits reported/validated, transfer events).

---

## 5. Dashboard & Analytics Endpoints

### `GET /api/v1/dashboard/summary`
- **Description:** Database-backed aggregate KPIs: total active students, approved intake, aggregate utilization, pending exceptions, total submissions.
- **Response:** `200 OK`

### `GET /api/v1/dashboard/institutions`
- **Description:** Per-institution drill-down aggregates (state, intake, utilization, exception counts).

---

## 6. Exception Management Endpoints

### `GET /api/v1/exceptions`
- **Params:** `institution_id`, `status` (OPEN, IN_REVIEW, RESOLVED), `rule_code`
- **Description:** Centralized queue of validation and compliance exceptions.

### `PATCH /api/v1/exceptions/{id}`
- **Body:** `{ "status": "RESOLVED" | "DISMISSED", "reviewer_comment": string }`
- **Description:** Human resolution of an exception with required explanation and audit logging.

---

## 7. Verification Endpoints

### `POST /api/v1/verification-requests`
- **Body:** `{ "student_id": string, "purpose": string, "expires_in_hours": integer }`
- **Description:** Generates an opaque, revocable verification reference and QR code URL.

### `GET /api/v1/verify/{reference}`
- **Description:** Publicly callable verification check. Checks expiry, revocation, and signature. Returns **strictly limited fields** (issuer, institution, programme, academic year, status). Never leaks raw personal data.

### `POST /api/v1/verify/{reference}/revoke`
- **Description:** Revokes an active verification reference.

---

## 8. Audit Trail Endpoints

### `GET /api/v1/audit`
- **Params:** `institution_id`, `action`, `actor`, `limit`
- **Description:** Tamper-evident audit trail of all sensitive operations.

