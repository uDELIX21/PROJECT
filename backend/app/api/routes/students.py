"""Student registry endpoints (scoped: REQ-PRV-02)."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import (AuthContext, assert_student_visible, current_user, get_school,
                          require, student_scope)
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.models.core import Enrollment, ParentStudentRelationship
from app.schemas import common
from app.schemas.requests import StudentCreateIn, StudentPatchIn, StudentStatusIn
from app.services import students as svc

router = APIRouter(prefix="/students", tags=["students"])


@router.get("")
def list_students(q: str | None = Query(default=None, max_length=80),
                  status: str | None = None, gender: str | None = None,
                  class_stream_id: uuid.UUID | None = None,
                  grade_id: uuid.UUID | None = None,
                  limit: int = Query(default=20, ge=1, le=100),
                  offset: int = Query(default=0, ge=0),
                  ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    scope = student_scope(ctx, db)
    if scope is not None and not scope:
        return {"items": [], "total": 0, "limit": limit, "offset": offset}
    rows, total = svc.list_students(db, school.id, q=q, status=status, gender=gender,
                                    class_stream_id=class_stream_id, grade_id=grade_id,
                                    limit=limit, offset=offset, scope=scope)
    return {"items": [common.student(s) for s in rows], "total": int(total),
            "limit": limit, "offset": offset}


@router.post("", status_code=201)
def create_student(body: StudentCreateIn, request: Request,
                   ctx: AuthContext = Depends(require(rbac.EDIT_STUDENT)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    student = svc.create_student(db, school_id=school.id, actor_id=ctx.user.id,
                                 request=request, **body.model_dump())
    db.commit()
    return common.student(student, detail=True)


@router.get("/{student_id}")
def get_student(student_id: uuid.UUID, ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    assert_student_visible(ctx, db, student_id)
    student = svc.get_student(db, school.id, student_id)
    return common.student(student, detail=True)


@router.patch("/{student_id}")
def patch_student(student_id: uuid.UUID, body: StudentPatchIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.EDIT_STUDENT)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    student = svc.get_student(db, school.id, student_id)
    svc.update_biodata(db, student, actor_id=ctx.user.id, request=request,
                       **body.model_dump(exclude_none=True))
    db.commit()
    return common.student(student, detail=True)


@router.post("/{student_id}/status")
def change_status(student_id: uuid.UUID, body: StudentStatusIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_ENROLLMENT)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    student = svc.get_student(db, school.id, student_id)
    svc.change_status(db, student, body.status, actor_id=ctx.user.id,
                      reason=body.reason, request=request)
    db.commit()
    return common.student(student, detail=True)


@router.get("/{student_id}/enrollments")
def student_enrollments(student_id: uuid.UUID,
                        ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                        db: Session = Depends(get_db)):
    school = get_school(db)
    assert_student_visible(ctx, db, student_id)
    svc.get_student(db, school.id, student_id)
    rows = db.scalars(select(Enrollment)
                      .where(Enrollment.student_id == student_id,
                             Enrollment.school_id == school.id)
                      .order_by(Enrollment.created_at.desc())).all()
    return {"items": [common.enrollment(e) for e in rows]}


@router.get("/{student_id}/guardians")
def student_guardians(student_id: uuid.UUID,
                      ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                      db: Session = Depends(get_db)):
    school = get_school(db)
    assert_student_visible(ctx, db, student_id)
    svc.get_student(db, school.id, student_id)
    rels = db.scalars(select(ParentStudentRelationship).where(
        ParentStudentRelationship.student_id == student_id,
        ParentStudentRelationship.school_id == school.id)).all()
    return {"items": [{**common.relationship(r), "parent": common.guardian(r.parent)}
                      for r in rels]}
