"""Audit log read access (REQ-AUD-03): restricted, read-only, no delete."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, require
from app.core.db import get_db
from app.models.audit import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit(action: str | None = None, entity_type: str | None = None,
               entity_id: str | None = None,
               limit: int = Query(default=50, ge=1, le=200),
               offset: int = Query(default=0, ge=0),
               ctx: AuthContext = Depends(require(rbac.VIEW_AUDIT)),
               db: Session = Depends(get_db)):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    rows = db.scalars(stmt.order_by(AuditLog.occurred_at.desc())
                      .limit(limit).offset(offset)).all()
    return {"items": [{"id": str(r.id), "action": r.action, "entity_type": r.entity_type,
                       "entity_id": r.entity_id, "actor_user_id": str(r.actor_user_id) if r.actor_user_id else None,
                       "previous": r.previous, "new": r.new, "reason": r.reason,
                       "ip": r.ip, "occurred_at": r.occurred_at.isoformat()} for r in rows],
            "limit": limit, "offset": offset}
