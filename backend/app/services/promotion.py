"""End-of-year promotion workflow (REQ-STU-03/04, BR-S05/06)."""
import uuid

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.core import (AcademicYear, ClassStream, Enrollment, Grade,
                             PromotionBatch, PromotionDecision, Student)
from app.services import enrollments as enroll_svc


def preview(db: Session, school_id: uuid.UUID, from_year_id: uuid.UUID,
            to_year_id: uuid.UUID) -> list[dict]:
    rows = db.execute(
        select(Enrollment, Student, ClassStream, Grade)
        .join(Student, Enrollment.student_id == Student.id)
        .join(ClassStream, Enrollment.class_stream_id == ClassStream.id)
        .join(Grade, ClassStream.grade_id == Grade.id)
        .where(Enrollment.school_id == school_id,
               Enrollment.academic_year_id == from_year_id,
               Enrollment.status == "ACTIVE")
        .order_by(Grade.ordinal, ClassStream.name, Student.surname)).all()
    out = []
    for enrollment, student, stream, grade in rows:
        if grade.band == "JHS" and grade.code == "JHS3":
            decision = "GRADUATE"
        else:
            decision = "PROMOTE"
        out.append({
            "student_id": str(student.id),
            "student_name": student.full_name,
            "admission_code": student.admission_code,
            "from_stream": stream.name,
            "grade_code": grade.code,
            "suggested_decision": decision,
            "enrollment_id": str(enrollment.id),
        })
    return out


def _next_stream(db: Session, school_id: uuid.UUID, mapping: dict[str, str],
                 grade: Grade, to_year_id: uuid.UUID) -> ClassStream | None:
    mapped = mapping.get(str(grade.id))
    if mapped:
        stream = db.get(ClassStream, uuid.UUID(mapped))
        if stream is None or stream.school_id != school_id \
                or str(stream.academic_year_id) != str(to_year_id):
            raise NotFoundError(f"Mapped target stream {mapped} not found in target year.")
        return stream
    # automatic: next ordinal grade, same section label
    next_grade = db.scalar(select(Grade).where(Grade.school_id == school_id,
                                               Grade.ordinal == grade.ordinal + 1))
    if next_grade is None:
        return None
    return db.scalar(select(ClassStream).where(
        ClassStream.school_id == school_id,
        ClassStream.academic_year_id == to_year_id,
        ClassStream.grade_id == next_grade.id,
        ClassStream.section_label == "A"))


