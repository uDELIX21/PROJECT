"""Offline sync engine — applies queued teacher mutations with the exact same
validation & scoping as the direct endpoints (REQ-OFF-03, design §09)."""
import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext
from app.core.errors import ApiError, ConflictError, ForbiddenError, NotFoundError
from app.core.ids import uuid7
from app.models.academic import Assessment, AssessmentScore, AttendanceRecord, AttendanceSheet
from app.models.core import Enrollment, Term
from app.models.sync import SyncMutation
from app.services import assessment as assess_svc
from app.services import attendance as att_svc


def _apply_score(db: Session, ctx: AuthContext, payload: dict, base_version: int | None) -> dict:
    assessment_id = _as_uuid(payload["assessment_id"])
    enrollment_id = _as_uuid(payload["enrollment_id"])
    sheet = db.get(Assessment, assessment_id)
    if sheet is None or sheet.school_id != _ctx_school(ctx, db):
        raise NotFoundError("Mark sheet not found.")
    # assignment scoping — identical to the direct endpoint (REQ-MRK-01)
    _assert_sheet_scope(db, ctx, sheet)
    term = db.get(Term, sheet.term_id)
    assess_svc.assert_term_open(term)
    if sheet.status != "DRAFT":
        raise ConflictError("Sheet is no longer editable.", code="MARKS_LOCKED")
    # optimistic concurrency: client's base_version vs current sheet version
    if base_version is not None and int(base_version) != sheet.version:
        current = db.scalar(select(AssessmentScore).where(
            AssessmentScore.assessment_id == sheet.id,
            AssessmentScore.enrollment_id == enrollment_id))
        raise ConflictError(
            "Sheet changed since you last synced.", code="VERSION_CONFLICT",
            details={"server_version": sheet.version,
                     "server_value": float(current.raw_score)
                     if current and current.raw_score is not None else None})
    raw = payload.get("raw_score")
    if raw is not None:
        raw = float(raw)
        if raw < 0 or raw > float(sheet.component.max_score):
            raise ConflictError("Score out of range.", code="SCORE_OUT_OF_RANGE")
    score = db.scalar(select(AssessmentScore).where(
        AssessmentScore.assessment_id == sheet.id,
        AssessmentScore.enrollment_id == enrollment_id))
    if score is None:
        score = AssessmentScore(id=uuid7(), school_id=sheet.school_id,
                                assessment_id=sheet.id, enrollment_id=enrollment_id,
                                raw_score=raw, is_absent=bool(payload.get("is_absent", False)),
                                note=payload.get("note"))
        db.add(score)
    else:
        score.raw_score = raw
        score.is_absent = bool(payload.get("is_absent", False))
        score.note = payload.get("note")
        score.version += 1
    sheet.version += 1
    db.flush()
    return {"server_version": sheet.version, "applied_value": raw}


def _apply_attendance(db: Session, ctx: AuthContext, payload: dict, base_version: int | None) -> dict:
    stream_id = _as_uuid(payload["class_stream_id"])
    term_id = _as_uuid(payload["term_id"])
    enrollment_id = _as_uuid(payload["enrollment_id"])
    sheet_date = date.fromisoformat(payload["sheet_date"])
    status = payload["status"]
    _assert_stream_scope(db, ctx, stream_id)
    term = db.get(Term, term_id)
    if term is None:
        raise NotFoundError("Term not found.")
    assess_svc.assert_term_open(term)
    if not (term.starts_on <= sheet_date <= term.ends_on):
        raise ConflictError("Date outside term.", code="DATE_OUT_OF_TERM")
    sheet = att_svc.get_sheet(db, stream_id=stream_id, sheet_date=sheet_date)
    if sheet is None:
        sheet = AttendanceSheet(id=uuid7(), school_id=_ctx_school(ctx, db),
                                class_stream_id=stream_id, term_id=term_id,
                                sheet_date=sheet_date, taken_by=ctx.user.id)
        db.add(sheet)
        db.flush()
    if sheet.status == "SUBMITTED":
        raise ConflictError("Sheet already submitted.", code="SHEET_SUBMITTED")
    if base_version is not None and int(base_version) != _sheet_version(db, sheet):
        raise ConflictError("Attendance sheet changed since you last synced.",
                            code="VERSION_CONFLICT",
                            details={"server_version": _sheet_version(db, sheet)})
    rec = db.scalar(select(AttendanceRecord).where(
        AttendanceRecord.sheet_id == sheet.id,
        AttendanceRecord.enrollment_id == enrollment_id))
    if rec is None:
        rec = AttendanceRecord(id=uuid7(), school_id=sheet.school_id, sheet_id=sheet.id,
                               enrollment_id=enrollment_id, status=status,
                               note=payload.get("note"))
        db.add(rec)
    else:
        rec.status = status
        rec.note = payload.get("note")
    sheet.taken_by = ctx.user.id
    db.flush()
    return {"sheet_id": str(sheet.id)}


