from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter
from backend.app.services.edupath_service import search_edupath_colleges, match_scholarships

router = APIRouter(prefix="/edupath", tags=["EduPath Opportunity Extension"])

class ScholarshipMatchRequest(BaseModel):
    family_income: float
    is_female: bool = False
    has_disability: bool = False

@router.get("/colleges", response_model=List[Dict[str, Any]])
def get_colleges(query: Optional[str] = None, state: Optional[str] = None):
    """Optional EduPath college and programme discovery."""
    return search_edupath_colleges(query=query, state=state)

@router.post("/scholarships/match", response_model=List[Dict[str, Any]])
def get_scholarships(req: ScholarshipMatchRequest):
    """Optional EduPath scholarship eligibility evaluation."""
    return match_scholarships(
        family_income=req.family_income,
        is_female=req.is_female,
        has_disability=req.has_disability
    )

