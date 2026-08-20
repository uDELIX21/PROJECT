"""Authorized pickup persons (REQ-PKU-01, BR-P03): per-student, expiry-aware, audited."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.core.phones import normalize_ghana_phone
from app.models.base import utcnow
from app.models.core import Student
from app.models.operations import PickupAuthorization


def create_authorization(db: Session, *, school_id: uuid.UUID, student_id: uuid.UUID,
                         person_name: str, relationship: str | None, phone: str | None,
                         id_reference: str | None, expires_on: date | None,
                         actor_id: uuid.UUID, request: Request | None = None
                         ) -> PickupAuthorization:
    student = db.get(Student, student_id)
    if student is None or student.school_id != school_id:
        raise NotFoundError("Student not found.")
    normalized = normalize_ghana_phone(phone) if phone else None
    if phone and normalized is None:
        raise ConflictError("Phone must be a valid Ghanaian number.", code="PHONE_INVALID")
    if expires_on and expires_on <= date.today():
        raise ConflictError("Expiry date must be in the future.", code="EXPIRY_INVALID")
    row = PickupAuthorization(id=uuid7(), school_id=school_id, student_id=student_id,
                              person_name=person_name.strip(), relationship=relationship,
                              phone=normalized, id_reference=id_reference,
                              valid_from=date.today(), expires_on=expires_on,
                              created_by=actor_id)
    db.add(row)
    audit(db, actor_id=actor_id, action="pickup.created", entity_type="pickup_authorization",
          entity_id=row.id, new={"person_name": person_name,
                                 "student_id": str(student_id)}, request=request)
    db.flush()
    return row


def effective_status(row: PickupAuthorization) -> str:
    """Expired authorizations become inactive automatically (BR-P03)."""
    if row.status == "REVOKED":
        return "REVOKED"
    if row.expires_on and row.expires_on < date.today():
        return "EXPIRED"
    return row.status


def list_for_student(db: Session, student_id: uuid.UUID) -> list[PickupAuthorization]:
    return list(db.scalars(select(PickupAuthorization).where(
        PickupAuthorization.student_id == student_id)
        .order_by(PickupAuthorization.created_at.desc())).all())


def revoke(db: Session, row: PickupAuthorization, *, reason: str, actor_id: uuid.UUID,
           request: Request | None = None) -> PickupAuthorization:
    if row.status == "REVOKED":
        raise ConflictError("Already revoked.", code="ALREADY_REVOKED")
    previous = effective_status(row)
    row.status = "REVOKED"
    row.revoked_at = utcnow()
    row.revoked_by = actor_id
    row.revoke_reason = reason
    audit(db, actor_id=actor_id, action="pickup.revoked", entity_type="pickup_authorization",
          entity_id=row.id, previous={"status": previous}, new={"status": "REVOKED"},
          reason=reason, request=request)
    db.flush()
    return row
