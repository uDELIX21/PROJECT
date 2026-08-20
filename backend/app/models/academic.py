"""Academic engine models: curriculum, assessment, grading, attendance, ECD, reports."""
import uuid
from datetime import date, datetime

from sqlalchemy import (JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey,
                        Integer, Numeric, String, Text, UniqueConstraint, Uuid)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (ActorMixin, Base, IdMixin, SchoolScopedMixin,
                             TimestampMixin, utcnow)

BANDS = ("EARLY_CHILDHOOD", "PRIMARY", "JHS")
SHEET_STATES = ("DRAFT", "SUBMITTED", "LOCKED")
ATTENDANCE_STATUSES = ("PRESENT", "ABSENT", "LATE", "EXCUSED", "LEFT_EARLY")
COMPONENT_KINDS = ("CLASS", "EXAM")
AGGREGATIONS = ("DIRECT", "MEAN", "BEST")


# --------------------------------------------------------------------------- curriculum

class Curriculum(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "curricula"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    origin: Mapped[str] = mapped_column(String(16), default="NATIONAL")  # NATIONAL|SCHOOL
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_curricula_school_name"),
        CheckConstraint("origin IN ('NATIONAL','SCHOOL')", name="origin_valid"),
    )


class CurriculumVersion(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "curriculum_versions"

    curriculum_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("curricula.id"), nullable=False, index=True)
    version_label: Mapped[str] = mapped_column(String(32), nullable=False)
    effective_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("curriculum_id", "version_label", name="uq_cv_curriculum_label"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED')", name="status_valid"),
    )


class Strand(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "strands"

    curriculum_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("curriculum_versions.id", ondelete="CASCADE"),
        nullable=False, index=True)
    grade_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("grades.id"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("subjects.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("curriculum_version_id", "grade_id", "subject_id", "code",
                         name="uq_strands_version_grade_subject_code"),
    )


class SubStrand(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "sub_strands"

    strand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("strands.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (UniqueConstraint("strand_id", "code", name="uq_sub_strands_strand_code"),)


class ContentStandard(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "content_standards"

    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sub_strands.id", ondelete="CASCADE"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(24), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("sub_strand_id", "code", name="uq_content_standards_sub_strand_code"),)


class Indicator(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "indicators"

    content_standard_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("content_standards.id", ondelete="CASCADE"),
        nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("content_standard_id", "code",
                         name="uq_indicators_content_standard_code"),)


class CoreCompetency(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "core_competencies"

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_core_competencies_school_code"),)


class IndicatorCoreCompetency(Base):
    __tablename__ = "indicator_core_competencies"

    indicator_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("indicators.id", ondelete="CASCADE"), primary_key=True)
    competency_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("core_competencies.id", ondelete="CASCADE"), primary_key=True)


class CompetencyRating(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "competency_ratings"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False, index=True)
    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False)
    competency_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("core_competencies.id"), nullable=False)
    rating: Mapped[str] = mapped_column(String(16), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("enrollment_id", "term_id", "competency_id",
                         name="uq_competency_ratings_unique"),
        CheckConstraint("rating IN ('EMERGING','DEVELOPING','ACHIEVED')", name="rating_valid"),
    )


# --------------------------------------------------------------------------- assessment

class AssessmentScheme(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    """Configurable weighting per (year, term, grade, optional subject). Most specific wins."""
    __tablename__ = "assessment_schemes"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False)
    grade_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("grades.id"), nullable=False)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("subjects.id"))
    name: Mapped[str] = mapped_column(String(80), default="Standard scheme")

    __table_args__ = (
        UniqueConstraint("academic_year_id", "term_id", "grade_id", "subject_id",
                         name="uq_assessment_schemes_scope"),
    )


class AssessmentComponent(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    """A scheme component (e.g. CLASS_SCORE 50%, TERMINAL_EXAM 50%). Config rows, not code."""
    __tablename__ = "assessment_components"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessment_schemes.id", ondelete="CASCADE"),
        nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    weight_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), default=100, nullable=False)
    aggregation: Mapped[str] = mapped_column(String(16), default="DIRECT")
    ordinal: Mapped[int] = mapped_column(Integer, default=1)

    __table_args__ = (
        UniqueConstraint("scheme_id", "code", name="uq_assessment_components_scheme_code"),
        CheckConstraint("kind IN ('CLASS','EXAM')", name="kind_valid"),
        CheckConstraint("aggregation IN ('DIRECT','MEAN','BEST')", name="aggregation_valid"),
        CheckConstraint("weight_pct > 0 AND weight_pct <= 100", name="weight_range"),
        CheckConstraint("max_score > 0", name="max_positive"),
    )


