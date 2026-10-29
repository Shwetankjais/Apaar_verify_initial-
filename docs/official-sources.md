# Official Sources and Grounding Policy
**Project:** APAAR Verify by Sutrāyukti  
**SIH 2026 Problem Statement 26263:** Development of an APAAR ID-Based Student Data Management and Verification Platform for AICTE-Approved Institutions  
**Document Version:** 1.0.0 (October 2026)

---

## 1. Verified Official References

The following official public government and regulatory sources govern the identity architecture, compliance thresholds, and data protection boundaries for this prototype:

| Source | Organization | Official URL | Verified Access Date | Key Grounding Principles |
| :--- | :--- | :--- | :--- | :--- |
| **APAAR FAQ** | Ministry of Education, Govt. of India | [https://apaar.education.gov.in/faqs](https://apaar.education.gov.in/faqs) | 2026-10-29 | Defines APAAR (Automated Permanent Academic Account Registry) as a unique 12-digit academic identity for lifelong learning, linked to DigiLocker and ABC. Clarifies that APAAR is an academic identifier, not a citizenship or biometric card. |
| **APAAR Privacy Policy** | Ministry of Education, Govt. of India | [https://apaar.education.gov.in/privacy-policy](https://apaar.education.gov.in/privacy-policy) | 2026-10-29 | Mandates purpose limitation, explicit consent, minimal data disclosure, and access controls for academic records. |
| **APAAR Terms of Use** | Ministry of Education, Govt. of India | [https://apaar.education.gov.in/termsofuse](https://apaar.education.gov.in/termsofuse) | 2026-10-29 | Specifies that academic credentials are authenticated via registered institutions (issuers). Issuer accountability is paramount. |
| **AICTE Approval Process Handbook (APH 2024–2027)** | All India Council for Technical Education | [https://aicte-qa.aicte-india.org/sites/default/files/APH%20Final.pdf](https://aicte-qa.aicte-india.org/sites/default/files/APH%20Final.pdf) | 2026-10-29 | Defines approved regular intake, approved supernumerary quota categories (TFW, EWS, J&K PMSSS, FN/OCI, Lateral Entry), intake compliance rules, and institutional reporting norms. |
| **Digital Personal Data Protection (DPDP) Rules 2025** | MeitY, Govt. of India | [https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa) | 2026-10-29 | Mandates data minimization, purpose limitation, audit trails of personal data access, and right to rectification. Strictly prohibits collecting unnecessary sensitive identifiers (e.g., Aadhaar) in non-statutory verification demos. |
| **Academic Bank of Credits (ABC)** | Ministry of Education / UGC | [https://www.abc.gov.in/](https://www.abc.gov.in/) | 2026-10-29 | Distinguishes credits reported, validated, earned, and accepted. Prohibits automated credit recognition across institutions without receiving-institution consent. |

---

## 2. Integration and Adapter Boundary Policy

1. **No Unauthorized Portal Scraping**: Under no circumstances does this application scrape internal portals (`apaar.education.gov.in`, `aicte-india.org`, or `nad.digilocker.gov.in`).
2. **Explicit Simulated Adapters**: Because live production API credentials are not issued to hackathon prototype sandboxes, all external APAAR verification and DigiLocker pulls are routed through an **explicitly documented adapter interface** (`APAARProviderInterface`) with an honest, visible `MockAPAARAdapter` returning synthetic status.
3. **Synthetic Demonstration Data Only**: All demo identifiers (`DEMO-APAAR-XXXX`), students (`Student Demo XXX`), and institutions are completely fictional.
4. **Advisory Disclaimer**: All pages and export outputs display a prominent badge:  
   `"Synthetic Demo / Non-Official Prototype — For SIH 2026 Demonstration Only"`.

