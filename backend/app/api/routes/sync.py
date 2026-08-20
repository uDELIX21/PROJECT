"""Offline sync endpoint (design §09): batch mutations, idempotent replays."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, require
from app.core.db import get_db
from app.schemas.requests import SyncBatchIn
from app.services import sync as sync_svc

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("/mutations")
def sync_mutations(body: SyncBatchIn, request: Request,
                   ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
                   db: Session = Depends(get_db)):
    results = sync_svc.apply_batch(db, ctx, [m.model_dump() for m in body.mutations])
    db.commit()
    return {"results": results}
