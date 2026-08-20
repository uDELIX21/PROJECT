"""Student registry service (create/admit/edit/status/search)."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.config import get_settings
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.core import ClassStream, Enrollment, Student
from app.services import lifecycle, sequences


def _admission_prefix(db: Session, school_id: uuid.UUID) -> str:
    """Per-school configurable prefix (REQ-CFG-01); falls back to app default."""
    from app.models.core import SchoolSetting
    row = db.scalar(select(SchoolSetting).where(
        SchoolSetting.school_id == school_id,
        SchoolSetting.key == "admission_code_prefix"))
    if row is not None and isinstance(row.value, str) and row.value:
        return row.value
    return get_settings().admission_code_prefix


def _student_json(s: Student) -> dict:
    return {"admission_code": s.admission_code, "surname": s.surname,
            "other_names": s.other_names, "gender": s.gender,
            "date_of_birth": str(s.date_of_birth), "status": s.status}


def create_student(db: Session, *, school_id: uuid.UUID, surname: str, other_names: str,
                   gender: str, date_of_birth: date, actor_id: uuid.UUID | None = None,
                   admit: bool = False, request: Request | None = None) -> Student:
    code, _ = sequences.next_value(db, school_id, "ADMISSION_CODE",
                                   prefix=_admission_prefix(db, school_id))
    student = Student(id=uuid7(), school_id=school_id, admission_code=code,
                      surname=surname.strip(), other_names=other_names.strip(),
                      gender=gender, date_of_birth=date_of_birth,
                      status="ADMITTED" if admit else "APPLICANT",
                      admitted_on=date.today() if admit else None,
                      created_by=actor_id)
    db.add(student)
    db.flush()
    audit(db, actor_id=actor_id, action="student.created", entity_type="student",
          entity_id=student.id, new=_student_json(student), request=request)
    if admit:
        audit(db, actor_id=actor_id, action="student.admitted", entity_type="student",
              entity_id=student.id, new={"status": "ADMITTED"}, request=request)
    return student


def update_biodata(db: Session, student: Student, *, actor_id: uuid.UUID | None,
                   request: Request | None = None, **fields) -> Student:
    editable = {"surname", "other_names", "gender", "date_of_birth", "nationality",
                "religion", "medical_notes"}
    previous, new = {}, {}
    for key, value in fields.items():
        if key in editable and value is not None and getattr(student, key) != value:
            previous[key] = str(getattr(student, key))
            new[key] = str(value)
            setattr(student, key, value)
    if new:
        student.updated_by = actor_id
        audit(db, actor_id=actor_id, action="student.biodata_changed",
              entity_type="student", entity_id=student.id,
              previous=previous, new=new, request=request)
    return student


def change_status(db: Session, student: Student, target: str, *, actor_id: uuid.UUID | None,
                  reason: str | None = None, request: Request | None = None) -> Student:
    lifecycle.assert_transition(student.status, target)
    previous = student.status
    student.status = target
    student.updated_by = actor_id
    if target == "ADMITTED" and student.admitted_on is None:
        student.admitted_on = date.today()
    audit(db, actor_id=actor_id, action="student.status_changed", entity_type="student",
          entity_id=student.id, previous={"status": previous},
          new={"status": target}, reason=reason, request=request)
    return student


def get_student(db: Session, school_id: uuid.UUID, student_id: uuid.UUID) -> Student:
    student = db.get(Student, student_id)
    if student is None or student.school_id != school_id:
        raise NotFoundError("Student not found.")  # uniform 404: no scope leakage
    return student


def list_students(db: Session, school_id: uuid.UUID, *, q: str | None = None,
                  status: str | None = None, gender: str | None = None,
                  class_stream_id: uuid.UUID | None = None,
                  grade_id: uuid.UUID | None = None,
                  limit: int = 20, offset: int = 0,
                  scope: set | None = None) -> tuple[list[Student], int]:
    """scope=None ⇒ unrestricted; a set ⇒ filter INSIDE the query so scoped
    users' students never fall off a page (REQ-PRV-02)."""
    stmt = select(Student).where(Student.school_id == school_id)
    count_stmt = select(func.count()).select_from(Student).where(Student.school_id == school_id)
    if scope is not None:
        stmt = stmt.where(Student.id.in_(scope))
        count_stmt = count_stmt.where(Student.id.in_(scope))
    if q:
        like = f"%{q.lower()}%"
        filt = or_(func.lower(Student.surname).like(like),
                   func.lower(Student.other_names).like(like),
                   func.lower(Student.admission_code).like(like))
        stmt, count_stmt = stmt.where(filt), count_stmt.where(filt)
    if status:
        stmt, count_stmt = stmt.where(Student.status == status), count_stmt.where(Student.status == status)
    if gender:
        stmt, count_stmt = stmt.where(Student.gender == gender), count_stmt.where(Student.gender == gender)
    if class_stream_id or grade_id:
        enroll_join = (select(Enrollment.student_id)
                       .join(ClassStream, Enrollment.class_stream_id == ClassStream.id)
                       .where(Enrollment.status == "ACTIVE"))
        if class_stream_id:
            enroll_join = enroll_join.where(Enrollment.class_stream_id == class_stream_id)
        if grade_id:
            enroll_join = enroll_join.where(ClassStream.grade_id == grade_id)
        stmt = stmt.where(Student.id.in_(enroll_join))
        count_stmt = count_stmt.where(Student.id.in_(enroll_join))
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(stmt.order_by(Student.surname, Student.other_names)
                      .limit(limit).offset(offset)).all()
    return list(rows), int(total)
