"""School profile, academic calendar (years/terms), and settings keys."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.audit import audit
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.models.core import AcademicYear, SchoolSetting, Term
from app.schemas import common
from app.schemas.requests import (SchoolPatchIn, TermCreateIn, TermReopenIn, YearCreateIn)
from app.services import calendar

router = APIRouter(tags=["settings"])


# --- school profile -------------------------------------------------------

@router.get("/school")
def school_profile(ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                   db: Session = Depends(get_db)):
    s = get_school(db)
    return {"id": str(s.id), "name": s.name, "short_name": s.short_name, "motto": s.motto,
            "location": s.location, "ghana_digital_address": s.ghana_digital_address,
            "phone": s.phone, "email": s.email, "timezone": s.timezone}


@router.patch("/school")
def patch_school(body: SchoolPatchIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    previous, new = {}, {}
    for key, value in body.model_dump(exclude_unset=True).items():
        old = getattr(school, key)
        if old != value:
            previous[key] = str(old) if old is not None else None
            new[key] = str(value) if value is not None else None
            setattr(school, key, value)
    if new:
        audit(db, actor_id=ctx.user.id, action="school.updated", entity_type="school",
              entity_id=school.id, previous=previous, new=new, request=request)
    db.commit()
    return {"ok": True}


@router.get("/settings")
def settings_list(ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(SchoolSetting).where(SchoolSetting.school_id == school.id)).all()
    return {"items": [{"key": r.key, "value": r.value, "description": r.description}
                      for r in rows]}


# --- academic years -------------------------------------------------------

@router.get("/academic-years")
def list_years(ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(AcademicYear).where(AcademicYear.school_id == school.id)
                      .order_by(AcademicYear.starts_on.desc())).all()
    return {"items": [common.year(y) for y in rows]}


@router.post("/academic-years", status_code=201)
def create_year(body: YearCreateIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    year = calendar.create_year(db, school_id=school.id, actor_id=ctx.user.id,
                                request=request, **body.model_dump())
    db.commit()
    return common.year(year)


@router.post("/academic-years/{year_id}/activate")
def activate_year(year_id: uuid.UUID, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    year = db.get(AcademicYear, year_id)
    if year is None or year.school_id != school.id:
        raise NotFoundError("Academic year not found.")
    calendar.activate_year(db, year, actor_id=ctx.user.id, request=request)
    db.commit()
    return common.year(year)


@router.post("/academic-years/{year_id}/terms", status_code=201)
def create_term(year_id: uuid.UUID, body: TermCreateIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    term = calendar.create_term(db, school_id=school.id, academic_year_id=year_id,
                                actor_id=ctx.user.id, request=request, **body.model_dump())
    db.commit()
    return common.term(term)


@router.get("/academic-years/{year_id}/terms")
def list_terms(year_id: uuid.UUID, ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(Term).where(Term.academic_year_id == year_id,
                                         Term.school_id == school.id)
                      .order_by(Term.starts_on)).all()
    return {"items": [common.term(t) for t in rows]}


# --- terms ----------------------------------------------------------------

def _term(db: Session, school_id: uuid.UUID, term_id: uuid.UUID) -> Term:
    t = db.get(Term, term_id)
    if t is None or t.school_id != school_id:
        raise NotFoundError("Term not found.")
    return t


@router.post("/terms/{term_id}/activate")
def activate_term(term_id: uuid.UUID, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    term = calendar.activate_term(db, _term(db, school.id, term_id),
                                  actor_id=ctx.user.id, request=request)
    db.commit()
    return common.term(term)


@router.post("/terms/{term_id}/close")
def close_term(term_id: uuid.UUID, request: Request,
               ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    term = calendar.close_term(db, _term(db, school.id, term_id),
                               actor_id=ctx.user.id, request=request)
    db.commit()
    return common.term(term)


@router.post("/terms/{term_id}/reopen")
def reopen_term(term_id: uuid.UUID, body: TermReopenIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.MANAGE_SETTINGS)),
                db: Session = Depends(get_db)):
    """Authorized reopening only — reason mandatory, action audited (BR-A02)."""
    school = get_school(db)
    term = calendar.reopen_term(db, _term(db, school.id, term_id), actor_id=ctx.user.id,
                                reason=body.reason, request=request)
    db.commit()
    return common.term(term)
