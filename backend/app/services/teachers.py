"""Teacher registry & assignment service (REQ-TCH-*, scoping source)."""
import uuid

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.core.phones import normalize_ghana_phone
from app.models.core import ClassStream, Teacher, TeacherAssignment


def create_teacher(db: Session, *, school_id: uuid.UUID, surname: str, other_names: str,
                   actor_id: uuid.UUID | None = None, request: Request | None = None,
                   **fields) -> Teacher:
    phone = fields.pop("phone", None)
    if phone:
        normalized = normalize_ghana_phone(phone)
        if normalized is None:
            raise ConflictError("Phone must be a valid Ghanaian number.", code="PHONE_INVALID")
        fields["phone"] = normalized
    teacher = Teacher(id=uuid7(), school_id=school_id, surname=surname.strip(),
                      other_names=other_names.strip(), created_by=actor_id, **fields)
    db.add(teacher)
    db.flush()
    audit(db, actor_id=actor_id, action="teacher.created", entity_type="teacher",
          entity_id=teacher.id, new={"name": teacher.full_name}, request=request)
    return teacher


def get_teacher(db: Session, school_id: uuid.UUID, teacher_id: uuid.UUID) -> Teacher:
    t = db.get(Teacher, teacher_id)
    if t is None or t.school_id != school_id:
        raise NotFoundError("Teacher not found.")
    return t


def create_assignment(db: Session, *, school_id: uuid.UUID, teacher_id: uuid.UUID,
                      academic_year_id: uuid.UUID, class_stream_id: uuid.UUID,
                      subject_id: uuid.UUID | None = None,
                      role: str = "SUBJECT_TEACHER",
                      actor_id: uuid.UUID | None = None,
                      request: Request | None = None) -> TeacherAssignment:
    get_teacher(db, school_id, teacher_id)
    stream = db.get(ClassStream, class_stream_id)
    if stream is None or stream.school_id != school_id or \
            str(stream.academic_year_id) != str(academic_year_id):
        raise ConflictError("Class stream does not belong to the given academic year.",
                            code="STREAM_YEAR_MISMATCH")
    if role == "FORM_TEACHER":
        existing = db.scalar(select(TeacherAssignment).where(
            TeacherAssignment.class_stream_id == class_stream_id,
            TeacherAssignment.academic_year_id == academic_year_id,
            TeacherAssignment.role == "FORM_TEACHER",
            TeacherAssignment.is_active.is_(True)))
        if existing is not None:
            raise ConflictError("This class already has an active form teacher.",
                                code="FORM_TEACHER_EXISTS")
        subject_id = None
    assignment = TeacherAssignment(id=uuid7(), school_id=school_id, teacher_id=teacher_id,
                                   academic_year_id=academic_year_id,
                                   class_stream_id=class_stream_id, subject_id=subject_id,
                                   role=role)
    db.add(assignment)
    audit(db, actor_id=actor_id, action="assignment.created", entity_type="teacher_assignment",
          entity_id=assignment.id,
          new={"teacher_id": str(teacher_id), "class_stream_id": str(class_stream_id),
               "subject_id": str(subject_id) if subject_id else None, "role": role},
          request=request)
    db.flush()
    return assignment


def teacher_stream_ids(db: Session, teacher_id: uuid.UUID,
                       academic_year_id: uuid.UUID) -> set[uuid.UUID]:
    rows = db.scalars(select(TeacherAssignment.class_stream_id).where(
        TeacherAssignment.teacher_id == teacher_id,
        TeacherAssignment.academic_year_id == academic_year_id,
        TeacherAssignment.is_active.is_(True))).all()
    return set(rows)
