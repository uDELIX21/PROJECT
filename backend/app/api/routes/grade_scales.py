"""Grading scale configuration endpoints (REQ-GRD-01)."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.db import get_db
from app.schemas.requests import ScaleBandsPutIn, ScaleCreateIn
from app.services import grading

router = APIRouter(prefix="/grade-scales", tags=["grade-scales"])


@router.get("")
def list_scales(ctx: AuthContext = Depends(require(rbac.VIEW_GRADES_CONFIG)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    from app.models.academic import GradeScale
    rows = db.scalars(select(GradeScale).where(GradeScale.school_id == school.id)).all()
    return {"items": [{"id": str(s.id), "name": s.name, "scope_band": s.scope_band,
                       "grade_id": str(s.grade_id) if s.grade_id else None,
                       "academic_year_id": str(s.academic_year_id) if s.academic_year_id else None,
                       "is_default": s.is_default,
                       "bands": [{"min_score": float(b.min_score), "max_score": float(b.max_score),
                                  "code": b.code, "remark": b.remark, "rank": b.rank}
                                 for b in grading.bands_for(db, s.id)]} for s in rows]}


@router.post("", status_code=201)
def create_scale(body: ScaleCreateIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.MANAGE_GRADES_CONFIG)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    scale = grading.create_scale(
        db, school_id=school.id, name=body.name,
        bands_payload=[b.model_dump() for b in body.bands],
        actor_id=ctx.user.id, scope_band=body.scope_band,
        grade_id=body.grade_id, academic_year_id=body.academic_year_id,
        is_default=body.is_default, request=request)
    db.commit()
    return {"id": str(scale.id), "name": scale.name}


@router.put("/{scale_id}/bands")
def replace_bands(scale_id: uuid.UUID, body: ScaleBandsPutIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_GRADES_CONFIG)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    scale = grading.get_scale(db, school.id, scale_id)
    grading.replace_bands(db, scale, [b.model_dump() for b in body.bands],
                          actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(scale.id), "bands": [b.model_dump() for b in body.bands]}