def apply_batch(db: Session, *, school_id: uuid.UUID, from_year_id: uuid.UUID,
                to_year_id: uuid.UUID, decisions: list[dict],
                stream_mapping: dict[str, str] | None = None,
                actor_id: uuid.UUID | None = None,
                request: Request | None = None) -> PromotionBatch:
    from_year = db.get(AcademicYear, from_year_id)
    to_year = db.get(AcademicYear, to_year_id)
    if from_year is None or to_year is None or from_year.school_id != school_id \
            or to_year.school_id != school_id:
        raise NotFoundError("Academic year not found.")
    if to_year.starts_on <= from_year.ends_on:
        raise ConflictError("Target year must start after the source year ends.",
                            code="YEAR_ORDER")
    existing = db.scalar(select(PromotionBatch).where(
        PromotionBatch.from_academic_year_id == from_year_id,
        PromotionBatch.to_academic_year_id == to_year_id,
        PromotionBatch.status == "APPLIED"))
    if existing is not None:
        raise ConflictError("A promotion batch between these years was already applied.",
                            code="BATCH_EXISTS")

    batch = PromotionBatch(id=uuid7(), school_id=school_id,
                           from_academic_year_id=from_year_id,
                           to_academic_year_id=to_year_id, status="APPLIED",
                           created_by=actor_id)
    db.add(batch)
    db.flush()

    mapping = stream_mapping or {}
    by_student = {str(d["student_id"]): d for d in decisions}

    rows = db.execute(
        select(Enrollment, Student, ClassStream, Grade)
        .join(Student, Enrollment.student_id == Student.id)
        .join(ClassStream, Enrollment.class_stream_id == ClassStream.id)
        .join(Grade, ClassStream.grade_id == Grade.id)
        .where(Enrollment.school_id == school_id,
               Enrollment.academic_year_id == from_year_id,
               Enrollment.status == "ACTIVE")).all()

    if not rows:
        raise ConflictError("No active enrollments found in the source year.",
                            code="NO_STUDENTS")

    for enrollment, student, stream, grade in rows:
        spec = by_student.get(str(student.id))
        decision = (spec or {}).get("decision")
        if decision is None:
            raise ConflictError(
                f"No decision provided for {student.full_name} ({student.admission_code}). "
                "Every student needs an explicit decision (BR-S05).",
                code="DECISION_MISSING")
        if decision == "GRADUATE" and not (grade.band == "JHS" and grade.code == "JHS3"):
            raise ConflictError("Only JHS 3 students may graduate (BR-S06).",
                                code="GRADUATE_INVALID")
        to_stream_id = None
        if decision == "PROMOTE":
            target = (spec or {}).get("to_class_stream_id")
            if target:
                target_stream = db.get(ClassStream, uuid.UUID(target))
                if target_stream is None or str(target_stream.academic_year_id) != str(to_year_id):
                    raise NotFoundError("Target class stream not found in target year.")
                to_stream = target_stream
            else:
                to_stream = _next_stream(db, school_id, mapping, grade, to_year_id)
            if to_stream is None:
                raise ConflictError(
                    f"No target stream found for {student.full_name}; provide an explicit "
                    "to_class_stream_id or create next-year streams first.",
                    code="NO_TARGET_STREAM")
            to_stream_id = to_stream.id
        elif decision == "REPEAT":
            same_grade_stream = db.scalar(select(ClassStream).where(
                ClassStream.school_id == school_id,
                ClassStream.academic_year_id == to_year_id,
                ClassStream.grade_id == grade.id,
                ClassStream.section_label == stream.section_label))
            if same_grade_stream is None:
                raise ConflictError(
                    f"No stream for repeating {grade.name} in target year.",
                    code="NO_TARGET_STREAM")
            to_stream_id = same_grade_stream.id

        pd = PromotionDecision(id=uuid7(), school_id=school_id, batch_id=batch.id,
                               student_id=student.id,
                               from_enrollment_id=enrollment.id,
                               to_class_stream_id=to_stream_id,
                               decision=decision, note=(spec or {}).get("note"))
        db.add(pd)
        db.flush()

        # close old enrollment
        enrollment.status = "COMPLETED"
        enrollment.ended_on = from_year.ends_on
        enrollment.promotion_decision_id = pd.id

        previous = student.status
        if decision == "PROMOTE":
            student.status = "PROMOTED"
            enroll_svc.create_enrollment(db, school_id=school_id, student_id=student.id,
                                         class_stream_id=to_stream_id,
                                         academic_year_id=to_year_id, actor_id=actor_id,
                                         request=request)
        elif decision == "REPEAT":
            student.status = "REPEATED"
            enroll_svc.create_enrollment(db, school_id=school_id, student_id=student.id,
                                         class_stream_id=to_stream_id,
                                         academic_year_id=to_year_id, is_repeat=True,
                                         actor_id=actor_id, request=request)
        elif decision == "WITHDRAWN" or decision == "WITHDRAW":
            student.status = "WITHDRAWN"
        elif decision == "TRANSFER":
            student.status = "TRANSFERRED"
        elif decision == "GRADUATE":
            student.status = "GRADUATED"
        audit(db, actor_id=actor_id, action="promotion.decision", entity_type="student",
              entity_id=student.id, previous={"status": previous},
              new={"status": student.status, "decision": decision}, request=request)

    from app.models.base import utcnow
    batch.applied_at = utcnow()
    batch.updated_by = actor_id
    audit(db, actor_id=actor_id, action="promotion.applied", entity_type="promotion_batch",
          entity_id=batch.id,
          new={"from_year": from_year.name, "to_year": to_year.name,
               "students": len(rows)},
          request=request)
    db.flush()
    return batch
