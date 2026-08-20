"""Teacher registry + assignment endpoints (REQ-TCH-*)."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.db import get_db
from app.models.core import TeacherAssignment
from app.schemas import common
from app.schemas.requests import AssignmentCreateIn, TeacherCreateIn
from app.services import teachers as svc

router = APIRouter(prefix="/teachers", tags=["teachers"])


@router.get("")
def list_teachers(q: str | None = Query(default=None, max_length=80),
                  limit: int = Query(default=20, ge=1, le=100),
                  offset: int = Query(default=0, ge=0),
                  ctx: AuthContext = Depends(require(rbac.VIEW_TEACHER)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    from app.models.core import Teacher
    from sqlalchemy import func, or_
    stmt = select(Teacher).where(Teacher.school_id == school.id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Teacher.surname).like(like),
                              func.lower(Teacher.other_names).like(like)))
    rows = db.scalars(stmt.order_by(Teacher.surname).limit(limit).offset(offset)).all()
    return {"items": [common.teacher(t) for t in rows], "limit": limit, "offset": offset}


@router.post("", status_code=201)
def create_teacher(body: TeacherCreateIn, request: Request,
                   ctx: AuthContext = Depends(require(rbac.EDIT_TEACHER)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    t = svc.create_teacher(db, school_id=school.id, actor_id=ctx.user.id,
                           request=request, **body.model_dump(exclude_none=True))
    db.commit()
    return common.teacher(t)


@router.get("/{teacher_id}")
def get_teacher(teacher_id: uuid.UUID,
                ctx: AuthContext = Depends(require(rbac.VIEW_TEACHER)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    t = svc.get_teacher(db, school.id, teacher_id)
    return common.teacher(t)


@router.get("/{teacher_id}/assignments")
def teacher_assignments(teacher_id: uuid.UUID,
                        ctx: AuthContext = Depends(require(rbac.VIEW_TEACHER)),
                        db: Session = Depends(get_db)):
    school = get_school(db)
    svc.get_teacher(db, school.id, teacher_id)
    rows = db.scalars(select(TeacherAssignment).where(
        TeacherAssignment.teacher_id == teacher_id,
        TeacherAssignment.school_id == school.id)).all()
    return {"items": [{"id": str(a.id), "academic_year_id": str(a.academic_year_id),
                       "class_stream_id": str(a.class_stream_id),
                       "subject_id": str(a.subject_id) if a.subject_id else None,
                       "role": a.role, "is_active": a.is_active} for a in rows]}


@router.post("/assignments", status_code=201)
def create_assignment(body: AssignmentCreateIn, request: Request,
                      ctx: AuthContext = Depends(require(rbac.MANAGE_ASSIGNMENTS)),
                      db: Session = Depends(get_db)):
    school = get_school(db)
    a = svc.create_assignment(db, school_id=school.id, actor_id=ctx.user.id,
                              request=request, **body.model_dump(exclude_none=True))
    db.commit()
    return {"id": str(a.id), "teacher_id": str(a.teacher_id),
            "class_stream_id": str(a.class_stream_id), "role": a.role}
