"""Curriculum endpoints: versioned tree, publish, competencies (REQ-CUR-*)."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, get_school, require
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.core.ids import uuid7
from app.models.academic import (ContentStandard, CoreCompetency, Curriculum,
                                 CurriculumVersion, Indicator, Strand, SubStrand)
from app.schemas.requests import (CurriculumCreateIn, StrandNodeIn, VersionCreateIn)
from app.services import curriculum as svc

router = APIRouter(prefix="/curriculum", tags=["curriculum"])


def _version(db: Session, school_id: uuid.UUID, version_id: uuid.UUID) -> CurriculumVersion:
    v = db.get(CurriculumVersion, version_id)
    if v is None or v.school_id != school_id:
        raise NotFoundError("Curriculum version not found.")
    return v


@router.get("")
def list_curricula(ctx: AuthContext = Depends(require(rbac.VIEW_GRADES_CONFIG)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(Curriculum).where(Curriculum.school_id == school.id)).all()
    out = []
    for c in rows:
        versions = db.scalars(select(CurriculumVersion).where(
            CurriculumVersion.curriculum_id == c.id)).all()
        out.append({"id": str(c.id), "name": c.name, "origin": c.origin,
                    "versions": [{"id": str(v.id), "label": v.version_label,
                                  "status": v.status} for v in versions]})
    return {"items": out}


@router.post("", status_code=201)
def create_curriculum(body: CurriculumCreateIn, request: Request,
                      ctx: AuthContext = Depends(require(rbac.MANAGE_CURRICULUM)),
                      db: Session = Depends(get_db)):
    school = get_school(db)
    c = Curriculum(id=uuid7(), school_id=school.id, name=body.name, origin=body.origin,
                   description=body.description, created_by=ctx.user.id)
    db.add(c)
    db.commit()
    return {"id": str(c.id), "name": c.name}


@router.post("/versions", status_code=201)
def create_version(body: VersionCreateIn, request: Request,
                   ctx: AuthContext = Depends(require(rbac.MANAGE_CURRICULUM)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    v = svc.create_version(db, school_id=school.id, curriculum_id=body.curriculum_id,
                           version_label=body.version_label,
                           copy_from_version_id=body.copy_from_version_id,
                           actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(v.id), "label": v.version_label, "status": v.status}


@router.post("/versions/{version_id}/publish")
def publish(version_id: uuid.UUID, request: Request,
            ctx: AuthContext = Depends(require(rbac.MANAGE_CURRICULUM)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    v = svc.publish_version(db, _version(db, school.id, version_id),
                            actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(v.id), "status": v.status}


@router.get("/versions/{version_id}/tree")
def tree(version_id: uuid.UUID, grade_id: uuid.UUID | None = None,
         subject_id: uuid.UUID | None = None,
         ctx: AuthContext = Depends(require(rbac.VIEW_GRADES_CONFIG)),
         db: Session = Depends(get_db)):
    school = get_school(db)
    _version(db, school.id, version_id)
    return {"items": svc.get_tree(db, version_id, grade_id, subject_id)}


def _node_write_guard(db: Session, school_id: uuid.UUID, version_id: uuid.UUID):
    return svc.assert_draft(_version(db, school_id, version_id))


@router.post("/versions/{version_id}/strands", status_code=201)
def add_strand(version_id: uuid.UUID, body: StrandNodeIn, request: Request,
               ctx: AuthContext = Depends(require(rbac.MANAGE_CURRICULUM)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    _node_write_guard(db, school.id, version_id)
    row = Strand(id=uuid7(), school_id=school.id, curriculum_version_id=version_id,
                 grade_id=body.grade_id, subject_id=body.subject_id,
                 code=body.code, title=body.title, ordinal=body.ordinal)
    db.add(row)
    db.commit()
    return {"id": str(row.id), "code": row.code}


@router.post("/strands/{parent_id}/sub-strands", status_code=201)
def add_sub_strand(parent_id: uuid.UUID, body: StrandNodeIn, request: Request,
                   ctx: AuthContext = Depends(require(rbac.MANAGE_CURRICULUM)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    parent = db.get(Strand, parent_id)
    if parent is None or parent.school_id != school.id:
        raise NotFoundError("Strand not found.")
    v = db.get(CurriculumVersion, parent.curriculum_version_id)
    svc.assert_draft(v)
    row = SubStrand(id=uuid7(), school_id=school.id, strand_id=parent_id,
                    code=body.code, title=body.title, ordinal=body.ordinal)
    db.add(row)
    db.commit()
    return {"id": str(row.id), "code": row.code}


@router.post("/sub-strands/{parent_id}/content-standards", status_code=201)
def add_content_standard(parent_id: uuid.UUID, body: StrandNodeIn, request: Request,
                         ctx: AuthContext = Depends(require(rbac.MANAGE_CURRICULUM)),
                         db: Session = Depends(get_db)):
    school = get_school(db)
    parent = db.get(SubStrand, parent_id)
    if parent is None or parent.school_id != school.id:
        raise NotFoundError("Sub-strand not found.")
    strand = db.get(Strand, parent.strand_id)
    svc.assert_draft(db.get(CurriculumVersion, strand.curriculum_version_id))
    row = ContentStandard(id=uuid7(), school_id=school.id, sub_strand_id=parent_id,
                          code=body.code, title=body.title, ordinal=body.ordinal)
    db.add(row)
    db.commit()
    return {"id": str(row.id), "code": row.code}


@router.post("/content-standards/{parent_id}/indicators", status_code=201)
def add_indicator(parent_id: uuid.UUID, body: StrandNodeIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_CURRICULUM)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    parent = db.get(ContentStandard, parent_id)
    if parent is None or parent.school_id != school.id:
        raise NotFoundError("Content standard not found.")
    sub = db.get(SubStrand, parent.sub_strand_id)
    strand = db.get(Strand, sub.strand_id)
    svc.assert_draft(db.get(CurriculumVersion, strand.curriculum_version_id))
    row = Indicator(id=uuid7(), school_id=school.id, content_standard_id=parent_id,
                    code=body.code, title=body.title, ordinal=body.ordinal)
    db.add(row)
    db.commit()
    return {"id": str(row.id), "code": row.code}


@router.get("/competencies")
def list_competencies(ctx: AuthContext = Depends(require(rbac.VIEW_GRADES_CONFIG)),
                      db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(CoreCompetency).where(
        CoreCompetency.school_id == school.id)).all()
    return {"items": [{"id": str(c.id), "code": c.code, "name": c.name} for c in rows]}
