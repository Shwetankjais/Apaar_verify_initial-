# 5-to-7-Minute Judge Demonstration Script
**Project:** APAAR Verify by Sutrāyukti  
**SIH 2026 Problem Statement 26263**

---

## Demo Timing & Narrative Arc

| Time | Stage | Action / Talking Point |
| :--- | :--- | :--- |
| **0:00 – 1:00** | **AICTE Executive Dashboard** | Open the platform with the **AICTE Administrator** role. Show database-backed KPIs: Total Active Enrolments (112), Approved Intake Capacity (145), Intake Utilization (~77%), Pending Exceptions (0), and Institutional Compliance breakdown. Highlight the visible **"Synthetic Demo Data"** badge. |
| **1:00 – 2:30** | **Institutional Upload & Validation Preview** | Switch role to **Institution Officer** for `DEMO001 (Mysuru Institute of Technology)`. Go to **Data Intake & Submissions**. Upload the intentionally flawed file `data/faulty_upload_demo.csv`. Click **Validate File (Preview)**. Explain that no database rows were modified. Walk the judges through the explainable row-level rule codes: `V001` (missing required fields), `V002` (malformed APAAR format), `V003` (duplicate within batch), `V004` (already existing identifier), `V005` (intake capacity exceeded), `V006` (inconsistent category vs seat type), `V007` (cross-institution active enrolment overlap). |
| **2:30 – 3:30** | **Transactional Commit & Idempotency** | Show how the system rejects hard errors while separating reviewable policy flags. Upload the clean correction batch `data/valid_upload_sample.csv`. Click **Submit Eligible Records**. Show the atomic transaction succeeding, the batch history updating with batch ID, and the dashboard metrics immediately reflecting the new database counts. Re-submit the same batch to prove **V008 Idempotency** (no duplicate writes). |
| **3:30 – 4:30** | **Exception Management & Cross-Institution Review** | Navigate to the **Exception Management Queue**. Show rule `V007` (Cross-institution duplicate): Student `DEMO-APAAR-0042` was enrolled at Deccan Engineering College and now appears at Coastal Technical Institute. Explain why Sutrāyukti **never automatically labels this fraud**; show the officer verifying the transfer certificate, adding reviewer comments, and adjudicating the exception to `RESOLVED (Transfer Accepted)`. Show the immutable audit log entry created in real time. |
| **4:30 – 5:30** | **Secure Record Verification & QR Code** | Switch to **Verification Portal**. Look up an active student record (`DEMO-APAAR-0001`). Generate a secure, expiring verification reference. Show the generated QR code. Demonstrate the verification endpoint response: only permitted fields are exposed (no Aadhaar, no parentage, no phone). Next, demonstrate entering an **expired** reference and a **revoked** reference; show clear rejection messages with cryptographic tamper verification. |
| **5:30 – 6:30** | **Verified Academic Journey (Key Differentiator)** | Switch to **Academic Journey** view. Select `DEMO-APAAR-0010`. Show the chronological timeline of issuer-signed milestones: Admission Confirmed → Active Enrolment → Semester 1 Credits Reported (22 credits) → Credit Record Validated. Explain the crucial regulatory distinction between credits *reported*, *validated*, *earned*, and *accepted by a receiving institution*. |
| **6:30 – 7:00** | **Optional EduPath Extension & Conclusion** | Briefly showcase the integrated **EduPath** advisory tab: student-controlled college search and PMSSS scholarship match adapted from EduSetu. Summarize: Trusted academic records, explainable validation, and secure verification for AICTE institutions. |

