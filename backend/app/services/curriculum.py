"""Versioned curriculum engine (REQ-CUR-*, BR-C).

Published versions are immutable — edits happen in a new draft version;
references store concrete indicator ids so history survives re-versioning.
"""
import uuid

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.academic import (ContentStandard, Curriculum, CurriculumVersion,
                                 CoreCompetency, Indicator, Strand, SubStrand)
from app.models.base import utcnow

SEED_COMPETENCIES = [
    ("CRITICAL_THINKING", "Critical Thinking"),
    ("CREATIVITY", "Creativity"),
    ("COMMUNICATION", "Communication"),
    ("COLLABORATION", "Collaboration"),
    ("DIGITAL_LITERACY", "Digital Literacy"),
    ("PROBLEM_SOLVING", "Problem Solving"),
]

SEED_ECD_DOMAINS = [
    ("GROSS_MOTOR", "Gross Motor Skills"),
    ("FINE_MOTOR", "Fine Motor Skills"),
    ("LANGUAGE", "Language & Speech"),
    ("COGNITIVE", "Cognitive Development"),
    ("SOCIAL", "Social Development"),
    ("EMOTIONAL", "Emotional Development"),
    ("SELF_CARE", "Self-Care"),
    ("CREATIVITY", "Creativity"),
    ("OBSERVATION", "Teacher Observation"),
]


def bootstrap_catalogs(db: Session, school_id: uuid.UUID) -> None:
    """Idempotent seeding of competency & domain catalogs (config rows, not code)."""
    from app.models.academic import DevelopmentalDomain
    for code, name in SEED_COMPETENCIES:
        exists = db.scalar(select(CoreCompetency).where(
            CoreCompetency.school_id == school_id, CoreCompetency.code == code))
        if exists is None:
            db.add(CoreCompetency(id=uuid7(), school_id=school_id, code=code, name=name))
    for idx, (code, name) in enumerate(SEED_ECD_DOMAINS):
        exists = db.scalar(select(DevelopmentalDomain).where(
            DevelopmentalDomain.school_id == school_id, DevelopmentalDomain.code == code))
        if exists is None:
            db.add(DevelopmentalDomain(id=uuid7(), school_id=school_id, code=code,
                                       name=name, ordinal=idx + 1))
    db.flush()


def create_version(db: Session, *, school_id: uuid.UUID, curriculum_id: uuid.UUID,
                   version_label: str, actor_id: uuid.UUID | None = None,
                   copy_from_version_id: uuid.UUID | None = None,
                   request: Request | None = None) -> CurriculumVersion:
    curriculum = db.get(Curriculum, curriculum_id)
    if curriculum is None or curriculum.school_id != school_id:
        raise NotFoundError("Curriculum not found.")
    dup = db.scalar(select(CurriculumVersion).where(
        CurriculumVersion.curriculum_id == curriculum_id,
        CurriculumVersion.version_label == version_label))
    if dup is not None:
        raise ConflictError("Version label already exists.", code="VERSION_EXISTS")
    version = CurriculumVersion(id=uuid7(), school_id=school_id, curriculum_id=curriculum_id,
                                version_label=version_label, created_by=actor_id)
    db.add(version)
    db.flush()
    if copy_from_version_id is not None:
        src = db.get(CurriculumVersion, copy_from_version_id)
        if src is None or src.curriculum_id != curriculum_id:
            raise NotFoundError("Source version not found.")
        _copy_tree(db, school_id, src.id, version.id)
    audit(db, actor_id=actor_id, action="curriculum.version_created",
          entity_type="curriculum_version", entity_id=version.id,
          new={"label": version_label, "copied_from": str(copy_from_version_id)
               if copy_from_version_id else None}, request=request)
    return version


