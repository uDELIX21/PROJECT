"""Offline sync mutation ledger (design §09): server-side idempotency & conflicts."""
import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, SchoolScopedMixin, utcnow


class SyncMutation(Base, IdMixin, SchoolScopedMixin):
    """Every offline mutation lands here exactly once (client_mutation_id unique).

    Replays return the stored result — the mutation is never applied twice
    (REQ-OFF-03, design §09.3)."""
    __tablename__ = "sync_mutations"

    client_mutation_id: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    entity_ref: Mapped[str] = mapped_column(String(160), nullable=False)
    base_version: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    response: Mapped[dict | None] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        CheckConstraint("status IN ('APPLIED','REJECTED','CONFLICT')", name="status_valid"),
        CheckConstraint(
            "entity_type IN ('ASSESSMENT_SCORE','ATTENDANCE_RECORD')",
            name="entity_type_valid"),
    )
