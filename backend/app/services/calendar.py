"""Academic year & term management (REQ-CAL-*, BR-A)."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.base import utcnow
from app.models.core import AcademicYear, Term


def create_year(db: Session, *, school_id: uuid.UUID, name: str, starts_on: date,
                ends_on: date, actor_id: uuid.UUID | None = None,
                request: Request | None = None) -> AcademicYear:
    dup = db.scalar(select(AcademicYear).where(AcademicYear.school_id == school_id,
                                               AcademicYear.name == name))
    if dup is not None:
        raise ConflictError(f"Academic year '{name}' already exists.", code="YEAR_EXISTS")
    overlap = db.scalar(select(AcademicYear).where(
        AcademicYear.school_id == school_id,
        AcademicYear.starts_on <= ends_on, AcademicYear.ends_on >= starts_on))
    if overlap is not None:
        raise ConflictError("Academic year dates overlap an existing year (BR-A06).",
                            code="YEAR_OVERLAP")
    year = AcademicYear(id=uuid7(), school_id=school_id, name=name,
                        starts_on=starts_on, ends_on=ends_on, created_by=actor_id)
    db.add(year)
    audit(db, actor_id=actor_id, action="year.created", entity_type="academic_year",
          entity_id=year.id, new={"name": name}, request=request)
    db.flush()
    return year


def active_year(db: Session, school_id: uuid.UUID) -> AcademicYear | None:
    return db.scalar(select(AcademicYear).where(AcademicYear.school_id == school_id,
                                                AcademicYear.status == "ACTIVE"))


def activate_year(db: Session, year: AcademicYear, *, actor_id: uuid.UUID | None,
                  request: Request | None = None) -> AcademicYear:
    current = active_year(db, year.school_id)
    if current is not None and current.id != year.id:
        current.status = "ARCHIVED"
        audit(db, actor_id=actor_id, action="year.archived", entity_type="academic_year",
              entity_id=current.id, new={"name": current.name}, request=request)
    year.status = "ACTIVE"
    audit(db, actor_id=actor_id, action="year.activated", entity_type="academic_year",
          entity_id=year.id, new={"name": year.name}, request=request)
    db.flush()
    return year


def create_term(db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID,
                name: str, starts_on: date, ends_on: date,
                actor_id: uuid.UUID | None = None, request: Request | None = None) -> Term:
    year = db.get(AcademicYear, academic_year_id)
    if year is None or year.school_id != school_id:
        raise NotFoundError("Academic year not found.")
    dup = db.scalar(select(Term).where(Term.academic_year_id == academic_year_id,
                                       Term.name == name))
    if dup is not None:
        raise ConflictError(f"Term '{name}' already exists in this year.", code="TERM_EXISTS")
    term = Term(id=uuid7(), school_id=school_id, academic_year_id=academic_year_id,
                name=name, starts_on=starts_on, ends_on=ends_on, created_by=actor_id)
    db.add(term)
    audit(db, actor_id=actor_id, action="term.created", entity_type="term",
          entity_id=term.id, new={"name": name, "year": year.name}, request=request)
    db.flush()
    return term


def active_term(db: Session, school_id: uuid.UUID) -> Term | None:
    return db.scalar(select(Term).where(Term.school_id == school_id,
                                        Term.status == "ACTIVE"))


def activate_term(db: Session, term: Term, *, actor_id: uuid.UUID | None,
                  request: Request | None = None) -> Term:
    current = active_term(db, term.school_id)
    if current is not None and current.id != term.id:
        raise ConflictError(
            f"Term '{current.name}' is active. Close it before activating another (BR-A02).",
            code="TERM_ACTIVE_EXISTS")
    term.status = "ACTIVE"
    audit(db, actor_id=actor_id, action="term.activated", entity_type="term",
          entity_id=term.id, new={"name": term.name}, request=request)
    db.flush()
    return term


def close_term(db: Session, term: Term, *, actor_id: uuid.UUID | None,
               request: Request | None = None) -> Term:
    if term.status != "ACTIVE":
        raise ConflictError("Only the active term can be closed.", code="NOT_ACTIVE_TERM")
    term.status = "CLOSED"
    term.closed_at = utcnow()
    term.closed_by = actor_id
    audit(db, actor_id=actor_id, action="term.closed", entity_type="term",
          entity_id=term.id, new={"name": term.name}, request=request)
    db.flush()
    return term


def reopen_term(db: Session, term: Term, *, actor_id: uuid.UUID | None, reason: str,
                request: Request | None = None) -> Term:
    """Authorized reopening of a closed term — reason mandatory, audited (BR-A02)."""
    if term.status != "CLOSED":
        raise ConflictError("Only closed terms can be reopened.", code="NOT_CLOSED_TERM")
    if not reason or not reason.strip():
        raise ConflictError("A reason is required to reopen a term.", code="REASON_REQUIRED")
    current = active_term(db, term.school_id)
    if current is not None and current.id != term.id:
        raise ConflictError("Another term is already active.", code="TERM_ACTIVE_EXISTS")
    term.status = "ACTIVE"
    term.reopened_at = utcnow()
    term.reopened_by = actor_id
    term.reopen_reason = reason.strip()
    audit(db, actor_id=actor_id, action="term.reopened", entity_type="term",
          entity_id=term.id, new={"name": term.name}, reason=reason.strip(), request=request)
    db.flush()
    return term
