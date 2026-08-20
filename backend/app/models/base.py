"""Declarative base & shared mixins (design §04 conventions)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, MetaData, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.ids import uuid7

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_aware(dt: datetime | None) -> datetime | None:
    """SQLite round-trips datetimes as naive; PostgreSQL returns tz-aware.
    Treat naive values as UTC so comparisons work on both engines."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class SchoolScopedMixin:
    """Every school-owned row carries school_id (tenancy, design §04)."""
    school_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("schools.id"), nullable=False, index=True)


class ActorMixin:
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
