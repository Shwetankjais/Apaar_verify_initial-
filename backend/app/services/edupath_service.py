"""
EduPath Student Opportunity Extension
Reuses domain knowledge and college/scholarship catalogs from EduSetu.
Keeps recommendations advisory, student-controlled, and separate from regulatory validation.
"""

from typing import List, Dict, Any, Optional

EDUPATH_COLLEGES = [
    {
        "id": "mit_mysuru",
        "name": "Mysuru Institute of Technology",
        "state": "Karnataka",
        "district": "Mysuru",
        "type": "Technical Institute",
        "aicte_approved": True,
        "programmes": ["Computer Science and Engineering", "Electronics and Communication", "Mechanical Engineering"],
        "eligibility_criteria": "10+2 with Physics, Mathematics & minimum 50% marks in aggregate.",
        "scholarships_accepted": ["PMSSS", "National Scholarship Portal", "AICTE Pragati"],
        "data_freshness": "AICTE Approval Handbook 2024–2027"
    },
    {
        "id": "dec_pune",
        "name": "Deccan Engineering College",
        "state": "Maharashtra",
        "district": "Pune",
        "type": "Engineering College",
        "aicte_approved": True,
        "programmes": ["Computer Science and Engineering", "Information Technology", "Civil Engineering"],
        "eligibility_criteria": "10+2 PCM with valid state/national entrance score.",
        "scholarships_accepted": ["PMSSS", "MahaDBT", "AICTE Saksham"],
        "data_freshness": "AICTE Approval Handbook 2024–2027"
    },
    {
        "id": "cti_mangalore",
        "name": "Coastal Technical Institute",
        "state": "Karnataka",
        "district": "Dakshina Kannada",
        "type": "Polytechnic & Engineering",
        "aicte_approved": True,
        "programmes": ["Electronics and Communication", "Electrical Engineering", "Robotics"],
        "eligibility_criteria": "10+2 with PCM or recognized 3-year Diploma for Lateral Entry.",
        "scholarships_accepted": ["PMSSS", "AICTE Swanath", "National Scholarship Portal"],
        "data_freshness": "AICTE Approval Handbook 2024–2027"
    },
    {
        "id": "nit_srinagar",
        "name": "National Institute of Technology Srinagar",
        "state": "Jammu & Kashmir",
        "district": "Srinagar",
        "type": "National Institute of Technology (MoE)",
        "aicte_approved": True,
        "programmes": ["Computer Science and Engineering", "Information Technology", "Electronics & Communication"],
        "eligibility_criteria": "JEE Main CRL Rank + JoSAA / CSAB / PMSSS Counselling.",
        "scholarships_accepted": ["AICTE PMSSS", "Central Sector Scholarship"],
        "data_freshness": "EduSetu Catalog 2024"
    }
]

EDUPATH_SCHOLARSHIPS = [
    {
        "id": "pmsss",
        "name": "Prime Minister's Special Scholarship Scheme (PMSSS)",
        "provider": "AICTE / Ministry of Education",
        "portal_url": "https://www.aicte-india.org/bureaus/jk",
        "max_income": 800000,
        "benefit": "Tuition fees up to ₹1.25L - ₹3.00L + ₹1.00L/yr maintenance allowance DBT.",
        "eligibility_summary": "Domiciles of J&K / Ladakh passing Class 12, family income under ₹8 LPA.",
        "documents": ["Domicile Certificate", "Class 12 Marksheet", "Income Certificate", "APAAR / DigiLocker"]
    },
    {
        "id": "pragati",
        "name": "AICTE Pragati Scholarship for Girl Students",
        "provider": "AICTE",
        "portal_url": "https://www.aicte-india.org/schemes/students-development-schemes/Pragati",
        "max_income": 800000,
        "benefit": "₹50,000 per annum for tuition and contingency support.",
        "eligibility_summary": "Female students admitted to 1st year of Degree/Diploma in AICTE approved institution.",
        "documents": ["Admission Proof", "Income Certificate (< 8 LPA)", "Class 10/12 Marksheet"]
    },
    {
        "id": "saksham",
        "name": "AICTE Saksham Scholarship for Specially-Abled Students",
        "provider": "AICTE",
        "portal_url": "https://www.aicte-india.org/schemes/students-development-schemes/Saksham",
        "max_income": 800000,
        "benefit": "₹50,000 per annum towards educational expenses.",
        "eligibility_summary": "Specially-abled students with disability >= 40% admitted to AICTE approved technical programmes.",
        "documents": ["Disability Certificate (>= 40%)", "AICTE College Admission Letter", "Income Certificate"]
    }
]

def search_edupath_colleges(query: Optional[str] = None, state: Optional[str] = None) -> List[Dict[str, Any]]:
    results = EDUPATH_COLLEGES
    if state and state != "All":
        results = [c for c in results if c["state"].lower() == state.lower()]
    if query:
        q = query.lower()
        results = [
            c for c in results 
            if q in c["name"].lower() or any(q in p.lower() for p in c["programmes"])
        ]
    return results

def match_scholarships(family_income: float, is_female: bool = False, has_disability: bool = False) -> List[Dict[str, Any]]:
    matches = []
    for s in EDUPATH_SCHOLARSHIPS:
        eligible = True
        if family_income > s["max_income"]:
            eligible = False
        if s["id"] == "pragati" and not is_female:
            eligible = False
        if s["id"] == "saksham" and not has_disability:
            eligible = False

        matches.append({
            **s,
            "is_eligible": eligible,
            "eligibility_note": "Eligible based on income and demographic criteria." if eligible else "Income or profile criteria not met."
        })
    return matches

