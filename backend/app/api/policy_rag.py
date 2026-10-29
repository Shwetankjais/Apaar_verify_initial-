from typing import Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter
from backend.app.services.policy_rag_service import query_policy_assistant

router = APIRouter(prefix="/policy", tags=["AICTE Policy & Handbook Assistant"])

class PolicyQueryRequest(BaseModel):
    query: str

@router.post("/query", response_model=Dict[str, Any])
def ask_policy_handbook(req: PolicyQueryRequest):
    """Answers regulatory and policy handbook questions with official AICTE/APAAR/DPDP citations."""
    return query_policy_assistant(req.query)

