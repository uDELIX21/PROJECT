"""Teacher appraisal endpoints (REQ-APR-01): confidential, evaluator-gated."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, current_user, get_school, require
from app.core.db import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.models.core import Teacher
from app.models.operations import AppraisalCriterion, AppraisalScore, TeacherAppraisal
from app.schemas.requests import (AppraisalCreateIn, AppraisalScoresIn, AppraisalSubmitIn,
                                  CriterionIn)
from app.services import appraisals as svc

router = APIRouter(prefix="/appraisals", tags=["appraisals"])


def _appraisal_or_404(db: Session, school_id: uuid.UUID, appraisal_id: uuid.UUID
                      ) -> TeacherAppraisal:
    a = db.get(TeacherAppraisal, appraisal_id)
    if a is None or a.school_id != school_id:
        raise NotFoundError("Appraisal not found.")
    return a


def _assert_can_view(ctx: AuthContext, db: Session, appraisal: TeacherAppraisal) -> None:
    """Evaluators/head/admin see appraisals; teachers only their own (confidentiality)."""
    if ctx.has(rbac.APPRAISE_TEACHER):
        return
    if ctx.user.teacher_id is not None and appraisal.teacher_id == ctx.user.teacher_id:
        if appraisal.status == "DRAFT":
            raise NotFoundError("Appraisal not found.")  # drafts stay confidential
        return
    raise NotFoundError("Appraisal not found.")  # uniform — no existence leak


@router.get("/criteria")
def list_criteria(ctx: AuthContext = Depends(require(rbac.APPRAISE_TEACHER)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    svc.bootstrap_criteria(db, school.id)
    db.commit()
    rows = svc.criteria_for(db, school.id)
    return {"items": [{"id": str(c.id), "code": c.code, "name": c.name,
                       "max_score": c.max_score, "weight_pct": float(c.weight_pct)}
                      for c in rows]}


@router.put("/criteria")
def update_criterion(body: CriterionIn, request: Request,
                     ctx: AuthContext = Depends(require(rbac.APPRAISE_TEACHER)),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    c = db.get(AppraisalCriterion, body.criterion_id)
    if c is None or c.school_id != school.id:
        raise NotFoundError("Criterion not found.")
    if body.max_score is not None and body.max_score > 0:
        c.max_score = body.max_score
    if body.weight_pct is not None and body.weight_pct >= 0:
        c.weight_pct = body.weight_pct
    if body.is_active is not None:
        c.is_active = body.is_active
    db.commit()
    return {"id": str(c.id), "max_score": c.max_score, "weight_pct": float(c.weight_pct)}


@router.get("")
def list_appraisals(teacher_id: uuid.UUID | None = None,
                    ctx: AuthContext = Depends(require(rbac.VIEW_TEACHER)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(TeacherAppraisal).where(TeacherAppraisal.school_id == school.id)
    if ctx.user.teacher_id is not None:
        # teachers: own only (confidentiality)
        stmt = stmt.where(TeacherAppraisal.teacher_id == ctx.user.teacher_id,
                          TeacherAppraisal.status != "DRAFT")
    elif teacher_id:
        stmt = stmt.where(TeacherAppraisal.teacher_id == teacher_id)
    rows = db.scalars(stmt.order_by(TeacherAppraisal.created_at.desc()).limit(100)).all()
    return {"items": [{"id": str(a.id), "teacher_id": str(a.teacher_id),
                       "status": a.status, "period_from": str(a.period_from),
                       "period_to": str(a.period_to),
                       "overall_rating": float(a.overall_rating)
                       if a.overall_rating is not None else None} for a in rows]}


@router.post("", status_code=201)
def create_appraisal(body: AppraisalCreateIn, request: Request,
                     ctx: AuthContext = Depends(require(rbac.APPRAISE_TEACHER)),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    a = svc.create_appraisal(db, school_id=school.id, teacher_id=body.teacher_id,
                             evaluator_user_id=ctx.user.id, period_from=body.period_from,
                             period_to=body.period_to, request=request)
    db.commit()
    return {"id": str(a.id), "status": a.status}


@router.get("/{appraisal_id}")
def get_appraisal(appraisal_id: uuid.UUID,
                  ctx: AuthContext = Depends(require(rbac.VIEW_TEACHER)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    a = _appraisal_or_404(db, school.id, appraisal_id)
    _assert_can_view(ctx, db, a)
    scores = db.scalars(select(AppraisalScore).where(
        AppraisalScore.appraisal_id == appraisal_id)).all()
    criteria = {c.id: c for c in svc.criteria_for(db, school.id)}
    teacher = db.get(Teacher, a.teacher_id)
    return {"id": str(a.id), "teacher_id": str(a.teacher_id),
            "teacher_name": teacher.full_name if teacher else None,
            "evaluator_user_id": str(a.evaluator_user_id), "status": a.status,
            "period_from": str(a.period_from), "period_to": str(a.period_to),
            "overall_rating": float(a.overall_rating) if a.overall_rating is not None else None,
            "overall_comment": a.overall_comment,
            "scores": [{"criterion_id": str(s.criterion_id),
                        "criterion": criteria[s.criterion_id].name
                        if s.criterion_id in criteria else None,
                        "score": float(s.score),
                        "max_score": criteria[s.criterion_id].max_score
                        if s.criterion_id in criteria else None,
                        "comment": s.comment} for s in scores]}


@router.put("/{appraisal_id}/scores")
def save_scores(appraisal_id: uuid.UUID, body: AppraisalScoresIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.APPRAISE_TEACHER)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    a = _appraisal_or_404(db, school.id, appraisal_id)
    svc.save_scores(db, a, [s.model_dump() for s in body.scores],
                    actor_id=ctx.user.id, request=request)
    db.commit()
    return {"saved": len(body.scores)}


@router.post("/{appraisal_id}/submit")
def submit(appraisal_id: uuid.UUID, body: AppraisalSubmitIn, request: Request,
           ctx: AuthContext = Depends(require(rbac.APPRAISE_TEACHER)),
           db: Session = Depends(get_db)):
    school = get_school(db)
    a = _appraisal_or_404(db, school.id, appraisal_id)
    svc.submit_appraisal(db, a, actor_id=ctx.user.id,
                         overall_comment=body.overall_comment, request=request)
    db.commit()
    return {"status": a.status, "overall_rating": a.overall_rating}


@router.post("/{appraisal_id}/acknowledge")
def acknowledge(appraisal_id: uuid.UUID, request: Request,
                ctx: AuthContext = Depends(current_user),
                db: Session = Depends(get_db)):
    school = get_school(db)
    a = _appraisal_or_404(db, school.id, appraisal_id)
    if ctx.user.teacher_id is None or a.teacher_id != ctx.user.teacher_id:
        raise ForbiddenError("Only the appraised teacher can acknowledge.",
                             code="NOT_YOUR_APPRAISAL")
    svc.acknowledge_appraisal(db, a, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"status": a.status}
