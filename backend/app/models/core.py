"""Core registry models: school, calendar, classes, people, enrollments, promotion."""
import uuid
from datetime import date, datetime

from sqlalchemy import (JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime,
                        ForeignKey, Index, Integer, Numeric, String, Text,
                        UniqueConstraint, Uuid)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (ActorMixin, Base, IdMixin, SchoolScopedMixin,
                             TimestampMixin, utcnow)

# --- enums (VARCHAR + CHECK per design §04) ---
STUDENT_STATUSES = ("APPLICANT", "ADMITTED", "ENROLLED", "ACTIVE", "PROMOTED", "REPEATED",
                    "WITHDRAWN", "TRANSFERRED", "SUSPENDED", "GRADUATED")
ENROLLMENT_STATUSES = ("ACTIVE", "COMPLETED", "WITHDRAWN", "TRANSFERRED")
YEAR_STATUSES = ("DRAFT", "ACTIVE", "ARCHIVED")
TERM_STATUSES = ("DRAFT", "ACTIVE", "CLOSED")
GRADE_BANDS = ("EARLY_CHILDHOOD", "PRIMARY", "JHS")
ASSIGNMENT_ROLES = ("SUBJECT_TEACHER", "FORM_TEACHER")
RELATIONSHIP_TYPES = ("MOTHER", "FATHER", "GUARDIAN", "GRANDPARENT", "SIBLING", "OTHER")
PROMOTION_DECISIONS = ("PROMOTE", "REPEAT", "WITHDRAW", "TRANSFER", "GRADUATE")


class School(Base, IdMixin, TimestampMixin):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(40))
    motto: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    ghana_digital_address: Mapped[str | None] = mapped_column(String(40))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(48), default="Africa/Accra")
    logo_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)


class SchoolSetting(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "school_settings"

    key: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[dict | list | str | int | bool] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))

    __table_args__ = (UniqueConstraint("school_id", "key", name="uq_school_settings_key"),)


class AcademicYear(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. 2026/2027
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", index=True)

    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_academic_years_school_name"),
        CheckConstraint("starts_on < ends_on", name="dates_ordered"),
        CheckConstraint("status IN ('DRAFT','ACTIVE','ARCHIVED')", name="status_valid"),
    )

    terms: Mapped[list["Term"]] = relationship(back_populates="academic_year",
                                               order_by="Term.starts_on")


class Term(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "terms"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(24), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="DRAFT", index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reopened_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    reopen_reason: Mapped[str | None] = mapped_column(Text)

    academic_year: Mapped[AcademicYear] = relationship(back_populates="terms")

    __table_args__ = (
        UniqueConstraint("academic_year_id", "name", name="uq_terms_year_name"),
        CheckConstraint("starts_on < ends_on", name="dates_ordered"),
        CheckConstraint("status IN ('DRAFT','ACTIVE','CLOSED')", name="status_valid"),
    )


class Department(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)

    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_departments_school_code"),)


class Grade(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "grades"

    department_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("departments.id"))
    code: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    band: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_grades_school_code"),
        CheckConstraint("band IN ('EARLY_CHILDHOOD','PRIMARY','JHS')", name="band_valid"),
    )


