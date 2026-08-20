"""Financial engine models: ledger, fees, payments, receipts, clearance (design §08).

Money is integer pesewas (1 GHS = 100). Ledger entries are append-only; the
application DB role gets no UPDATE/DELETE on ledger/receipt tables in prod.
"""
import uuid
from datetime import date, datetime

from sqlalchemy import (JSON, BigInteger, Boolean, CheckConstraint, Date, DateTime,
                        ForeignKey, Index, Integer, Numeric, String, Text,
                        UniqueConstraint, Uuid)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (ActorMixin, Base, IdMixin, SchoolScopedMixin,
                             TimestampMixin, utcnow)

FEE_TYPES = ("TUITION", "FEEDING", "ICT_LAB", "PTA_LEVY", "TRANSPORT", "EXAMINATION", "OTHER")
CHARGE_STATUSES = ("ACTIVE", "PART_SETTLED", "SETTLED", "ADJUSTED")
PAYMENT_METHODS = ("MTN_MOMO", "TELECEL_CASH", "AT_MONEY", "CASH", "BANK_TRANSFER", "OTHER")
PAYMENT_STATUSES = ("INITIATED", "PENDING", "CONFIRMED", "FAILED", "REVERSED", "REFUNDED")
ENTRY_TYPES = ("DEBIT", "CREDIT")
LEDGER_CATEGORIES = ("CHARGE", "PAYMENT", "WAIVER", "ADJUSTMENT", "REFUND",
                     "CREDIT_NOTE", "OPENING_BALANCE", "REVERSAL")
CLEARANCE_TYPES = ("REPORT_CARD", "EXAMINATION")
CLEARANCE_STATES = ("CLEAR", "BLOCKED", "WAIVED", "PAYMENT_PLAN",
                    "PENDING_RECONCILIATION", "MANUAL_OVERRIDE")


class FeeStructure(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "fee_structures"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    grade_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("grades.id"))
    band: Mapped[str | None] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")

    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','ACTIVE','ARCHIVED')", name="status_valid"),
        CheckConstraint("band IN ('EARLY_CHILDHOOD','PRIMARY','JHS') OR band IS NULL",
                        name="band_valid"),
    )


class FeeStructureItem(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "fee_structure_items"

    structure_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fee_structures.id", ondelete="CASCADE"),
        nullable=False, index=True)
    fee_type: Mapped[str] = mapped_column(String(24), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period: Mapped[str] = mapped_column(String(16), default="PER_TERM")
    term_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("terms.id"))

    __table_args__ = (
        CheckConstraint("amount_pesewas >= 0", name="amount_non_negative"),
        CheckConstraint("period IN ('PER_TERM','PER_YEAR','ONE_OFF')", name="period_valid"),
        CheckConstraint(
            "fee_type IN ('TUITION','FEEDING','ICT_LAB','PTA_LEVY','TRANSPORT',"
            "'EXAMINATION','OTHER')", name="fee_type_valid"),
    )


class FeeCharge(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    """A concrete charge on a student (from billing run, manual entry, or import)."""
    __tablename__ = "fee_charges"

    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False, index=True)
    term_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("terms.id"))
    fee_type: Mapped[str] = mapped_column(String(24), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    due_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)
    source: Mapped[str] = mapped_column(String(16), default="STRUCTURE")

    __table_args__ = (
        Index("ix_fee_charges_student_status", "student_id", "status"),
        CheckConstraint("amount_pesewas > 0", name="amount_positive"),
        CheckConstraint("status IN ('ACTIVE','PART_SETTLED','SETTLED','ADJUSTED')",
                        name="status_valid"),
        CheckConstraint("source IN ('STRUCTURE','MANUAL','OPENING')", name="source_valid"),
    )


