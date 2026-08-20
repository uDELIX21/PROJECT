"""Parent/guardian endpoints incl. explicit student linking (REQ-PAR-*)."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.db import get_db
from app.models.core import ParentGuardian, ParentStudentRelationship
from app.schemas import common
from app.schemas.requests import GuardianCreateIn, GuardianLinkIn
from app.services import guardians as svc

router = APIRouter(prefix="/parents", tags=["parents"])


@router.get("")
def list_parents(q: str | None = Query(default=None, max_length=80),
                 limit: int = Query(default=20, ge=1, le=100),
                 offset: int = Query(default=0, ge=0),
                 ctx: AuthContext = Depends(require(rbac.VIEW_PARENT)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(ParentGuardian).where(ParentGuardian.school_id == school.id)
    count = select(func.count()).select_from(ParentGuardian) \
        .where(ParentGuardian.school_id == school.id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(func.lower(ParentGuardian.name).like(like)
                          | ParentGuardian.phone.like(f"%{q}%"))
        count = count.where(func.lower(ParentGuardian.name).like(like)
                            | ParentGuardian.phone.like(f"%{q}%"))
    total = db.scalar(count) or 0
    rows = db.scalars(stmt.order_by(ParentGuardian.name).limit(limit).offset(offset)).all()
    return {"items": [common.guardian(g) for g in rows], "total": int(total),
            "limit": limit, "offset": offset}


@router.post("", status_code=201)
def create_parent(body: GuardianCreateIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.EDIT_PARENT)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    g = svc.create_guardian(db, school_id=school.id, actor_id=ctx.user.id,
                            request=request, **body.model_dump(exclude_none=True))
    db.commit()
    return common.guardian(g)


@router.get("/{parent_id}")
def get_parent(parent_id: uuid.UUID, ctx: AuthContext = Depends(require(rbac.VIEW_PARENT)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    g = svc.get_guardian(db, school.id, parent_id)
    return common.guardian(g)


@router.get("/{parent_id}/children")
def parent_children(parent_id: uuid.UUID,
                    ctx: AuthContext = Depends(require(rbac.VIEW_PARENT)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    svc.get_guardian(db, school.id, parent_id)
    rels = db.scalars(select(ParentStudentRelationship).where(
        ParentStudentRelationship.parent_id == parent_id,
        ParentStudentRelationship.school_id == school.id)).all()
    from app.models.core import Student
    items = []
    for r in rels:
        s = db.get(Student, r.student_id)
        if s:
            items.append({**common.relationship(r), "student": common.student(s)})
    return {"items": items}


@router.post("/{parent_id}/links", status_code=201)
def link_student(parent_id: uuid.UUID, body: GuardianLinkIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.EDIT_PARENT)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    rel = svc.link_student(db, school_id=school.id, parent_id=parent_id,
                           student_id=body.student_id,
                           relationship_type=body.relationship_type,
                           is_primary_contact=body.is_primary_contact,
                           is_billing_contact=body.is_billing_contact,
                           actor_id=ctx.user.id, source="MANUAL", request=request)
    db.commit()
    return common.relationship(rel)


@router.delete("/{parent_id}/links/{rel_id}", status_code=204)
def unlink_student(parent_id: uuid.UUID, rel_id: uuid.UUID, request: Request,
                   ctx: AuthContext = Depends(require(rbac.EDIT_PARENT)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    rel = db.get(ParentStudentRelationship, rel_id)
    if rel is None or rel.parent_id != parent_id or rel.school_id != school.id:
        from app.core.errors import NotFoundError
        raise NotFoundError("Relationship not found.")
    svc.unlink_student(db, rel, actor_id=ctx.user.id, request=request)
    db.commit()
    return None
