from typing import Optional
import datetime
from pydantic import BaseModel

class AuditEventResponse(BaseModel):
    id: str
    actor_role: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    institution_id: Optional[str] = None
    previous_hash: Optional[str] = None
    event_hash: str
    metadata_json: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