class ClassStream(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    """A grade instance within an academic year, e.g. Basic 4A in 2026/2027."""
    __tablename__ = "class_streams"

    grade_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("grades.id"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    section_label: Mapped[str] = mapped_column(String(8), nullable=False, default="A")
    capacity: Mapped[int | None] = mapped_column(Integer)

    grade: Mapped[Grade] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("grade_id", "academic_year_id", "section_label",
                         name="uq_class_streams_grade_year_section"),
    )


class Subject(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "subjects"

    code: Mapped[str] = mapped_column(String(24), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_subjects_school_code"),)


class GradeSubject(Base):
    __tablename__ = "grade_subjects"

    grade_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("grades.id", ondelete="CASCADE"), primary_key=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("subjects.id", ondelete="CASCADE"), primary_key=True)


class Student(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "students"

    admission_code: Mapped[str] = mapped_column(String(24), nullable=False)
    surname: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    other_names: Mapped[str] = mapped_column(String(160), nullable=False)
    gender: Mapped[str] = mapped_column(String(8), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    nationality: Mapped[str] = mapped_column(String(48), default="Ghanaian")
    religion: Mapped[str | None] = mapped_column(String(48))
    medical_notes: Mapped[str | None] = mapped_column(Text)  # restricted
    photo_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(String(16), default="APPLICANT", index=True)
    admitted_on: Mapped[date | None] = mapped_column(Date)

    __table_args__ = (
        UniqueConstraint("school_id", "admission_code", name="uq_students_school_admission_code"),
        CheckConstraint("gender IN ('F','M')", name="gender_valid"),
        CheckConstraint(
            "status IN ('APPLICANT','ADMITTED','ENROLLED','ACTIVE','PROMOTED','REPEATED',"
            "'WITHDRAWN','TRANSFERRED','SUSPENDED','GRADUATED')", name="status_valid"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.surname} {self.other_names}".strip()


class ParentGuardian(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "parent_guardians"

    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # +233…
    phone2: Mapped[str | None] = mapped_column(String(16))
    email: Mapped[str | None] = mapped_column(String(255))
    occupation: Mapped[str | None] = mapped_column(String(120))
    residential_address: Mapped[str | None] = mapped_column(Text)
    ghana_digital_address: Mapped[str | None] = mapped_column(String(40))  # distinct field
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6))
    comm_preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    sms_opt_out: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)

    # Phone format (+233XXXXXXXXX) is enforced by normalization at the service
    # layer (core.phones) — portable across SQLite (dev/test) and PostgreSQL (prod).


class ParentStudentRelationship(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "parent_student_relationships"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("parent_guardians.id"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(16), nullable=False)
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    is_billing_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(24), default="MANUAL")  # MANUAL|IMPORT|IMPORT_SUGGESTION
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)

    parent: Mapped[ParentGuardian] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("parent_id", "student_id", "relationship_type",
                         name="uq_parent_student_rel"),
        CheckConstraint(
            "relationship_type IN ('MOTHER','FATHER','GUARDIAN','GRANDPARENT','SIBLING','OTHER')",
            name="rel_type_valid"),
    )


class Teacher(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "teachers"

    staff_code: Mapped[str | None] = mapped_column(String(24))
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), unique=True)
    surname: Mapped[str] = mapped_column(String(80), nullable=False)
    other_names: Mapped[str] = mapped_column(String(160), nullable=False)
    gender: Mapped[str | None] = mapped_column(String(8))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(16))
    email: Mapped[str | None] = mapped_column(String(255))
    qualification: Mapped[str | None] = mapped_column(String(160))
    job_title: Mapped[str | None] = mapped_column(String(80))
    hired_on: Mapped[date | None] = mapped_column(Date)
    employment_status: Mapped[str] = mapped_column(String(16), default="ACTIVE")

    __table_args__ = (
        UniqueConstraint("school_id", "staff_code", name="uq_teachers_school_staff_code"),
        CheckConstraint("employment_status IN ('ACTIVE','ON_LEAVE','EXITED')", name="emp_valid"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.surname} {self.other_names}".strip()


class TeacherAssignment(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    """Drives all teacher resource scoping (REQ-MRK-01, REQ-TCH-02)."""
    __tablename__ = "teacher_assignments"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("teachers.id"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False, index=True)
    class_stream_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("class_streams.id"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("subjects.id"))
    role: Mapped[str] = mapped_column(String(24), default="SUBJECT_TEACHER")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    __table_args__ = (
        CheckConstraint("role IN ('SUBJECT_TEACHER','FORM_TEACHER')", name="role_valid"),
    )


class Enrollment(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "enrollments"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False, index=True)
    class_stream_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("class_streams.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)
    started_on: Mapped[date | None] = mapped_column(Date)
    ended_on: Mapped[date | None] = mapped_column(Date)
    is_repeat: Mapped[bool] = mapped_column(Boolean, default=False)
    promotion_decision_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)

    class_stream: Mapped[ClassStream] = relationship(lazy="selectin")

    __table_args__ = (
        Index("ix_enrollments_year_status", "academic_year_id", "status"),
        CheckConstraint("status IN ('ACTIVE','COMPLETED','WITHDRAWN','TRANSFERRED')",
                        name="status_valid"),
    )


class PromotionBatch(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "promotion_batches"

    from_academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False)
    to_academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")  # DRAFT|APPLIED|REVERSED
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("from_academic_year_id", "to_academic_year_id",
                         name="uq_promotion_batches_years"),
    )


class PromotionDecision(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "promotion_decisions"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("promotion_batches.id"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False)
    from_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False)
    to_class_stream_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("class_streams.id"))
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("batch_id", "student_id", name="uq_promotion_decisions_batch_student"),
        CheckConstraint(
            "decision IN ('PROMOTE','REPEAT','WITHDRAW','TRANSFER','GRADUATE')",
            name="decision_valid"),
    )


class DocumentSequence(Base, IdMixin):
    """Monotonic per-school counters (admission codes, receipt numbers…)."""
    __tablename__ = "document_sequences"

    school_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("schools.id"), nullable=False)
    key: Mapped[str] = mapped_column(String(32), nullable=False)
    prefix: Mapped[str] = mapped_column(String(12), default="")
    current_value: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "key", name="uq_document_sequences_school_key"),
    )
