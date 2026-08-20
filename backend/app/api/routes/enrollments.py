"""Enrollment & promotion endpoints (REQ-STU-02..04)."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.db import get_db
from app.models.core import Enrollment
from app.schemas import common
from app.schemas.requests import EnrollmentCreateIn, PromotionApplyIn
from app.services import enrollments as svc
from app.services import promotion as promo

router = APIRouter(prefix="/enrollments", tags=["enrollments"])


@router.get("")
def list_enrollments(class_stream_id: uuid.UUID | None = None,
                     academic_year_id: uuid.UUID | None = None,
                     status: str | None = Query(default="ACTIVE"),
                     limit: int = Query(default=50, ge=1, le=500),
                     offset: int = Query(default=0, ge=0),
                     ctx: AuthContext = Depends(require(rbac.MANAGE_ENROLLMENT)),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(Enrollment).where(Enrollment.school_id == school.id)
    if class_stream_id:
        stmt = stmt.where(Enrollment.class_stream_id == class_stream_id)
    if academic_year_id:
        stmt = stmt.where(Enrollment.academic_year_id == academic_year_id)
    if status:
        stmt = stmt.where(Enrollment.status == status)
    rows = db.scalars(stmt.order_by(Enrollment.created_at).limit(limit).offset(offset)).all()
    return {"items": [common.enrollment(e) for e in rows], "limit": limit, "offset": offset}


@router.post("", status_code=201)
def create_enrollment(body: EnrollmentCreateIn, request: Request,
                      ctx: AuthContext = Depends(require(rbac.MANAGE_ENROLLMENT)),
                      db: Session = Depends(get_db)):
    school = get_school(db)
    enrollment = svc.create_enrollment(db, school_id=school.id, actor_id=ctx.user.id,
                                       request=request, **body.model_dump(exclude_none=True))
    db.commit()
    return common.enrollment(enrollment)


@router.post("/{enrollment_id}/withdraw", status_code=200)
def withdraw(enrollment_id: uuid.UUID, request: Request,
             ctx: AuthContext = Depends(require(rbac.MANAGE_ENROLLMENT)),
             db: Session = Depends(get_db)):
    school = get_school(db)
    e = svc.get_enrollment(db, school.id, enrollment_id)
    svc.end_enrollment(db, e, outcome="WITHDRAWN", actor_id=ctx.user.id, request=request)
    db.commit()
    return common.enrollment(e)


@router.post("/{enrollment_id}/transfer", status_code=200)
def transfer(enrollment_id: uuid.UUID, request: Request,
             ctx: AuthContext = Depends(require(rbac.MANAGE_ENROLLMENT)),
             db: Session = Depends(get_db)):
    school = get_school(db)
    e = svc.get_enrollment(db, school.id, enrollment_id)
    svc.end_enrollment(db, e, outcome="TRANSFERRED", actor_id=ctx.user.id, request=request)
    db.commit()
    return common.enrollment(e)


@router.post("/promotion/preview")
def promotion_preview(body: PromotionApplyIn,
                      ctx: AuthContext = Depends(require(rbac.MANAGE_ENROLLMENT)),
                      db: Session = Depends(get_db)):
    school = get_school(db)
    return {"items": promo.preview(db, school.id, body.from_academic_year_id,
                                   body.to_academic_year_id)}


@router.post("/promotion/apply")
def promotion_apply(body: PromotionApplyIn, request: Request,
                    ctx: AuthContext = Depends(require(rbac.MANAGE_ENROLLMENT)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    batch = promo.apply_batch(db, school_id=school.id,
                              from_year_id=body.from_academic_year_id,
                              to_year_id=body.to_academic_year_id,
                              decisions=body.decisions,
                              stream_mapping=body.stream_mapping,
                              actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(batch.id), "status": batch.status,
            "from_year_id": str(batch.from_academic_year_id),
            "to_year_id": str(batch.to_academic_year_id)}
