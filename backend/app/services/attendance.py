"""Attendance service: sheets, summaries, compliance (REQ-ATT-*, BR-T)."""
import uuid
from datetime import date, timedelta

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, LockedError, NotFoundError
from app.core.ids import uuid7
from app.models.academic import AttendanceRecord, AttendanceSheet
from app.models.base import utcnow
from app.models.core import ClassStream, Enrollment, Student, Teacher, TeacherAssignment, Term

# default weights (BR-T02; configurable via school settings later)
DEFAULT_WEIGHTS = {"PRESENT": 1.0, "LATE": 1.0, "LEFT_EARLY": 1.0,
                   "ABSENT": 0.0, "EXCUSED": 0.0}
VALID_STATUSES = set(DEFAULT_WEIGHTS)


def get_sheet(db: Session, *, stream_id: uuid.UUID, sheet_date: date) -> AttendanceSheet | None:
    return db.scalar(select(AttendanceSheet).where(
        AttendanceSheet.class_stream_id == stream_id,
        AttendanceSheet.sheet_date == sheet_date))


def upsert_sheet(db: Session, *, school_id: uuid.UUID, stream_id: uuid.UUID,
                 term_id: uuid.UUID, sheet_date: date,
                 records: list[dict], actor_id: uuid.UUID,
                 request: Request | None = None) -> AttendanceSheet:
    term = db.get(Term, term_id)
    if term is None or term.school_id != school_id:
        raise NotFoundError("Term not found.")
    if term.status != "ACTIVE":
        raise LockedError("Attendance can only be recorded for the active term (BR-T04).",
                          code="TERM_CLOSED")
    if not (term.starts_on <= sheet_date <= term.ends_on):
        raise ConflictError("Date falls outside the term range.", code="DATE_OUT_OF_TERM")

    sheet = get_sheet(db, stream_id=stream_id, sheet_date=sheet_date)
    created = sheet is None
    if created:
        sheet = AttendanceSheet(id=uuid7(), school_id=school_id, class_stream_id=stream_id,
                                term_id=term_id, sheet_date=sheet_date, taken_by=actor_id)
        db.add(sheet)
        db.flush()
    elif sheet.status == "SUBMITTED":
        raise LockedError("Sheet already submitted; contact an administrator to amend.",
                          code="SHEET_SUBMITTED")

    enrollment_ids = {e.id for e in db.scalars(select(Enrollment).where(
        Enrollment.class_stream_id == stream_id,
        Enrollment.academic_year_id == term.academic_year_id,
        Enrollment.status == "ACTIVE")).all()}
    for r in records:
        status = r["status"]
        if status not in VALID_STATUSES:
            raise ConflictError(f"Invalid attendance status '{status}'.",
                                code="STATUS_INVALID")
        if r["enrollment_id"] not in enrollment_ids:
            raise ConflictError("Enrollment not active in this class.", code="ENROLLMENT_INVALID")
        rec = db.scalar(select(AttendanceRecord).where(
            AttendanceRecord.sheet_id == sheet.id,
            AttendanceRecord.enrollment_id == r["enrollment_id"]))
        if rec is None:
            rec = AttendanceRecord(id=uuid7(), school_id=school_id, sheet_id=sheet.id,
                                   enrollment_id=r["enrollment_id"], status=status,
                                   note=r.get("note"))
            db.add(rec)
        else:
            rec.status = status
            rec.note = r.get("note")
    sheet.taken_by = actor_id
    audit(db, actor_id=actor_id, action="attendance.sheet_saved",
          entity_type="attendance_sheet", entity_id=sheet.id,
          new={"date": str(sheet_date), "records": len(records)}, request=request)
    db.flush()
    return sheet


def submit_sheet(db: Session, sheet: AttendanceSheet, *, actor_id: uuid.UUID,
                 request: Request | None = None) -> AttendanceSheet:
    if sheet.status != "DRAFT":
        raise ConflictError("Sheet already submitted.", code="SHEET_SUBMITTED")
    sheet.status = "SUBMITTED"
    sheet.submitted_at = utcnow()
    audit(db, actor_id=actor_id, action="attendance.sheet_submitted",
          entity_type="attendance_sheet", entity_id=sheet.id, request=request)
    db.flush()
    return sheet


def sheet_records(db: Session, sheet_id: uuid.UUID) -> list[AttendanceRecord]:
    return list(db.scalars(select(AttendanceRecord).where(
        AttendanceRecord.sheet_id == sheet_id)).all())


def student_summary(db: Session, enrollment_id: uuid.UUID, *,
                    weights: dict | None = None) -> dict:
    """Weighted attendance percentage for one enrollment (BR-T03)."""
    w = weights or DEFAULT_WEIGHTS
    rows = db.execute(
        select(AttendanceRecord.status, func.count())
        .join(AttendanceSheet, AttendanceRecord.sheet_id == AttendanceSheet.id)
        .where(AttendanceRecord.enrollment_id == enrollment_id)
        .group_by(AttendanceRecord.status)).all()
    counts = {status: n for status, n in rows}
    days = sum(counts.values())
    earned = sum(w.get(s, 0.0) * n for s, n in counts.items())
    pct = round(earned / days * 100, 1) if days else None
    return {"days_recorded": days, "counts": counts, "percentage": pct}


def class_summary(db: Session, stream_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    enrollments = db.execute(select(Enrollment, Student).join(
        Student, Enrollment.student_id == Student.id).where(
        Enrollment.class_stream_id == stream_id,
        Enrollment.status == "ACTIVE")).all()
    items = []
    for enrollment, student in enrollments:
        s = student_summary(db, enrollment.id)
        items.append({"student_id": str(student.id), "student_name": student.full_name,
                      "admission_code": student.admission_code, **s})
    items.sort(key=lambda i: (i["percentage"] is None, i["percentage"] or 0))
    return {"items": items}


def compliance(db: Session, *, school_id: uuid.UUID, term_id: uuid.UUID) -> list[dict]:
    """Roll-call compliance: submitted sheets vs expected school days (BR-T05).

    Expected days = weekdays within the term range (weekends excluded; holiday
    calendar is a school setting — refinement tracked for later phases).
    """
    term = db.get(Term, term_id)
    if term is None or term.school_id != school_id:
        raise NotFoundError("Term not found.")
    expected = 0
    d = term.starts_on
    while d <= term.ends_on:
        if d.weekday() < 5:
            expected += 1
        d += timedelta(days=1)
    streams = db.scalars(select(ClassStream).where(
        ClassStream.academic_year_id == term.academic_year_id,
        ClassStream.school_id == school_id)).all()
    out = []
    for stream in streams:
        submitted = db.scalar(select(func.count()).select_from(AttendanceSheet).where(
            AttendanceSheet.class_stream_id == stream.id,
            AttendanceSheet.term_id == term_id,
            AttendanceSheet.status == "SUBMITTED")) or 0
        form_teacher = db.scalar(
            select(Teacher).join(TeacherAssignment,
                                 TeacherAssignment.teacher_id == Teacher.id).where(
                TeacherAssignment.class_stream_id == stream.id,
                TeacherAssignment.role == "FORM_TEACHER",
                TeacherAssignment.is_active.is_(True)).limit(1))
        out.append({"class_stream_id": str(stream.id), "class_name": stream.name,
                    "form_teacher": form_teacher.full_name if form_teacher else None,
                    "expected_days": expected, "sheets_submitted": int(submitted),
                    "compliance_pct": round(int(submitted) / expected * 100, 1) if expected else None})
    return out
