"""Discipline incidents: sensitive records with restricted access (REQ-DIS-01)."""
import uuid
from datetime import datetime

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.base import utcnow
from app.models.core import Student
from app.models.operations import DisciplineIncident

CATEGORIES = ("DISRUPTION", "BULLYING", "FIGHTING", "TRUANCY", "DAMAGE_TO_PROPERTY",
              "DISRESPECT", "UNIFORM_VIOLATION", "ACADEMIC_DISHONESTY", "OTHER")


def create_incident(db: Session, *, school_id: uuid.UUID, student_id: uuid.UUID,
                    category: str, description: str, staff_user_id: uuid.UUID,
                    incident_at: datetime | None = None, severity: str = "MINOR",
                    action_taken: str | None = None,
                    request: Request | None = None) -> DisciplineIncident:
    student = db.get(Student, student_id)
    if student is None or student.school_id != school_id:
        raise NotFoundError("Student not found.")
    if category not in CATEGORIES:
        raise ConflictError(f"Unknown category {category}.", code="CATEGORY_UNKNOWN")
    row = DisciplineIncident(id=uuid7(), school_id=school_id, student_id=student_id,
                             incident_at=incident_at or utcnow(), category=category,
                             description=description, severity=severity,
                             action_taken=action_taken, staff_user_id=staff_user_id,
                             created_by=staff_user_id)
    db.add(row)
    audit(db, actor_id=staff_user_id, action="discipline.created",
          entity_type="discipline_incident", entity_id=row.id,
          new={"category": category, "severity": severity,
               "student_id": str(student_id)}, request=request)
    db.flush()
    return row


def update_status(db: Session, incident: DisciplineIncident, *, status: str,
                  resolution: str | None, action_taken: str | None,
                  actor_id: uuid.UUID, request: Request | None = None) -> DisciplineIncident:
    if status not in ("OPEN", "UNDER_REVIEW", "RESOLVED"):
        raise ConflictError("Invalid status.", code="STATUS_INVALID")
    if status == "RESOLVED" and not resolution:
        raise ConflictError("A resolution note is required to resolve an incident.",
                            code="RESOLUTION_REQUIRED")
    previous = incident.status
    incident.status = status
    if resolution is not None:
        incident.resolution = resolution
    if action_taken is not None:
        incident.action_taken = action_taken
    audit(db, actor_id=actor_id, action="discipline.status_changed",
          entity_type="discipline_incident", entity_id=incident.id,
          previous={"status": previous}, new={"status": status}, request=request)
    db.flush()
    return incident


def mark_parent_notified(db: Session, incident: DisciplineIncident, *,
                         actor_id: uuid.UUID, request: Request | None = None) -> None:
    incident.parent_notified_at = utcnow()
    audit(db, actor_id=actor_id, action="discipline.parent_notified",
          entity_type="discipline_incident", entity_id=incident.id, request=request)
    db.flush()
