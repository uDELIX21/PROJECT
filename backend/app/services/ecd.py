"""Early-childhood developmental assessment (REQ-ECD-*, BR-E) + core competencies."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.academic import (CompetencyRating, DevelopmentalDomain,
                                 DevelopmentalRating, ObservationLog)

RATINGS = ("EMERGING", "DEVELOPING", "ACHIEVED")


def domains(db: Session, school_id: uuid.UUID) -> list[DevelopmentalDomain]:
    return list(db.scalars(select(DevelopmentalDomain).where(
        DevelopmentalDomain.school_id == school_id,
        DevelopmentalDomain.is_active.is_(True)).order_by(DevelopmentalDomain.ordinal)).all())


def upsert_rating(db: Session, *, school_id: uuid.UUID, enrollment_id: uuid.UUID,
                  term_id: uuid.UUID, domain_id: uuid.UUID, rating: str,
                  comment: str | None, actor_id: uuid.UUID,
                  request: Request | None = None) -> DevelopmentalRating:
    if rating not in RATINGS:
        raise ConflictError(f"Rating must be one of {RATINGS}.", code="RATING_INVALID")
    row = db.scalar(select(DevelopmentalRating).where(
        DevelopmentalRating.enrollment_id == enrollment_id,
        DevelopmentalRating.term_id == term_id,
        DevelopmentalRating.domain_id == domain_id))
    if row is None:
        row = DevelopmentalRating(id=uuid7(), school_id=school_id,
                                  enrollment_id=enrollment_id, term_id=term_id,
                                  domain_id=domain_id, rating=rating, comment=comment,
                                  created_by=actor_id)
        db.add(row)
    else:
        previous = row.rating
        row.rating = rating
        row.comment = comment
        row.updated_by = actor_id
        audit(db, actor_id=actor_id, action="ecd.rating_changed",
              entity_type="developmental_rating", entity_id=row.id,
              previous={"rating": previous}, new={"rating": rating}, request=request)
    db.flush()
    return row


def ratings_for(db: Session, enrollment_id: uuid.UUID,
                term_id: uuid.UUID) -> list[DevelopmentalRating]:
    return list(db.scalars(select(DevelopmentalRating).where(
        DevelopmentalRating.enrollment_id == enrollment_id,
        DevelopmentalRating.term_id == term_id)).all())


def add_observation(db: Session, *, school_id: uuid.UUID, enrollment_id: uuid.UUID,
                    logged_on: date, body: str, author_id: uuid.UUID,
                    supersedes: uuid.UUID | None = None,
                    request: Request | None = None) -> ObservationLog:
    """Append-only notes; editing creates a revision chain (BR-E02)."""
    if supersedes is not None:
        old = db.get(ObservationLog, supersedes)
        if old is None or old.school_id != school_id:
            raise NotFoundError("Observation not found.")
        if old.superseded_by is not None:
            raise ConflictError("That observation was already revised.", code="ALREADY_SUPERSEDED")
    log = ObservationLog(id=uuid7(), school_id=school_id, enrollment_id=enrollment_id,
                         logged_on=logged_on, author_user_id=author_id, body=body)
    db.add(log)
    db.flush()
    if supersedes is not None:
        old.superseded_by = log.id
    audit(db, actor_id=author_id, action="ecd.observation_added",
          entity_type="observation_log", entity_id=log.id,
          new={"logged_on": str(logged_on), "supersedes": str(supersedes) if supersedes else None},
          request=request)
    return log


def observations_for(db: Session, enrollment_id: uuid.UUID,
                     include_superseded: bool = False) -> list[ObservationLog]:
    stmt = select(ObservationLog).where(ObservationLog.enrollment_id == enrollment_id)
    if not include_superseded:
        stmt = stmt.where(ObservationLog.superseded_by.is_(None))
    return list(db.scalars(stmt.order_by(ObservationLog.logged_on.desc())).all())


def upsert_competency_rating(db: Session, *, school_id: uuid.UUID, enrollment_id: uuid.UUID,
                             term_id: uuid.UUID, competency_id: uuid.UUID, rating: str,
                             comment: str | None, actor_id: uuid.UUID,
                             request: Request | None = None) -> CompetencyRating:
    if rating not in RATINGS:
        raise ConflictError(f"Rating must be one of {RATINGS}.", code="RATING_INVALID")
    row = db.scalar(select(CompetencyRating).where(
        CompetencyRating.enrollment_id == enrollment_id,
        CompetencyRating.term_id == term_id,
        CompetencyRating.competency_id == competency_id))
    if row is None:
        row = CompetencyRating(id=uuid7(), school_id=school_id, enrollment_id=enrollment_id,
                               term_id=term_id, competency_id=competency_id, rating=rating,
                               comment=comment, created_by=actor_id)
        db.add(row)
    else:
        row.rating = rating
        row.comment = comment
        row.updated_by = actor_id
    db.flush()
    return row


def competency_ratings_for(db: Session, enrollment_id: uuid.UUID,
                           term_id: uuid.UUID) -> list[CompetencyRating]:
    return list(db.scalars(select(CompetencyRating).where(
        CompetencyRating.enrollment_id == enrollment_id,
        CompetencyRating.term_id == term_id)).all())
