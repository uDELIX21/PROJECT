"""Bulk import models (design §04): job lifecycle + per-row findings."""
import uuid
from datetime import datetime

from sqlalchemy import (JSON, BigInteger, CheckConstraint, DateTime, ForeignKey,
                        Integer, String, Text, Uuid)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import ActorMixin, Base, IdMixin, SchoolScopedMixin, TimestampMixin

JOB_STAGES = ("UPLOADED", "PARSED", "PREVIEWED", "CONFIRMED", "IMPORTING",
              "COMPLETED", "FAILED", "ROLLED_BACK")
ROW_SEVERITIES = ("OK", "WARNING", "ERROR", "DUPLICATE", "MATCH_CANDIDATE")


class ImportJob(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "import_jobs"

    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # STUDENTS|TEACHERS|PARENTS
    file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("stored_files.id"))
    file_name: Mapped[str | None] = mapped_column(String(255))
    stage: Mapped[str] = mapped_column(String(16), default="UPLOADED", index=True)
    options: Mapped[dict] = mapped_column(JSON, default=dict)
    rows_total: Mapped[int] = mapped_column(Integer, default=0)
    rows_ok: Mapped[int] = mapped_column(Integer, default=0)
    rows_warn: Mapped[int] = mapped_column(Integer, default=0)
    rows_error: Mapped[int] = mapped_column(Integer, default=0)
    rows_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    rows_match: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("kind IN ('STUDENTS','TEACHERS','PARENTS')", name="kind_valid"),
        CheckConstraint(
            "stage IN ('UPLOADED','PARSED','PREVIEWED','CONFIRMED','IMPORTING',"
            "'COMPLETED','FAILED','ROLLED_BACK')", name="stage_valid"),
    )


class ImportErrorRow(Base, IdMixin, SchoolScopedMixin):
    """One row per import file row: findings + raw data + match suggestions."""
    __tablename__ = "import_errors"

    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_no: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    field: Mapped[str | None] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    guidance: Mapped[str | None] = mapped_column(Text)
    raw_row: Mapped[dict] = mapped_column(JSON, default=dict)
    match_suggestion: Mapped[dict | None] = mapped_column(JSON)  # candidate + resolution

    __table_args__ = (
        CheckConstraint(
            "severity IN ('OK','WARNING','ERROR','DUPLICATE','MATCH_CANDIDATE')",
            name="severity_valid"),
    )