class Assessment(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    """A concrete mark sheet: one class × subject × component × term."""
    __tablename__ = "assessments"

    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False, index=True)
    class_stream_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("class_streams.id"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("subjects.id"), nullable=False)
    component_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessment_components.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", index=True)
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locked_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    component: Mapped[AssessmentComponent] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("term_id", "class_stream_id", "subject_id", "component_id",
                         name="uq_assessments_scope"),
        CheckConstraint("status IN ('DRAFT','SUBMITTED','LOCKED')", name="status_valid"),
    )


class AssessmentScore(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "assessment_scores"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False, index=True)
    raw_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    is_absent: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (
        UniqueConstraint("assessment_id", "enrollment_id", name="uq_assessment_scores_pair"),
        CheckConstraint("raw_score >= 0", name="score_non_negative"),
    )


class ScoreOverride(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    """Controlled correction trail (BR-M04): original preserved, reason + approver recorded."""
    __tablename__ = "score_overrides"

    assessment_score_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("assessment_scores.id"), nullable=False, index=True)
    original_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    new_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="PENDING")  # PENDING|APPROVED|REJECTED


# --------------------------------------------------------------------------- grading

class GradeScale(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "grade_scales"

    name: Mapped[str] = mapped_column(String(80), nullable=False)
    scope_band: Mapped[str | None] = mapped_column(String(16))
    grade_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("grades.id"))
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("academic_years.id"))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint("scope_band IN ('EARLY_CHILDHOOD','PRIMARY','JHS') OR scope_band IS NULL",
                        name="band_valid"),
    )


class GradeScaleBand(Base, IdMixin, SchoolScopedMixin):
    __tablename__ = "grade_scale_bands"

    scale_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("grade_scales.id", ondelete="CASCADE"), nullable=False, index=True)
    min_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    remark: Mapped[str] = mapped_column(String(80), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (CheckConstraint("min_score <= max_score", name="range_ordered"),)


# --------------------------------------------------------------------------- ECD

class DevelopmentalDomain(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "developmental_domains"

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_developmental_domains_school_code"),)


class DevelopmentalRating(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "developmental_ratings"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False, index=True)
    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False)
    domain_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("developmental_domains.id"), nullable=False)
    rating: Mapped[str] = mapped_column(String(16), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("enrollment_id", "term_id", "domain_id",
                         name="uq_developmental_ratings_unique"),
        CheckConstraint("rating IN ('EMERGING','DEVELOPING','ACHIEVED')", name="rating_valid"),
    )


class ObservationLog(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    """Append-only daily observation notes (BR-E02); edits create a revision."""
    __tablename__ = "observation_logs"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False, index=True)
    logged_on: Mapped[date] = mapped_column(Date, nullable=False)
    author_user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    superseded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("observation_logs.id"))


# --------------------------------------------------------------------------- attendance

class AttendanceSheet(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "attendance_sheets"

    class_stream_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("class_streams.id"), nullable=False, index=True)
    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False, index=True)
    sheet_date: Mapped[date] = mapped_column(Date, nullable=False)
    taken_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("class_stream_id", "sheet_date", name="uq_attendance_sheets_class_date"),
        CheckConstraint("status IN ('DRAFT','SUBMITTED')", name="status_valid"),
    )


class AttendanceRecord(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "attendance_records"

    sheet_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("attendance_sheets.id", ondelete="CASCADE"),
        nullable=False, index=True)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (
        UniqueConstraint("sheet_id", "enrollment_id", name="uq_attendance_records_pair"),
        CheckConstraint(
            "status IN ('PRESENT','ABSENT','LATE','EXCUSED','LEFT_EARLY')", name="status_valid"),
    )


# --------------------------------------------------------------------------- reports

class ReportTemplate(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "report_templates"

    band: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    layout_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("school_id", "band", "version", name="uq_report_templates_band_version"),
        CheckConstraint("band IN ('EARLY_CHILDHOOD','PRIMARY','JHS')", name="band_valid"),
    )


class ReportCard(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "report_cards"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False, index=True)
    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("report_templates.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", index=True)
    data_snapshot: Mapped[dict | None] = mapped_column(JSON)
    clearance_snapshot: Mapped[dict | None] = mapped_column(JSON)
    pdf_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("stored_files.id"))
    teacher_remark: Mapped[str | None] = mapped_column(Text)
    head_remark: Mapped[str | None] = mapped_column(Text)
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    override_reason: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("student_id", "term_id", name="uq_report_cards_student_term"),
        CheckConstraint(
            "status IN ('DRAFT','GENERATED','FINALIZED','PUBLISHED')", name="status_valid"),
    )


class StoredFile(Base, IdMixin, TimestampMixin, ActorMixin):
    """File storage registry — DB holds metadata only (REQ-TECH-04)."""
    __tablename__ = "stored_files"

    storage_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    mime: Mapped[str] = mapped_column(String(80), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(64))
