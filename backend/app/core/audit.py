"""Audit log writer (design §12/§20). Sensitive mutations MUST go through this."""
import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.ids import uuid7
from app.models.audit import AuditLog


def audit(db: Session, *, actor_id: uuid.UUID | None, action: str,
          entity_type: str, entity_id: Any, previous: Any = None, new: Any = None,
          reason: str | None = None, request: Request | None = None) -> AuditLog:
    ip = request.client.host if request is not None and request.client else None
    ua = request.headers.get("user-agent") if request is not None else None
    row = AuditLog(
        id=uuid7(),
        actor_user_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        previous=previous,
        new=new,
        reason=reason,
        ip=ip,
        user_agent=ua[:512] if ua else None,
    )
    db.add(row)
    return row
