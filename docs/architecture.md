# System Architecture
**Project:** APAAR Verify by Sutrāyukti  
**SIH 2026 Problem Statement 26263**

---

## 1. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend / Web Application                     │
│  ┌────────────────────┬────────────────────┬──────────────────────────────┐  │
│  │ AICTE Dashboard    │ Institution Portal │ Verified Academic Journey    │  │
│  │ (Analytics & KPIs) │ (Intake & Uploads) │ & Record Verification        │  │
│  └────────────────────┴────────────────────┴──────────────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ HTTPS / JSON REST API
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Central Backend Core                         │
│  ┌────────────────────────┬────────────────────────┬──────────────────────┐  │
│  │ Auth & RBAC Middleware │ Upload & Batch Engine  │ Validation & Intake  │  │
│  ├────────────────────────┼────────────────────────┼──────────────────────┤  │
│  │ Exceptions & Review    │ Verification & Crypto  │ Tamper-Evident Audit │  │
│  └────────────────────────┴────────────────────────┴──────────────────────┘  │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ SQLAlchemy 2.0 ORM
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│               Relational Database (SQLite / PostgreSQL Compatible)           │
│  • institutions             • approved_intakes      • students (UUID)       │
│  • enrolments               • submissions           • validation_issues     │
│  • verification_references  • audit_events          • academic_events       │
└──────────────────────────────────────┬───────────────────────────────────────┘
                                       │ Documented Adapter Boundary
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      External Adapters & Optional Modules                    │
│  ┌───────────────────────────┬────────────────────────────────────────────┐  │
│  │ Mock APAAR Identity API   │ Optional EduPath (Career & PMSSS Advisory) │  │
│  │ (Explicitly Simulated)    │ (Adapted from EduSetu Domain Knowledge)    │  │
│  └───────────────────────────┴────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architectural Principles

1. **Single Backend of Truth**:
   The FastAPI backend holds all business logic, validation rules, role-based access checks, transaction handling, cryptographic signing, and database writes. The frontend never accesses the database directly.

2. **Decoupled Preview vs. Transactional Submission**:
   File validation is done via `POST /api/v1/uploads/validate` in memory, returning row-by-row issues without mutating database state. Commits occur via `POST /api/v1/uploads/submit`, which runs an atomic transaction revalidating rows inside the transaction lock with an idempotency key.

3. **Protection of Academic Identifiers**:
   Plaintext APAAR identifiers are never leaked in logs. In the database, records use internal UUIDs with protected token lookups (`apaar_lookup_token` generated via HMAC-SHA256 with an environment salt). Normal UI views display masked synthetic identifiers (`DEMO-APAAR-***1`).

4. **Tamper-Evident Verification**:
   Verification links point to `GET /api/v1/verify/{reference}` with an opaque token hash. QR codes embed only the verification URL, never raw student PII. Responses are cryptographically signed using an HMAC-SHA256 server secret, proving payload integrity and timestamping.

5. **EduSetu Codebase Reuse Strategy**:
   EduSetu's college data and scholarship rules are integrated cleanly as the optional student-facing **EduPath** module. Complex, non-functional cloud vector stores and unverified approval processes are excluded from the core regulatory pipeline to ensure zero friction and 100% test reproducibility.