def _copy_tree(db: Session, school_id: uuid.UUID, src_version_id: uuid.UUID,
               dst_version_id: uuid.UUID) -> None:
    for strand in db.scalars(select(Strand).where(Strand.curriculum_version_id == src_version_id)):
        new_strand = Strand(id=uuid7(), school_id=school_id, curriculum_version_id=dst_version_id,
                            grade_id=strand.grade_id, subject_id=strand.subject_id,
                            code=strand.code, title=strand.title, ordinal=strand.ordinal)
        db.add(new_strand)
        db.flush()
        for sub in db.scalars(select(SubStrand).where(SubStrand.strand_id == strand.id)):
            new_sub = SubStrand(id=uuid7(), school_id=school_id, strand_id=new_strand.id,
                                code=sub.code, title=sub.title, ordinal=sub.ordinal)
            db.add(new_sub)
            db.flush()
            for cs in db.scalars(select(ContentStandard).where(ContentStandard.sub_strand_id == sub.id)):
                new_cs = ContentStandard(id=uuid7(), school_id=school_id, sub_strand_id=new_sub.id,
                                         code=cs.code, title=cs.title, ordinal=cs.ordinal)
                db.add(new_cs)
                db.flush()
                for ind in db.scalars(select(Indicator).where(Indicator.content_standard_id == cs.id)):
                    db.add(Indicator(id=uuid7(), school_id=school_id,
                                     content_standard_id=new_cs.id, code=ind.code,
                                     title=ind.title, ordinal=ind.ordinal))


def publish_version(db: Session, version: CurriculumVersion, *, actor_id: uuid.UUID,
                    request: Request | None = None) -> CurriculumVersion:
    if version.status != "DRAFT":
        raise ConflictError("Only draft versions can be published.", code="NOT_DRAFT")
    version.status = "PUBLISHED"
    version.published_at = utcnow()
    version.updated_by = actor_id
    audit(db, actor_id=actor_id, action="curriculum.published",
          entity_type="curriculum_version", entity_id=version.id,
          new={"label": version.version_label}, request=request)
    db.flush()
    return version


def assert_draft(version: CurriculumVersion) -> None:
    """BR-C01: published versions are immutable."""
    if version.status != "DRAFT":
        raise ConflictError(
            "Published curriculum versions are immutable; create a new draft version.",
            code="VERSION_IMMUTABLE")


def add_strand(db: Session, *, school_id: uuid.UUID, version: CurriculumVersion,
               grade_id: uuid.UUID, subject_id: uuid.UUID, code: str, title: str,
               ordinal: int = 1) -> Strand:
    assert_draft(version)
    row = Strand(id=uuid7(), school_id=school_id, curriculum_version_id=version.id,
                 grade_id=grade_id, subject_id=subject_id, code=code, title=title,
                 ordinal=ordinal)
    db.add(row)
    db.flush()
    return row


def get_tree(db: Session, version_id: uuid.UUID, grade_id: uuid.UUID | None = None,
             subject_id: uuid.UUID | None = None) -> list[dict]:
    stmt = select(Strand).where(Strand.curriculum_version_id == version_id)
    if grade_id:
        stmt = stmt.where(Strand.grade_id == grade_id)
    if subject_id:
        stmt = stmt.where(Strand.subject_id == subject_id)
    out = []
    for strand in db.scalars(stmt.order_by(Strand.ordinal)):
        node = {"id": str(strand.id), "code": strand.code, "title": strand.title,
                "grade_id": str(strand.grade_id), "subject_id": str(strand.subject_id),
                "sub_strands": []}
        for sub in db.scalars(select(SubStrand).where(SubStrand.strand_id == strand.id)
                              .order_by(SubStrand.ordinal)):
            sub_node = {"id": str(sub.id), "code": sub.code, "title": sub.title,
                        "content_standards": []}
            for cs in db.scalars(select(ContentStandard)
                                 .where(ContentStandard.sub_strand_id == sub.id)
                                 .order_by(ContentStandard.ordinal)):
                cs_node = {"id": str(cs.id), "code": cs.code, "title": cs.title,
                           "indicators": []}
                for ind in db.scalars(select(Indicator)
                                      .where(Indicator.content_standard_id == cs.id)
                                      .order_by(Indicator.ordinal)):
                    cs_node["indicators"].append({"id": str(ind.id), "code": ind.code,
                                                  "title": ind.title})
                sub_node["content_standards"].append(cs_node)
            node["sub_strands"].append(sub_node)
        out.append(node)
    return out
