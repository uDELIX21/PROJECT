"""Configurable grading scales (REQ-GRD-01, BR-M08)."""
import uuid

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.academic import GradeScale, GradeScaleBand


def _bands_json(bands: list[GradeScaleBand]) -> list[dict]:
    return [{"min": float(b.min_score), "max": float(b.max_score), "code": b.code,
             "remark": b.remark, "rank": b.rank} for b in bands]


def validate_bands(bands_payload: list[dict]) -> None:
    """Ranges must be well-formed and non-overlapping."""
    seen: list[tuple[float, float]] = []
    codes: set[str] = set()
    for b in bands_payload:
        lo, hi = float(b["min_score"]), float(b["max_score"])
        if lo < 0 or hi > 100 or lo > hi:
            raise ConflictError(f"Band {b.get('code')}: invalid range [{lo}, {hi}].",
                                code="BAND_RANGE_INVALID")
        for (a, z) in seen:
            if lo <= z and a <= hi:
                raise ConflictError("Grade bands must not overlap.", code="BANDS_OVERLAP")
        seen.append((lo, hi))
        if b["code"] in codes:
            raise ConflictError("Duplicate grade code in scale.", code="BAND_CODE_DUPLICATE")
        codes.add(b["code"])


def create_scale(db: Session, *, school_id: uuid.UUID, name: str,
                 bands_payload: list[dict], actor_id: uuid.UUID | None = None,
                 scope_band: str | None = None, grade_id: uuid.UUID | None = None,
                 academic_year_id: uuid.UUID | None = None,
                 is_default: bool = False, request: Request | None = None) -> GradeScale:
    validate_bands(bands_payload)
    scale = GradeScale(id=uuid7(), school_id=school_id, name=name, scope_band=scope_band,
                       grade_id=grade_id, academic_year_id=academic_year_id,
                       is_default=is_default, created_by=actor_id)
    db.add(scale)
    db.flush()
    for b in bands_payload:
        db.add(GradeScaleBand(id=uuid7(), school_id=school_id, scale_id=scale.id,
                              min_score=float(b["min_score"]), max_score=float(b["max_score"]),
                              code=b["code"], remark=b["remark"], rank=int(b["rank"])))
    audit(db, actor_id=actor_id, action="grade_scale.created", entity_type="grade_scale",
          entity_id=scale.id, new={"name": name, "bands": bands_payload}, request=request)
    db.flush()
    return scale


def replace_bands(db: Session, scale: GradeScale, bands_payload: list[dict], *,
                  actor_id: uuid.UUID | None, request: Request | None = None) -> GradeScale:
    validate_bands(bands_payload)
    old = db.scalars(select(GradeScaleBand).where(
        GradeScaleBand.scale_id == scale.id)).all()
    previous = _bands_json(list(old))
    for b in old:
        db.delete(b)
    for b in bands_payload:
        db.add(GradeScaleBand(id=uuid7(), school_id=scale.school_id, scale_id=scale.id,
                              min_score=float(b["min_score"]), max_score=float(b["max_score"]),
                              code=b["code"], remark=b["remark"], rank=int(b["rank"])))
    audit(db, actor_id=actor_id, action="grade_scale.bands_changed",
          entity_type="grade_scale", entity_id=scale.id,
          previous=previous, new=bands_payload, request=request)
    db.flush()
    return scale


def get_scale(db: Session, school_id: uuid.UUID, scale_id: uuid.UUID) -> GradeScale:
    s = db.get(GradeScale, scale_id)
    if s is None or s.school_id != school_id:
        raise NotFoundError("Grade scale not found.")
    return s


def bands_for(db: Session, scale_id: uuid.UUID) -> list[GradeScaleBand]:
    return list(db.scalars(select(GradeScaleBand).where(GradeScaleBand.scale_id == scale_id)
                           .order_by(GradeScaleBand.rank)).all())


def resolve_scale(db: Session, *, school_id: uuid.UUID, band: str,
                  grade_id: uuid.UUID | None = None,
                  academic_year_id: uuid.UUID | None = None) -> GradeScale | None:
    """Most specific wins: (grade+year) → (band+year) → band → school default."""
    def query(**kw) -> GradeScale | None:
        stmt = select(GradeScale).where(GradeScale.school_id == school_id)
        for k, v in kw.items():
            stmt = stmt.where(getattr(GradeScale, k) == v) if v is not None \
                else stmt.where(getattr(GradeScale, k).is_(None))
        return db.scalar(stmt.limit(1))

    if grade_id and academic_year_id:
        s = query(grade_id=grade_id, academic_year_id=academic_year_id)
        if s:
            return s
    if academic_year_id:
        s = query(scope_band=band, academic_year_id=academic_year_id, grade_id=None)
        if s:
            return s
    s = query(scope_band=band, academic_year_id=None, grade_id=None)
    if s:
        return s
    return db.scalar(select(GradeScale).where(GradeScale.school_id == school_id,
                                              GradeScale.is_default.is_(True)).limit(1))


def grade_for_score(db: Session, scale: GradeScale, score: float) -> dict | None:
    for b in bands_for(db, scale.id):
        if float(b.min_score) <= score <= float(b.max_score):
            return {"grade": b.code, "remark": b.remark, "rank": b.rank}
    return None
