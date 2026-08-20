"""Early-childhood developmental assessment + core competency ratings (REQ-ECD-*)."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import (AuthContext, assert_stream_visible, assert_student_visible,
                          get_school, require)
from app.core.db import get_db
from app.core.errors import ConflictError, NotFoundError
from app.models.academic import CoreCompetency, DevelopmentalDomain
from app.models.core import ClassStream, Enrollment, Grade
from app.schemas.requests import (CompetencyRatingIn, ObservationIn, RatingsPutIn)
from app.services import ecd as svc

router = APIRouter(prefix="/ecd", tags=["ecd"])


def _enrollment(db: Session, school_id: uuid.UUID, enrollment_id: uuid.UUID) -> Enrollment:
    e = db.get(Enrollment, enrollment_id)
    if e is None or e.school_id != school_id:
        raise NotFoundError("Enrollment not found.")
    return e


@router.get("/domains")
def list_domains(ctx: AuthContext = Depends(require(rbac.VIEW_GRADES_CONFIG)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    return {"items": [{"id": str(d.id), "code": d.code, "name": d.name}
                      for d in svc.domains(db, school.id)]}


@router.get("/ratings")
def get_ratings(enrollment_id: uuid.UUID, term_id: uuid.UUID,
                ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    e = _enrollment(db, school.id, enrollment_id)
    assert_student_visible(ctx, db, e.student_id)
    rows = svc.ratings_for(db, enrollment_id, term_id)
    domains = {d.id: d for d in svc.domains(db, school.id)}
    return {"items": [{"id": str(r.id), "domain_id": str(r.domain_id),
                       "domain": domains.get(r.domain_id).name if r.domain_id in domains else None,
                       "rating": r.rating, "comment": r.comment} for r in rows]}


@router.put("/ratings")
def put_ratings(body: RatingsPutIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
                db: Session = Depends(get_db)):
    """ECD ratings are qualitative — the only assessment mode for this band (BR-M07)."""
    school = get_school(db)
    e = _enrollment(db, school.id, body.enrollment_id)
    assert_stream_visible(ctx, db, e.class_stream_id)
    stream = db.get(ClassStream, e.class_stream_id)
    grade = db.get(Grade, stream.grade_id)
    if grade.band != "EARLY_CHILDHOOD":
        raise ConflictError("Developmental ratings apply to early-childhood classes only.",
                            code="NOT_ECD")
    out = []
    for item in body.ratings:
        r = svc.upsert_rating(db, school_id=school.id, enrollment_id=body.enrollment_id,
                              term_id=body.term_id, domain_id=item.domain_id,
                              rating=item.rating, comment=item.comment,
                              actor_id=ctx.user.id, request=request)
        out.append({"id": str(r.id), "domain_id": str(r.domain_id), "rating": r.rating})
    db.commit()
    return {"items": out}


@router.get("/observations")
def list_observations(enrollment_id: uuid.UUID, include_superseded: bool = False,
                      ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                      db: Session = Depends(get_db)):
    school = get_school(db)
    e = _enrollment(db, school.id, enrollment_id)
    assert_student_visible(ctx, db, e.student_id)
    rows = svc.observations_for(db, enrollment_id, include_superseded)
    return {"items": [{"id": str(o.id), "logged_on": str(o.logged_on), "body": o.body,
                       "superseded": o.superseded_by is not None} for o in rows]}


@router.post("/observations", status_code=201)
def add_observation(body: ObservationIn, request: Request,
                    ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    e = _enrollment(db, school.id, body.enrollment_id)
    assert_stream_visible(ctx, db, e.class_stream_id)
    stream = db.get(ClassStream, e.class_stream_id)
    grade = db.get(Grade, stream.grade_id)
    if grade.band != "EARLY_CHILDHOOD":
        raise ConflictError("Observation logs apply to early-childhood classes only.",
                            code="NOT_ECD")
    log = svc.add_observation(db, school_id=school.id, enrollment_id=body.enrollment_id,
                              logged_on=body.logged_on or date.today(), body=body.body,
                              author_id=ctx.user.id, supersedes=body.supersedes,
                              request=request)
    db.commit()
    return {"id": str(log.id)}


@router.get("/competency-ratings")
def competency_ratings(enrollment_id: uuid.UUID, term_id: uuid.UUID,
                       ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                       db: Session = Depends(get_db)):
    school = get_school(db)
    e = _enrollment(db, school.id, enrollment_id)
    assert_student_visible(ctx, db, e.student_id)
    rows = svc.competency_ratings_for(db, enrollment_id, term_id)
    comps = {c.id: c for c in db.scalars(select(CoreCompetency).where(
        CoreCompetency.school_id == school.id)).all()}
    return {"items": [{"id": str(r.id), "competency_id": str(r.competency_id),
                       "competency": comps[r.competency_id].name if r.competency_id in comps else None,
                       "rating": r.rating, "comment": r.comment} for r in rows]}


@router.put("/competency-ratings")
def put_competency_ratings(body: CompetencyRatingIn, request: Request,
                           ctx: AuthContext = Depends(require(rbac.ENTER_MARKS)),
                           db: Session = Depends(get_db)):
    school = get_school(db)
    e = _enrollment(db, school.id, body.enrollment_id)
    assert_stream_visible(ctx, db, e.class_stream_id)
    out = []
    for item in body.ratings:
        r = svc.upsert_competency_rating(db, school_id=school.id,
                                         enrollment_id=body.enrollment_id,
                                         term_id=body.term_id,
                                         competency_id=item.competency_id,
                                         rating=item.rating, comment=item.comment,
                                         actor_id=ctx.user.id, request=request)
        out.append({"id": str(r.id), "rating": r.rating})
    db.commit()
    return {"items": out}
