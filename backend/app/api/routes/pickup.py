"""Authorized pickup endpoints (REQ-PKU-01), esp. for early childhood."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, assert_student_visible, get_school, require
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.models.core import Enrollment, ClassStream, Grade
from app.models.operations import PickupAuthorization
from app.schemas.requests import PickupCreateIn, PickupRevokeIn
from app.services import pickup as svc

router = APIRouter(prefix="/pickup", tags=["pickup"])


@router.get("")
def list_for_student(student_id: uuid.UUID,
                     ctx: AuthContext = Depends(require(rbac.VIEW_STUDENT)),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    assert_student_visible(ctx, db, student_id)
    rows = svc.list_for_student(db, student_id)
    return {"items": [{"id": str(r.id), "person_name": r.person_name,
                       "relationship": r.relationship, "phone": r.phone,
                       "status": svc.effective_status(r),
                       "valid_from": str(r.valid_from) if r.valid_from else None,
                       "expires_on": str(r.expires_on) if r.expires_on else None,
                       "created_by": str(r.created_by) if r.created_by else None}
                      for r in rows]}


@router.post("", status_code=201)
def create(body: PickupCreateIn, request: Request,
           ctx: AuthContext = Depends(require(rbac.MANAGE_PICKUP)),
           db: Session = Depends(get_db)):
    school = get_school(db)
    assert_student_visible(ctx, db, body.student_id)
    row = svc.create_authorization(db, school_id=school.id, student_id=body.student_id,
                                   person_name=body.person_name,
                                   relationship=body.relationship, phone=body.phone,
                                   id_reference=body.id_reference,
                                   expires_on=body.expires_on,
                                   actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(row.id), "status": svc.effective_status(row)}


@router.post("/{auth_id}/revoke")
def revoke(auth_id: uuid.UUID, body: PickupRevokeIn, request: Request,
           ctx: AuthContext = Depends(require(rbac.MANAGE_PICKUP)),
           db: Session = Depends(get_db)):
    school = get_school(db)
    row = db.get(PickupAuthorization, auth_id)
    if row is None or row.school_id != school.id:
        raise NotFoundError("Pickup authorization not found.")
    assert_student_visible(ctx, db, row.student_id)
    svc.revoke(db, row, reason=body.reason, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"status": row.status}


@router.get("/early-childhood")
def early_childhood_overview(ctx: AuthContext = Depends(require(rbac.MANAGE_PICKUP)),
                             db: Session = Depends(get_db)):
    """School-wide view: EC students and their active pickup authorizations."""
    school = get_school(db)
    from app.models.core import Student
    rows = db.execute(
        select(Student, PickupAuthorization)
        .join(Enrollment, Enrollment.student_id == Student.id)
        .join(ClassStream, Enrollment.class_stream_id == ClassStream.id)
        .join(Grade, ClassStream.grade_id == Grade.id)
        .outerjoin(PickupAuthorization, PickupAuthorization.student_id == Student.id)
        .where(Enrollment.status == "ACTIVE", Grade.band == "EARLY_CHILDHOOD",
               Enrollment.school_id == school.id)).all()
    out = {}
    for student, auth in rows:
        entry = out.setdefault(str(student.id), {
            "student_id": str(student.id), "student_name": student.full_name,
            "authorizations": []})
        if auth is not None:
            entry["authorizations"].append({
                "id": str(auth.id), "person_name": auth.person_name,
                "phone": auth.phone, "status": svc.effective_status(auth)})
    return {"items": list(out.values())}