def _sheet_version(db: Session, sheet: AttendanceSheet) -> int:
    """Attendance sheets use record count as a coarse version token."""
    return len(att_svc.sheet_records(db, sheet.id))


def _ctx_school(ctx: AuthContext, db: Session) -> uuid.UUID:
    from app.api.deps import get_school
    return get_school(db).id


def _assert_sheet_scope(db: Session, ctx: AuthContext, sheet: Assessment) -> None:
    if ctx.user.teacher_id is None:
        return  # unrestricted staff
    from app.models.core import TeacherAssignment
    a = db.scalar(select(TeacherAssignment).where(
        TeacherAssignment.teacher_id == ctx.user.teacher_id,
        TeacherAssignment.class_stream_id == sheet.class_stream_id,
        TeacherAssignment.is_active.is_(True)))
    if a is None:
        raise ForbiddenError("You are not assigned to this class.",
                             code="NOT_ASSIGNED_CLASS")
    if a.role != "FORM_TEACHER" and a.subject_id != sheet.subject_id:
        raise ForbiddenError("You are not assigned to this subject in this class.",
                             code="NOT_ASSIGNED_SUBJECT")


def _assert_stream_scope(db: Session, ctx: AuthContext, stream_id: uuid.UUID) -> None:
    if ctx.user.teacher_id is None:
        return
    from app.models.core import TeacherAssignment
    a = db.scalar(select(TeacherAssignment).where(
        TeacherAssignment.teacher_id == ctx.user.teacher_id,
        TeacherAssignment.class_stream_id == stream_id,
        TeacherAssignment.is_active.is_(True)))
    if a is None:
        raise ForbiddenError("You are not assigned to this class.",
                             code="NOT_ASSIGNED_CLASS")


HANDLERS = {
    "ASSESSMENT_SCORE": _apply_score,
    "ATTENDANCE_RECORD": _apply_attendance,
}


def _as_uuid(value) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def apply_batch(db: Session, ctx: AuthContext, mutations: list[dict]) -> list[dict]:
    """Process a batch; each mutation is independent — one failure never blocks
    the rest, and every result is recorded for replay idempotency."""
    school_id = _ctx_school(ctx, db)
    results = []
    for m in mutations:
        client_id = _as_uuid(m["client_mutation_id"])
        existing = db.scalar(select(SyncMutation).where(
            SyncMutation.client_mutation_id == client_id))
        if existing is not None:
            results.append({"client_mutation_id": m["client_mutation_id"],
                            "status": existing.status,
                            "result": existing.response or {}, "replayed": True})
            continue
        # unknown types are rejected up front (the ledger CHECK cannot store them)
        if m["entity_type"] not in HANDLERS:
            results.append({"client_mutation_id": m["client_mutation_id"],
                            "status": "REJECTED", "replayed": False,
                            "result": {"code": "MUTATION_TYPE_UNKNOWN",
                                       "message": f"Unknown mutation type {m['entity_type']}."}})
            continue
        row = SyncMutation(id=uuid7(), school_id=school_id, client_mutation_id=client_id,
                           user_id=ctx.user.id, entity_type=m["entity_type"],
                           entity_ref=m.get("entity_ref", ""),
                           base_version=m.get("base_version"),
                           payload=m.get("payload", {}), status="REJECTED")
        db.add(row)
        db.flush()
        handler = HANDLERS.get(m["entity_type"])
        try:
            result = handler(db, ctx, m.get("payload", {}), m.get("base_version"))
            row.status = "APPLIED"
            row.response = result
            results.append({"client_mutation_id": m["client_mutation_id"],
                            "status": "APPLIED", "result": result, "replayed": False})
        except ApiError as e:
            row.status = "CONFLICT" if e.code == "VERSION_CONFLICT" else "REJECTED"
            row.response = {"code": e.code, "message": e.message, "details": e.details}
            results.append({"client_mutation_id": m["client_mutation_id"],
                            "status": row.status, "result": row.response, "replayed": False})
        db.flush()
    return results
