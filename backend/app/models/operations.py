"""Operations models: appraisals, discipline, pickup, communications (design §03)."""
import uuid
from datetime import date, datetime

from sqlalchemy import (Boolean, CheckConstraint, Date, DateTime, ForeignKey,
                        Integer, String, Text, UniqueConstraint, Uuid)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import (ActorMixin, Base, IdMixin, SchoolScopedMixin,
                             TimestampMixin, utcnow)

APPRAISAL_STATUSES = ("DRAFT", "SUBMITTED", "ACKNOWLEDGED")
INCIDENT_STATUSES = ("OPEN", "UNDER_REVIEW", "RESOLVED")
INCIDENT_SEVERITIES = ("MINOR", "MODERATE", "SERIOUS")
PICKUP_STATUSES = ("ACTIVE", "REVOKED", "EXPIRED")
SMS_STATUSES = ("QUEUED", "SENDING", "SENT", "DELIVERED", "FAILED", "SKIPPED")
NOTIF_KINDS = ("PAYMENT_CONFIRMED", "FEE_REMINDER", "REPORT_AVAILABLE",
               "EMERGENCY_BROADCAST", "ANNOUNCEMENT", "DISCIPLINE_NOTICE",
               "APPRAISAL_SUBMITTED", "SYSTEM")


class AppraisalCriterion(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "appraisal_criteria"

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=10)
    weight_pct: Mapped[float] = mapped_column(default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_appraisal_criteria_school_code"),)


class TeacherAppraisal(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "teacher_appraisals"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teachers.id"), nullable=False, index=True)
    evaluator_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False)
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", index=True)
    overall_comment: Mapped[str | None] = mapped_column(Text)
    overall_rating: Mapped[float | None] = mapped_column()
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','SUBMITTED','ACKNOWLEDGED')", name="status_valid"),
        CheckConstraint("period_from <= period_to", name="period_ordered"),
    )


class AppraisalScore(Base, IdMixin, SchoolScopedMixin):
    __tablename__ = "appraisal_scores"

    appraisal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teacher_appraisals.id", ondelete="CASCADE"),
        nullable=False, index=True)
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("appraisal_criteria.id"), nullable=False)
    score: Mapped[float] = mapped_column(nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("appraisal_id", "criterion_id", name="uq_appraisal_scores_pair"),)


class DisciplineIncident(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "discipline_incidents"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    incident_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="MINOR")
    action_taken: Mapped[str | None] = mapped_column(Text)
    staff_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="OPEN", index=True)
    resolution: Mapped[str | None] = mapped_column(Text)
    parent_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("status IN ('OPEN','UNDER_REVIEW','RESOLVED')", name="status_valid"),
        CheckConstraint("severity IN ('MINOR','MODERATE','SERIOUS')", name="severity_valid"),
    )


class PickupAuthorization(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "pickup_authorizations"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    person_name: Mapped[str] = mapped_column(String(160), nullable=False)
    relationship: Mapped[str | None] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(20))
    photo_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    id_reference: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)
    valid_from: Mapped[date | None] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    revoke_reason: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE','REVOKED','EXPIRED')", name="status_valid"),
    )


class CommunicationTemplate(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "communication_templates"

    event_code: Mapped[str] = mapped_column(String(40), nullable=False)
    channel: Mapped[str] = mapped_column(String(8), default="SMS")
    template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("school_id", "event_code", "channel",
                         name="uq_comm_templates_event_channel"),
        CheckConstraint("channel IN ('SMS','IN_APP')", name="channel_valid"),
    )


class SMSMessage(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "sms_messages"

    recipient_guardian_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("parent_guardians.id"), index=True)
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    event_code: Mapped[str | None] = mapped_column(String(40))
    rendered_body: Mapped[str] = mapped_column(Text, nullable=False)
    provider_code: Mapped[str] = mapped_column(String(32), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(96))
    status: Mapped[str] = mapped_column(String(16), default="QUEUED", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(255))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    student_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("students.id"))

    __table_args__ = (
        CheckConstraint(
            "status IN ('QUEUED','SENDING','SENT','DELIVERED','FAILED','SKIPPED')",
            name="status_valid"),
    )


class Notification(Base, IdMixin, SchoolScopedMixin):
    __tablename__ = "notifications"

    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(String(255))
    student_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("students.id"))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