class LedgerEntry(Base, IdMixin, SchoolScopedMixin, ActorMixin):
    """Append-only source of financial truth (REQ-FIN-01). Never updated or deleted;
    corrections are REVERSAL entries referencing the original (BR-F02)."""
    __tablename__ = "ledger_entries"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False)
    term_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("terms.id"))
    entry_type: Mapped[str] = mapped_column(String(8), nullable=False)
    category: Mapped[str] = mapped_column(String(24), nullable=False)
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    fee_charge_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("fee_charges.id"))
    payment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("payments.id"))
    waiver_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("waivers.id"))
    adjustment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("adjustments.id"))
    refund_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("refunds.id"))
    reversed_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ledger_entries.id"))
    idempotency_key: Mapped[str | None] = mapped_column(String(96), unique=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        Index("ix_ledger_entries_student_term", "student_id", "term_id"),
        Index("ix_ledger_entries_student_type", "student_id", "entry_type"),
        CheckConstraint("entry_type IN ('DEBIT','CREDIT')", name="entry_type_valid"),
        CheckConstraint("amount_pesewas > 0", name="amount_positive"),
        CheckConstraint(
            "category IN ('CHARGE','PAYMENT','WAIVER','ADJUSTMENT','REFUND','CREDIT_NOTE',"
            "'OPENING_BALANCE','REVERSAL')", name="category_valid"),
    )


class Waiver(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "waivers"

    fee_charge_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("fee_charges.id"))
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    term_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("terms.id"))
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # WAIVER|DISCOUNT|SCHOLARSHIP
    amount_pesewas: Mapped[int | None] = mapped_column(BigInteger)
    pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        CheckConstraint("kind IN ('WAIVER','DISCOUNT','SCHOLARSHIP')", name="kind_valid"),
        CheckConstraint("(amount_pesewas IS NOT NULL) != (pct IS NOT NULL)",
                        name="exactly_one_of_amount_pct"),
    )


class Adjustment(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "adjustments"

    fee_charge_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("fee_charges.id"))
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        CheckConstraint("direction IN ('DEBIT','CREDIT')", name="direction_valid"),
        CheckConstraint("amount_pesewas > 0", name="amount_positive"),
    )


class Refund(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "refunds"

    payment_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("payments.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authorized_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="APPROVED")

    __table_args__ = (
        CheckConstraint("status IN ('REQUESTED','APPROVED','PAID','REJECTED')",
                        name="status_valid"),
        CheckConstraint("amount_pesewas > 0", name="amount_positive"),
    )


class PaymentPlan(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "payment_plans"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("enrollments.id"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="APPROVED")
    approved_by: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "status IN ('PROPOSED','APPROVED','ON_TRACK','DEFAULTED','COMPLETED')",
            name="status_valid"),
    )


class PaymentPlanInstallment(Base, IdMixin, SchoolScopedMixin):
    __tablename__ = "payment_plan_installments"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("payment_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    due_on: Mapped[date] = mapped_column(Date, nullable=False)
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")

    __table_args__ = (
        CheckConstraint("status IN ('PENDING','PAID','MISSED')", name="status_valid"),
        CheckConstraint("amount_pesewas > 0", name="amount_positive"),
    )


class Payment(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "payments"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    enrollment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("enrollments.id"))
    term_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("terms.id"))
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(24), nullable=False)
    provider_code: Mapped[str | None] = mapped_column(String(32))
    provider_reference: Mapped[str | None] = mapped_column(String(96))
    payer_name: Mapped[str | None] = mapped_column(String(160))
    payer_phone: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(16), default="INITIATED", index=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    receipt_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("receipts.id"))

    __table_args__ = (
        CheckConstraint("amount_pesewas > 0", name="amount_positive"),
        CheckConstraint(
            "status IN ('INITIATED','PENDING','CONFIRMED','FAILED','REVERSED','REFUNDED')",
            name="status_valid"),
        CheckConstraint(
            "method IN ('MTN_MOMO','TELECEL_CASH','AT_MONEY','CASH','BANK_TRANSFER','OTHER')",
            name="method_valid"),
    )


