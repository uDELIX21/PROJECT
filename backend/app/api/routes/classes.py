"""Grades, class streams, subjects, rosters (REQ-PROF-02/03)."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, assert_stream_visible, get_school, require
from app.core.db import get_db
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.core import ClassStream, Enrollment, Grade, GradeSubject, Student, Subject
from app.schemas import common
from app.schemas.requests import GradeCreateIn, StreamCreateIn, SubjectCreateIn

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("/grades")
def list_grades(ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(Grade).where(Grade.school_id == school.id)
                      .order_by(Grade.ordinal)).all()
    return {"items": [common.grade(g) for g in rows]}


@router.post("/grades", status_code=201)
def create_grade(body: GradeCreateIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.MANAGE_CLASSES)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    dup = db.scalar(select(Grade).where(Grade.school_id == school.id, Grade.code == body.code))
    if dup is not None:
        raise ConflictError("Grade code already exists.", code="GRADE_EXISTS")
    grade = Grade(id=uuid7(), school_id=school.id, code=body.code, name=body.name,
                  ordinal=body.ordinal, band=body.band, created_by=ctx.user.id)
    db.add(grade)
    db.commit()
    return common.grade(grade)


@router.get("/streams")
def list_streams(academic_year_id: uuid.UUID | None = None,
                 grade_id: uuid.UUID | None = None,
                 ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(ClassStream).where(ClassStream.school_id == school.id)
    if academic_year_id:
        stmt = stmt.where(ClassStream.academic_year_id == academic_year_id)
    if grade_id:
        stmt = stmt.where(ClassStream.grade_id == grade_id)
    rows = db.scalars(stmt.order_by(ClassStream.name)).all()
    return {"items": [common.stream(s) for s in rows]}


@router.post("/streams", status_code=201)
def create_stream(body: StreamCreateIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_CLASSES)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    grade = db.get(Grade, body.grade_id)
    if grade is None or grade.school_id != school.id:
        raise NotFoundError("Grade not found.")
    name = body.name or f"{grade.name} {body.section_label}"
    stream = ClassStream(id=uuid7(), school_id=school.id, grade_id=body.grade_id,
                         academic_year_id=body.academic_year_id, name=name,
                         section_label=body.section_label, capacity=body.capacity)
    db.add(stream)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise ConflictError("A stream with this section already exists for that grade/year.",
                            code="STREAM_EXISTS")
    return common.stream(stream)


@router.get("/streams/{stream_id}/roster")
def stream_roster(stream_id: uuid.UUID,
                  ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    assert_stream_visible(ctx, db, stream_id)  # teachers: assigned classes only (J8)
    stream = db.get(ClassStream, stream_id)
    if stream is None or stream.school_id != school.id:
        raise NotFoundError("Class stream not found.")
    rows = db.execute(
        select(Student, Enrollment)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .where(Enrollment.class_stream_id == stream_id, Enrollment.status == "ACTIVE")
        .order_by(Student.surname)).all()
    return {"stream": common.stream(stream),
            "items": [{**common.student(s), "enrollment": common.enrollment(e)}
                      for s, e in rows],
            "count": len(rows)}


@router.get("/subjects")
def list_subjects(ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(Subject).where(Subject.school_id == school.id,
                                            Subject.is_active.is_(True))
                      .order_by(Subject.name)).all()
    return {"items": [{"id": str(s.id), "code": s.code, "name": s.name} for s in rows]}


@router.post("/subjects", status_code=201)
def create_subject(body: SubjectCreateIn, request: Request,
                   ctx: AuthContext = Depends(require(rbac.MANAGE_CLASSES)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    dup = db.scalar(select(Subject).where(Subject.school_id == school.id,
                                          Subject.code == body.code))
    if dup is not None:
        raise ConflictError("Subject code already exists.", code="SUBJECT_EXISTS")
    subj = Subject(id=uuid7(), school_id=school.id, code=body.code, name=body.name)
    db.add(subj)
    db.commit()
    return {"id": str(subj.id), "code": subj.code, "name": subj.name}


@router.get("/grades/{grade_id}/subjects")
def grade_subjects(grade_id: uuid.UUID, ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    grade = db.get(Grade, grade_id)
    if grade is None or grade.school_id != school.id:
        raise NotFoundError("Grade not found.")
    rows = db.scalars(select(Subject).join(GradeSubject,
                                           GradeSubject.subject_id == Subject.id)
                      .where(GradeSubject.grade_id == grade_id)).all()
    return {"items": [{"id": str(s.id), "code": s.code, "name": s.name} for s in rows]}


@router.put("/grades/{grade_id}/subjects/{subject_id}", status_code=204)
def attach_subject(grade_id: uuid.UUID, subject_id: uuid.UUID, request: Request,
                   ctx: AuthContext = Depends(require(rbac.MANAGE_CLASSES)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    grade = db.get(Grade, grade_id)
    subj = db.get(Subject, subject_id)
    if grade is None or subj is None or grade.school_id != school.id or subj.school_id != school.id:
        raise NotFoundError("Grade or subject not found.")
    exists = db.scalar(select(GradeSubject).where(GradeSubject.grade_id == grade_id,
                                                  GradeSubject.subject_id == subject_id))
    if exists is None:
        db.add(GradeSubject(grade_id=grade_id, subject_id=subject_id))
        db.commit()
    return None
