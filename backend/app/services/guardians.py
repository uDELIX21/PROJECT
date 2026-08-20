"""Parent/guardian service: profiles + explicit student relationships (BR-P)."""
import uuid

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.core.phones import normalize_ghana_phone
from app.models.core import ParentGuardian, ParentStudentRelationship, Student


def create_guardian(db: Session, *, school_id: uuid.UUID, name: str, phone: str,
                    actor_id: uuid.UUID | None = None, request: Request | None = None,
                    **fields) -> ParentGuardian:
    normalized = normalize_ghana_phone(phone)
    if normalized is None:
        raise ConflictError("Phone must be a valid Ghanaian number (e.g. 0241234567 or +233241234567).",
                            code="PHONE_INVALID")
    phone2 = fields.pop("phone2", None)
    if phone2:
        n2 = normalize_ghana_phone(phone2)
        if n2 is None:
            raise ConflictError("Second phone is not a valid Ghanaian number.",
                                code="PHONE_INVALID")
        fields["phone2"] = n2
    guardian = ParentGuardian(id=uuid7(), school_id=school_id, name=name.strip(),
                              phone=normalized, created_by=actor_id, **fields)
    db.add(guardian)
    db.flush()
    audit(db, actor_id=actor_id, action="parent.created", entity_type="parent_guardian",
          entity_id=guardian.id, new={"name": guardian.name, "phone": guardian.phone},
          request=request)
    return guardian


def get_guardian(db: Session, school_id: uuid.UUID, guardian_id: uuid.UUID) -> ParentGuardian:
    g = db.get(ParentGuardian, guardian_id)
    if g is None or g.school_id != school_id:
        raise NotFoundError("Parent/guardian not found.")
    return g


def link_student(db: Session, *, school_id: uuid.UUID, parent_id: uuid.UUID,
                 student_id: uuid.UUID, relationship_type: str,
                 actor_id: uuid.UUID | None = None, source: str = "MANUAL",
                 is_primary_contact: bool = False, is_billing_contact: bool = False,
                 request: Request | None = None) -> ParentStudentRelationship:
    parent = get_guardian(db, school_id, parent_id)
    student = db.get(Student, student_id)
    if student is None or student.school_id != school_id:
        raise NotFoundError("Student not found.")
    existing = db.scalar(select(ParentStudentRelationship).where(
        ParentStudentRelationship.parent_id == parent_id,
        ParentStudentRelationship.student_id == student_id,
        ParentStudentRelationship.relationship_type == relationship_type))
    if existing is not None:
        raise ConflictError("This relationship already exists.", code="DUPLICATE_LINK")
    rel = ParentStudentRelationship(
        id=uuid7(), school_id=school_id, parent_id=parent_id, student_id=student_id,
        relationship_type=relationship_type, is_primary_contact=is_primary_contact,
        is_billing_contact=is_billing_contact, source=source, confirmed_by=actor_id)
    db.add(rel)
    audit(db, actor_id=actor_id, action="parent.linked", entity_type="parent_student_relationship",
          entity_id=rel.id,
          new={"parent_id": str(parent_id), "student_id": str(student_id),
               "relationship_type": relationship_type, "source": source},
          request=request)
    db.flush()
    return rel


def unlink_student(db: Session, rel: ParentStudentRelationship, *,
                   actor_id: uuid.UUID | None, request: Request | None = None) -> None:
    audit(db, actor_id=actor_id, action="parent.unlinked",
          entity_type="parent_student_relationship", entity_id=rel.id,
          previous={"parent_id": str(rel.parent_id), "student_id": str(rel.student_id),
                    "relationship_type": rel.relationship_type},
          request=request)
    db.delete(rel)
    db.flush()