class PaymentAllocation(Base, IdMixin, SchoolScopedMixin):
    __tablename__ = "payment_allocations"

    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_charge_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("fee_charges.id"), nullable=False, index=True)
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (CheckConstraint("amount_pesewas > 0", name="amount_positive"),)


class PaymentProviderConfig(Base, IdMixin, TimestampMixin, SchoolScopedMixin):
    __tablename__ = "payment_provider_configs"

    code: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    method: Mapped[str] = mapped_column(String(24), nullable=False)
    kind: Mapped[str] = mapped_column(String(8), default="STUB")  # STUB|LIVE
    webhook_secret_env: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_provider_configs_school_code"),
        CheckConstraint("kind IN ('STUB','LIVE')", name="kind_valid"),
    )


class WebhookEvent(Base, IdMixin, SchoolScopedMixin):
    __tablename__ = "webhook_events"

    provider_code: Mapped[str] = mapped_column(String(32), nullable=False)
    external_event_id: Mapped[str | None] = mapped_column(String(96))
    event_type: Mapped[str | None] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    signature_status: Mapped[str] = mapped_column(String(16), nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("payments.id"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    __table_args__ = (
        CheckConstraint("signature_status IN ('VALID','INVALID','MISSING')",
                        name="signature_status_valid"),
    )


class Receipt(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "receipts"

    receipt_no: Mapped[str] = mapped_column(String(24), nullable=False)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("payments.id"), unique=True, nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    payer_name: Mapped[str | None] = mapped_column(String(160))
    amount_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    method: Mapped[str] = mapped_column(String(24), nullable=False)
    issued_on: Mapped[date] = mapped_column(Date, nullable=False)
    transaction_ref: Mapped[str | None] = mapped_column(String(96))
    academic_year_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("academic_years.id"))
    term_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("terms.id"))
    balance_after_pesewas: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="ISSUED")
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    voided_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    void_reason: Mapped[str | None] = mapped_column(Text)
    pdf_file_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("stored_files.id"))

    __table_args__ = (
        UniqueConstraint("school_id", "receipt_no", name="uq_receipts_school_no"),
        CheckConstraint("status IN ('ISSUED','VOIDED')", name="status_valid"),
        CheckConstraint("amount_pesewas > 0", name="amount_positive"),
    )


class ClearancePolicy(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "clearance_policies"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False)
    term_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("terms.id"))
    clearance_type: Mapped[str] = mapped_column(String(16), nullable=False)
    mode: Mapped[str] = mapped_column(String(24), nullable=False)
    threshold: Mapped[int] = mapped_column(BigInteger, nullable=False)  # pct×100 or pesewas
    band: Mapped[str | None] = mapped_column(String(16))
    grade_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("grades.id"))

    __table_args__ = (
        CheckConstraint("clearance_type IN ('REPORT_CARD','EXAMINATION')", name="type_valid"),
        CheckConstraint("mode IN ('PERCENT_OF_CHARGES','FIXED_AMOUNT')", name="mode_valid"),
        CheckConstraint("threshold >= 0", name="threshold_non_negative"),
    )


class FinancialClearance(Base, IdMixin, TimestampMixin, SchoolScopedMixin, ActorMixin):
    __tablename__ = "financial_clearances"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("students.id"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("academic_years.id"), nullable=False)
    term_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("terms.id"), nullable=False)
    clearance_type: Mapped[str] = mapped_column(String(16), nullable=False)
    state: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    override_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    override_reason: Mapped[str | None] = mapped_column(Text)
    override_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_pesewas: Mapped[int] = mapped_column(BigInteger, default=0)
    charged_pesewas: Mapped[int] = mapped_column(BigInteger, default=0)

    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", "term_id", "clearance_type",
                         name="uq_financial_clearances_scope"),
        CheckConstraint(
            "state IN ('CLEAR','BLOCKED','WAIVED','PAYMENT_PLAN','PENDING_RECONCILIATION',"
            "'MANUAL_OVERRIDE')", name="state_valid"),
    )
