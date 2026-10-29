import datetime
import hashlib
import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.audit_event import AuditEvent

def hash_audit_record(actor_id: str, action: str, entity_type: str, entity_id: str, prev_hash: str, timestamp_str: str) -> str:
    payload = f"{actor_id}|{action}|{entity_type}|{entity_id}|{prev_hash}|{timestamp_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def record_audit_event(
    db: Session,
    actor_role: str,
    actor_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    institution_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditEvent:
    # Find last audit event for chaining
    last_event = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).first()
    prev_hash = last_event.event_hash if last_event else "GENESIS_BLOCK_HASH"
    
    now = datetime.datetime.utcnow()
    event_hash = hash_audit_record(actor_id, action, entity_type, entity_id, prev_hash, now.isoformat())
    
    event = AuditEvent(
        actor_role=actor_role,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        institution_id=institution_id,
        previous_hash=prev_hash,
        event_hash=event_hash,
        metadata_json=json.dumps(metadata or {}),
        timestamp=now
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

