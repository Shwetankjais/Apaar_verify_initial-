# APAAR Verify by Sutrāyukti
### Trusted academic records. Explainable validation. Secure verification.
**Smart India Hackathon (SIH) 2026 | Problem Statement 26263**  
*“Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions”*

---

> **DISCLAIMER:**  
> This application is an independent, non-official technological prototype developed for SIH 2026. All student identifiers (`DEMO-APAAR-XXXX`), institutions, and enrolments are synthetic demonstration data. This application does not claim official AICTE or APAAR accreditation, certification, or live government API connectivity.

---

## 🏛️ System Architecture

APAAR Verify is engineered with a strict **single-backend-of-truth** architecture. The FastAPI backend orchestrates deterministic validation, role-based tenant access control, transactional idempotency, cryptographic signatures, and audit trails. The frontend interacts strictly via authenticated JSON REST APIs.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Streamlit Interactive Frontend                      │
│   (AICTE Dashboard · Institution Intake · Verified Academic Journey)     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ HTTPS / JSON REST API
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Central Core                             │
│   • Auth & RBAC Middleware          • Deterministic Rule Engine (V001–10)│
│   • Transactional Batch Importer    • Tamper-Evident Audit Chaining      │
│   • Opaque Token Crypto Signer      • EduPath & Regulatory Assistant     │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │ SQLAlchemy ORM
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                Relational Database (SQLite / PostgreSQL)                 │
│  institutions · approved_intakes · students · enrolments · submissions   │
│  validation_issues · verification_references · academic_events · audit   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Core SIH 2026 Features (Problem Statement 26263)

1. **Institution Directory & Intake Configuration**:
   - Manages AICTE-approved regular intake capacity and supernumerary quotas (TFW, EWS, J&K PMSSS, Foreign National).
   - Distinct seat accounting ensures supernumerary seats never consume regular intake limits.

2. **Deterministic Data Intake & Validation Engine (Rules V001–V010)**:
   - **V001**: Required field missing (Hard error; reject row).
   - **V002**: Malformed demo identifier (Format check; clearly distinguishes syntax validation from external identity verification).
   - **V003**: Duplicate identifier within a single batch.
   - **V004**: Identifier already in database (Classified as update vs conflict; never assumed fraud).
   - **V005**: Admissions exceed applicable approved intake.
   - **V006**: Inconsistent category / NRI / supernumerary fields.
   - **V007**: Potential simultaneous active enrolment across institutions.
   - **V008**: Duplicate batch retry (Transactional idempotency key).
   - **V009**: Accepted record modification requires audit and re-review.
   - **V010**: Batch anomaly alert (>50% error rate).

3. **AICTE Central Executive Dashboard**:
   - Database-backed aggregates: Active Enrolments, Approved Intake Capacity, Intake Utilization %, Open Exceptions, and Submission Timeliness.
   - Plotly visualizations and institution-level drill-down.

4. **Centralized Exception Management Queue**:
   - Human-in-the-loop review workflow (`OPEN`, `RESOLVED`, `DISMISSED`) with required reviewer comments.
   - Explains why the alert fired, statutory reference, and suggested correction.

5. **Verified Academic Journey (Key Differentiator)**:
   - Chronological, issuer-authenticated academic timeline: Admission Confirmed → Active Enrolment → Semester Credits Reported → Credit Record Validated.
   - Strict regulatory distinction between credits *reported*, *validated*, *earned*, and *accepted by a receiving institution*.

6. **Tamper-Evident Verification & QR Codes**:
   - Generates high-entropy opaque reference codes and QR URLs.
   - Strictly returns permitted disclosure fields (no Aadhaar, no parentage, no phone).
   - Cryptographically signed with server HMAC-SHA256. Handles valid, expired, and revoked states.

7. **EduPath Opportunity Extension (EduSetu Domain Reuse)**:
   - Student-controlled college search and AICTE scholarship matching (PMSSS, Pragati, Saksham).

8. **AICTE Regulatory Handbook Assistant (Advisory RAG)**:
   - Clause-grounded Q&A backed by AICTE Approval Process Handbook (APH 2024–2027), APAAR guidelines, and DPDP Rules 2025.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+ (Tested on Python 3.13)
- macOS / Linux / Windows

### 2. Environment Setup
```bash
# Clone or navigate to the project directory
cd apaar_verify

# Activate virtual environment
source venv/bin/activate  # (Windows: venv\Scripts\activate)

# Install dependencies
pip install -r requirements.txt
```

### 3. Seed Database & Demo Datasets
```bash
python scripts/seed_demo.py
```
*Output: Seeds 3 institutions, 143 baseline students, approved intake quotas, sample academic milestones, and creates `data/faulty_upload_demo.csv` and `data/valid_upload_sample.csv`.*

### 4. Run Pytest Suite
```bash
pytest backend/tests
```
*Output: 14/14 tests pass (API endpoints, validation engine V001–V010, verification lifecycle).*

### 5. Launch Backend & Frontend

**Terminal 1 — FastAPI Backend:**
```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run frontend/app.py --server.port 8501
```
Web Interface: [http://localhost:8501](http://localhost:8501)

---

## 📁 Repository Structure

```
apaar_verify/
├── backend/
│   ├── app/
│   │   ├── api/             # REST Endpoints (Institutions, Uploads, Students, Dashboard, etc.)
│   │   ├── models/          # SQLAlchemy Database Models
│   │   ├── schemas/         # Pydantic Request & Response Schemas
│   │   ├── services/        # Business Logic, Rules V001-V010, Verification, Audit
│   │   ├── config.py        # Centralized Settings & Secrets
│   │   ├── database.py      # SQLAlchemy Session & Engine
│   │   └── main.py          # FastAPI App Entrypoint
│   └── tests/               # 14 Pytest Unit & Integration Tests
├── frontend/
│   ├── app.py               # Streamlit Government-Tech UI
│   └── api_client.py        # Backend API Client with RBAC Headers
├── data/                    # Synthetic Demo CSV Files (Faulty & Valid)
├── scripts/
│   └── seed_demo.py         # Database Seeding Script
├── docs/                    # Architecture, Validation Rules, Security, Demo Script
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔒 Security & Privacy Notes

- **Zero Aadhaar Collection**: Prototype strictly adheres to data minimization and DPDP Rules 2025.
- **Keyed Identifier Hashing**: APAAR identifiers are transformed into keyed HMAC lookup tokens to avoid unmasked plaintext database indexing.
- **Backend Authorization**: Tenant scoping prevents institutional officers from reading or mutating other colleges' records.
- **Tamper-Proof Audit Chaining**: Every submission, exception resolution, and verification access is cryptographically chained using SHA-256 hashes.

