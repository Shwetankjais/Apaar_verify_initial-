# Deterministic Validation Engine & Status Model
**Project:** APAAR Verify by Sutrāyukti  
**SIH 2026 Problem Statement 26263**

---

## 1. Validation Rules Matrix

Every submission row is evaluated deterministically against the following test suite. Each validation issue produces a structured record:
`{ rule_code, severity, row_number, student_id, field, explanation, suggested_correction, resolution_state }`

| Rule Code | Rule Name | Condition | Severity | Expected Handling |
| :--- | :--- | :--- | :--- | :--- |
| **V001** | Required Field Missing | Missing mandatory fields: `student_name`, `institution_student_id`, `programme_course`, `academic_year`, `admission_date`, `category`, `seat_type`. | **HARD ERROR** | Row rejected. Cannot be committed to enrolment database. |
| **V002** | Malformed Demo APAAR Identifier | Identifier does not match prototype format `DEMO-APAAR-\d{4}` (or missing entirely). Format-only check; does not imply authoritative identity authenticity. | **HARD ERROR** | Row rejected. Suggest correction to proper synthetic format. |
| **V003** | Intra-Batch Duplicate Identifier | Two or more rows within the same upload share the same synthetic APAAR identifier or same institutional student ID. | **HARD ERROR** | Row rejected. Duplicate rows in single file flagged. |
| **V004** | Identifier Already Exists in Database | The APAAR identifier exists in the platform. Checked to determine if this is a legitimate update/re-enrolment vs an enrolment conflict. | **REVIEW REQUIRED** | Never automatically inferred as fraud. Flagged for officer review. |
| **V005** | Admissions Exceed Approved Intake | Total accepted + pending admissions in regular (or specific supernumerary) category exceeds the configured AICTE approved capacity. | **EXCEPTION** | Row flagged as intake excess exception. Blocked from automatic regular admission unless authorized supernumerary slot is applied. |
| **V006** | Inconsistent Category / Seat Fields | Inconsistency between category and seat type (e.g. `seat_type == 'NRI'` with `category == 'SC'`, or `seat_type == 'TFW'` with income above threshold). | **HARD ERROR / REVIEW** | Flags inconsistency based on documented demo rules. |
| **V007** | Potential Simultaneous Active Enrolment | Student has an existing `ACTIVE` enrolment at another institution for the overlapping academic year without an approved `TRANSFERRED` or `WITHDRAWN` event. | **REVIEW REQUIRED** | Flagged for manual review. If legitimate transfer certificate is presented, transfer history is recorded. |
| **V008** | Duplicate Batch / Idempotency Key | An upload with the same `batch_key` or file hash has already been processed for this institution. | **IDEMPOTENT** | Returns cached result of earlier run without creating duplicate database writes. |
| **V009** | Accepted Record Modification | Institutional officer attempts to alter an already `ACCEPTED` record (e.g., changing course or category). | **AUDIT / RE-REVIEW** | Preserves historical immutable snapshot, marks record for regulator re-review, and logs audit event. |
| **V010** | Unusual Enrolment Anomaly | Anomaly detection: batch contains >25% sudden change in admissions compared to historical trends or >15% validation error frequency. | **REVIEW REQUIRED** | Explainable anomaly alert generated for administrative oversight. |

---

## 2. Row Outcomes

Each row in an upload preview and submission transaction receives one of three outcomes:
1. **`REJECTED`**: A hard error (V001, V002, V003, V006) prevents acceptance.
2. **`REVIEW_REQUIRED`**: Syntactically valid but policy/data conflict detected (V004, V005, V007, V009, V010). Routed to the centralized exception queue.
3. **`ELIGIBLE`**: Mandatory checks passed. Ready for transactional commit. (Explicitly labeled: *Eligible under platform intake rules; not proof of external APAAR identity verification.*)

---

## 3. Approved Intake & Compliance Formula

$$\text{Intake Utilization (\%)} = \left( \frac{\text{Counted Active Admissions}}{\text{Applicable Approved Intake}} \right) \times 100$$

### Seat Category Accounting Rules:
- **Regular Intake**: Counts admissions where `seat_type == 'REGULAR'`. Capped strictly by `approved_intakes.regular_intake`.
- **Approved Supernumerary Intake**: Configured per course (e.g. Tuition Fee Waiver (TFW), EWS, J&K PMSSS, Foreign National/OCI, Sports Quota). Counted in separate versioned limits.
- **Transfers & Withdrawals**: Students with status `WITHDRAWN` or `TRANSFERRED` do not consume regular intake quota.

