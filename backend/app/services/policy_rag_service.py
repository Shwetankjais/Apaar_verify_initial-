"""
AICTE Policy & Regulatory Handbook Assistant
Advisory question-answering grounded in official public regulatory sources:
- AICTE Approval Process Handbook (APH 2024-2027)
- APAAR FAQ & Terms of Use (MoE)
- MeitY DPDP Rules 2025
"""

from typing import Dict, Any, List

OFFICIAL_POLICY_KB = [
    {
        "keywords": ["supernumerary", "tfw", "tuition fee waiver", "extra seats", "quota"],
        "topic": "Supernumerary Seats & TFW Guidelines",
        "answer": "Under AICTE Approval Process Handbook (APH 2024–2027, Section 3.14), Tuition Fee Waiver (TFW) seats up to a maximum of 5% of Approved Intake per Course are supernumerary in nature and are available exclusively to economically weaker candidates whose parent annual income is less than ₹8.00 Lakh. Other approved supernumerary categories include J&K PMSSS (2 seats per branch in eligible colleges) and FN/OCI quota (up to 15% supernumerary where approved).",
        "source_doc": "AICTE Approval Process Handbook 2024–2027",
        "clause": "Chapter III, Clause 3.14 (Supernumerary Seats)",
        "source_url": "https://aicte-qa.aicte-india.org/sites/default/files/APH%20Final.pdf",
        "version_date": "2024–2027"
    },
    {
        "keywords": ["apaar", "what is apaar", "format", "12 digit", "identifier"],
        "topic": "APAAR Academic Identity Nature & Standards",
        "answer": "According to the Ministry of Education APAAR Guidelines & FAQ, APAAR (Automated Permanent Academic Account Registry) is a unique 12-digit academic identity for lifelong learning. It is linked to DigiLocker and the Academic Bank of Credits (ABC) to facilitate credit mobility, digital degree verification, and streamlined admissions. An APAAR ID format validation checks syntax; it does not replace authorized institutional admission verification.",
        "source_doc": "Ministry of Education APAAR FAQs & Documentation",
        "clause": "Section 1 - Overview & Objectives",
        "source_url": "https://apaar.education.gov.in/faqs",
        "version_date": "2026 Edition"
    },
    {
        "keywords": ["excess", "over-admission", "intake", "penalty", "utilization"],
        "topic": "AICTE Intake Excess & Admission Compliance",
        "answer": "AICTE Approval Process Handbook strictly prohibits institutions from admitting students in excess of the Approved Regular Intake for any programme without explicit supernumerary or intake-enhancement sanction. Excess admissions trigger validation exceptions (Rule V005) and subject the institution to regulatory review, reduction of intake in subsequent years, or withdrawal of approval.",
        "source_doc": "AICTE Approval Process Handbook 2024–2027",
        "clause": "Chapter VII, Clause 7.2 (Penal Action for Violation of Norms)",
        "source_url": "https://aicte-qa.aicte-india.org/sites/default/files/APH%20Final.pdf",
        "version_date": "2024–2027"
    },
    {
        "keywords": ["transfer", "migration", "dual", "simultaneous", "two colleges"],
        "topic": "Student Migration, Transfer & Simultaneous Enrolment",
        "answer": "A student cannot hold simultaneous ACTIVE enrolments across two AICTE-approved institutions for the same regular full-time programme. In case of transfer, the issuing institution must record a WITHDRAWN or TRANSFERRED milestone in the academic timeline and issue a Transfer Certificate (TC). The receiving institution must present the transfer record to resolve cross-institution conflict flags (Rule V007).",
        "source_doc": "AICTE Academic Guidelines & ABC Mobility Framework",
        "clause": "Guidelines on Student Mobility and Credit Transfer",
        "source_url": "https://www.abc.gov.in/",
        "version_date": "2025–2026"
    },
    {
        "keywords": ["dpdp", "privacy", "aadhaar", "consent", "personal data"],
        "topic": "Digital Personal Data Protection & Identity Minimization",
        "answer": "Under MeitY DPDP Rules 2025 and judicial guidelines, public and educational platforms must practice data minimization. Collecting unnecessary national identity numbers (such as Aadhaar) for routine verification is prohibited when educational identifiers (APAAR) suffice. Public verification links must disclose only permitted non-sensitive fields, and all personal record accesses must be auditable.",
        "source_doc": "MeitY Digital Personal Data Protection Rules 2025",
        "clause": "Rule 4 (Data Minimization & Purpose Limitation)",
        "source_url": "https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa",
        "version_date": "2025"
    }
]

def query_policy_assistant(user_query: str) -> Dict[str, Any]:
    """Retrieves relevant official policy clause based on semantic keyword match."""
    q_words = user_query.lower().split()
    best_match = None
    best_score = 0

    for item in OFFICIAL_POLICY_KB:
        score = sum(1 for kw in item["keywords"] if kw in user_query.lower())
        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score > 0:
        return {
            "query": user_query,
            "has_answer": True,
            "topic": best_match["topic"],
            "answer": best_match["answer"],
            "source_document": best_match["source_doc"],
            "clause": best_match["clause"],
            "source_url": best_match["source_url"],
            "version_date": best_match["version_date"],
            "advisory_disclaimer": "Advisory regulatory guidance only. Official AICTE statutory orders, handbook publications, and authorized regulatory officers govern definitive decisions."
        }
    else:
        return {
            "query": user_query,
            "has_answer": False,
            "topic": "Uncertain / No Direct Statutory Match",
            "answer": "The available official regulatory corpus (AICTE APH 2024–2027, APAAR Guidelines, DPDP Rules) does not contain a specific clause directly addressing your exact query. Please refer directly to the AICTE portal or consult the regional AICTE camp office.",
            "source_document": "AICTE Official Portal",
            "clause": "General Inquiries",
            "source_url": "https://www.aicte-india.org",
            "version_date": "Current",
            "advisory_disclaimer": "Advisory regulatory guidance only."
        }

