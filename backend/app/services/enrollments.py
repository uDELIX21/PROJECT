"""Enrollment service: formal enrollment records & lifecycle coupling (BR-S02/03)."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.core import AcademicYear, ClassStream, Enrollment, Student
from app.services import lifecycle

ENROLLABLE_STATUSES = {"ADMITTED", "ENROLLED", "ACTIVE", "PROMOTED", "REPEATED"}


def get_stream(db: Session, school_id: uuid.UUID, stream_id: uuid.UUID) -> ClassStream:
    stream = db.get(ClassStream, stream_id)
    if stream is None or stream.school_id != school_id:
        raise NotFoundError("Class stream not found.")
    return stream


def active_enrollment(db: Session, student_id: uuid.UUID,
                      academic_year_id: uuid.UUID) -> Enrollment | None:
    return db.scalar(select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.academic_year_id == academic_year_id,
        Enrollment.status == "ACTIVE"))


def create_enrollment(db: Session, *, school_id: uuid.UUID, student_id: uuid.UUID,
                      class_stream_id: uuid.UUID, academic_year_id: uuid.UUID | None = None,
                      is_repeat: bool = False, started_on: date | None = None,
                      actor_id: uuid.UUID | None = None,
                      request: Request | None = None) -> Enrollment:
    student = db.get(Student, student_id)
    if student is None or student.school_id != school_id:
        raise NotFoundError("Student not found.")
    stream = get_stream(db, school_id, class_stream_id)
    year_id = academic_year_id or stream.academic_year_id
    year = db.get(AcademicYear, year_id)
    if year is None or year.school_id != school_id or str(year.id) != str(stream.academic_year_id):
        raise ConflictError("Class stream does not belong to the given academic year.",
                            code="STREAM_YEAR_MISMATCH")
    if student.status not in ENROLLABLE_STATUSES:
        raise ConflictError(
            f"Student status {student.status} cannot be enrolled (must be admitted first).",
            code="STUDENT_NOT_ADMITTED")
    existing = active_enrollment(db, student_id, year_id)
    if existing is not None:
        if existing.class_stream_id == class_stream_id and not is_repeat:
            raise ConflictError("Student already has an active enrollment in this year.",
                                code="DUPLICATE_ENROLLMENT")
        raise ConflictError("Student already has an active enrollment in this academic year. "
                            "Withdraw or transfer it first.", code="DUPLICATE_ENROLLMENT")
    enrollment = Enrollment(id=uuid7(), school_id=school_id, student_id=student_id,
                            academic_year_id=year_id, class_stream_id=class_stream_id,
                            status="ACTIVE", started_on=started_on or year.starts_on,
                            is_repeat=is_repeat, created_by=actor_id)
    db.add(enrollment)
    previous_status = student.status
    if student.status in ("ADMITTED", "PROMOTED", "REPEATED"):
        lifecycle.assert_transition(student.status, "ENROLLED") if student.status == "ADMITTED" \
            else lifecycle.assert_transition(student.status, "ACTIVE")
        student.status = "ENROLLED" if student.status == "ADMITTED" else "ACTIVE"
    elif student.status == "ENROLLED":
        student.status = "ACTIVE"
    if student.status != previous_status:
        audit(db, actor_id=actor_id, action="student.status_changed", entity_type="student",
              entity_id=student.id, previous={"status": previous_status},
              new={"status": student.status}, reason="enrollment created", request=request)
    audit(db, actor_id=actor_id, action="enrollment.created", entity_type="enrollment",
          entity_id=enrollment.id,
          new={"student_id": str(student_id), "class_stream_id": str(class_stream_id),
               "academic_year_id": str(year_id), "is_repeat": is_repeat},
          request=request)
    db.flush()
    return enrollment


def end_enrollment(db: Session, enrollment: Enrollment, *, outcome: str,
                   actor_id: uuid.UUID | None, reason: str | None = None,
                   request: Request | None = None) -> Enrollment:
    """outcome: WITHDRAWN | TRANSFERRED | COMPLETED."""
    if enrollment.status != "ACTIVE":
        raise ConflictError("Only active enrollments can be ended.", code="NOT_ACTIVE")
    enrollment.status = outcome
    enrollment.ended_on = date.today()
    student = db.get(Student, enrollment.student_id)
    if student is not None and outcome in ("WITHDRAWN", "TRANSFERRED"):
        previous = student.status
        lifecycle.assert_transition(previous, outcome)
        student.status = outcome
        audit(db, actor_id=actor_id, action="student.status_changed", entity_type="student",
              entity_id=student.id, previous={"status": previous},
              new={"status": outcome}, reason=reason, request=request)
    audit(db, actor_id=actor_id, action=f"enrollment.{outcome.lower()}",
          entity_type="enrollment", entity_id=enrollment.id,
          previous={"status": "ACTIVE"}, new={"status": outcome}, reason=reason,
          request=request)
    db.flush()
    return enrollment


def get_enrollment(db: Session, school_id: uuid.UUID, enrollment_id: uuid.UUID) -> Enrollment:
    e = db.get(Enrollment, enrollment_id)
    if e is None or e.school_id != school_id:
        raise NotFoundError("Enrollment not found.")
    return e
