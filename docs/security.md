# Security, Privacy & DPDP Compliance
**Project:** APAAR Verify by Sutrāyukti  
**SIH 2026 Problem Statement 26263**

---

## 1. Data Minimization & Privacy Protection

- **No Aadhaar Collection**: Under no circumstances does this prototype collect, store, or process 12-digit Aadhaar numbers or biometric data. In compliance with MeitY DPDP Rules 2025 and judicial guidelines, academic verification must rely solely on the educational identity concept (APAAR) and institutional roll numbers.
- **Protected Lookup Tokens**: Rather than storing raw or unsalted plaintext identifiers in database indexes, APAAR identifiers are hashed with a server-managed HMAC secret (`HMAC-SHA256(APAAR_SALT, identifier)`). This enables deterministic lookups without risking database rainbow-table reversal.
- **Identifier Masking**: All frontend views, reports, and API lists mask APAAR identifiers (e.g. `DEMO-APAAR-***1`).
- **Zero Raw PII in Verification QR**: The verification QR code contains only a high-entropy UUID reference URL (`https://.../api/v1/verify/vref_8f3a9e...`). It contains zero raw names, roll numbers, or course strings.

---

## 2. Backend Role-Based Access Control (RBAC) & Tenant Scoping

Access control is strictly enforced at the FastAPI middleware/dependency level:
1. **Regulator Admin (`aicte_admin`)**: Unrestricted national/cross-institution visibility, intake configuration, exception adjudication, and regulatory analytics.
2. **Institution Officer (`institution_officer`)**: Restricted strictly to their own institution's submissions, intake metrics, and student records. Cross-tenant reads or writes return HTTP 403 Forbidden.
3. **Verifier (`verifier`)**: Can only inspect opaque verification references via `GET /api/v1/verify/{ref}`. Cannot search student database or view institutional rosters.
4. **Auditor (`auditor`)**: Read-only access to tamper-evident audit logs and submission histories. Cannot mutate records.
5. **Student (`student`)**: Read-only view of their own verified academic journey and ability to generate an expiring verification reference.

---

## 3. Cryptographic Verification & Tamper-Evidence

- **Signed Digital Payload**: When a verification reference is evaluated, the backend produces an HMAC-SHA256 cryptographic signature of the canonical permitted fields (`institution_id`, `student_hash`, `course`, `academic_year`, `status`, `timestamp`). A verification signature proves that the payload was emitted by the authorized Sutrāyukti verification server and was not tampered with in transit.
- **Revocation & Expiry**: Every verification reference includes an explicit expiration timestamp (`expires_at`) and an active boolean (`is_revoked`). Expired or revoked references are rejected with clear, transparent rejection reason codes.
- **Tamper-Evident Audit Chain**: Audit events are cryptographically hashed and sequenced. Modification of historical audit rows breaks the hash consistency.

