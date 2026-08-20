"""Discipline endpoints — restricted access for sensitive records (REQ-DIS-01)."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import (AuthContext, assert_student_visible, get_school, require,
                          student_scope)
from app.core.db import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.models.operations import DisciplineIncident
from app.schemas.requests import IncidentCreateIn, IncidentUpdateIn
from app.services import comms, discipline as svc

router = APIRouter(prefix="/discipline", tags=["discipline"])


def _incident_or_404(db: Session, school_id: uuid.UUID, incident_id: uuid.UUID
                     ) -> DisciplineIncident:
    i = db.get(DisciplineIncident, incident_id)
    if i is None or i.school_id != school_id:
        raise NotFoundError("Incident not found.")
    return i


@router.get("")
def list_incidents(student_id: uuid.UUID | None = None, status: str | None = None,
                   ctx: AuthContext = Depends(require(rbac.VIEW_DISCIPLINE)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(DisciplineIncident).where(DisciplineIncident.school_id == school.id)
    scope = student_scope(ctx, db)
    if ctx.user.parent_id is not None:
        # parents: resolved summaries for own children only (design §28 confidentiality)
        if student_id:
            assert_student_visible(ctx, db, student_id)
            stmt = stmt.where(DisciplineIncident.student_id == student_id)
        else:
            if scope is None:
                raise ForbiddenError()
            stmt = stmt.where(DisciplineIncident.student_id.in_(scope))
        stmt = stmt.where(DisciplineIncident.status == "RESOLVED")
    elif scope is not None:
        # teachers: only students in their assigned classes
        if student_id:
            assert_student_visible(ctx, db, student_id)
            stmt = stmt.where(DisciplineIncident.student_id == student_id)
        else:
            stmt = stmt.where(DisciplineIncident.student_id.in_(scope))
    elif student_id:
        stmt = stmt.where(DisciplineIncident.student_id == student_id)
    if status:
        stmt = stmt.where(DisciplineIncident.status == status)
    rows = db.scalars(stmt.order_by(DisciplineIncident.incident_at.desc()).limit(100)).all()
    items = []
    for i in rows:
        item = {"id": str(i.id), "student_id": str(i.student_id), "category": i.category,
                "severity": i.severity, "status": i.status,
                "incident_at": i.incident_at.isoformat()}
        if ctx.user.parent_id is None:  # full detail staff-only
            item.update({"description": i.description, "action_taken": i.action_taken,
                         "resolution": i.resolution})
        items.append(item)
    return {"items": items}


@router.post("", status_code=201)
def create_incident(body: IncidentCreateIn, request: Request,
                    ctx: AuthContext = Depends(require(rbac.MANAGE_DISCIPLINE)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    # teachers may only log incidents for students in their assigned classes
    assert_student_visible(ctx, db, body.student_id)
    i = svc.create_incident(db, school_id=school.id, student_id=body.student_id,
                            category=body.category, description=body.description,
                            staff_user_id=ctx.user.id, severity=body.severity,
                            action_taken=body.action_taken, request=request)
    db.commit()
    return {"id": str(i.id), "status": i.status}


@router.patch("/{incident_id}")
def update_incident(incident_id: uuid.UUID, body: IncidentUpdateIn, request: Request,
                    ctx: AuthContext = Depends(require(rbac.MANAGE_DISCIPLINE)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    i = _incident_or_404(db, school.id, incident_id)
    svc.update_status(db, i, status=body.status, resolution=body.resolution,
                      action_taken=body.action_taken, actor_id=ctx.user.id,
                      request=request)
    db.commit()
    return {"status": i.status}


@router.post("/{incident_id}/notify-parent")
def notify_parent(incident_id: uuid.UUID, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_DISCIPLINE)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    i = _incident_or_404(db, school.id, incident_id)
    from app.models.core import ParentGuardian, ParentStudentRelationship, Student
    student = db.get(Student, i.student_id)
    sent = 0
    for guardian in db.scalars(select(ParentGuardian).join(
            ParentStudentRelationship,
            ParentStudentRelationship.parent_id == ParentGuardian.id).where(
            ParentStudentRelationship.student_id == i.student_id)).all():
        msg = comms.send_sms(db, school_id=school.id, phone=guardian.phone,
                             body=comms.render(db, school.id, "DISCIPLINE_NOTICE",
                                               {"guardian_name": guardian.name.split()[0],
                                                "student_name": student.full_name if student else "",
                                                "school_name": school.name}),
                             event_code="DISCIPLINE_NOTICE", guardian_id=guardian.id,
                             student_id=i.student_id)
        if msg.status in ("SENT", "SENDING", "QUEUED"):
            sent += 1
        for u in comms.guardian_users(db, i.student_id):
            comms.notify_user(db, school_id=school.id, user_id=u.id,
                              kind="DISCIPLINE_NOTICE", title="Please contact the school",
                              body=f"Please contact the school regarding {student.full_name if student else 'your child'}.",
                              student_id=i.student_id)
    svc.mark_parent_notified(db, i, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"notified": sent}
