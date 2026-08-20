"""Append-only ledger: the single source of financial truth (REQ-FIN-01, BR-F).

Balances are derived (Σ DEBIT − Σ CREDIT); entries are immutable and corrections
are REVERSAL entries referencing the original (BR-F02). No `student.balance` column.
"""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.finance import FeeCharge, LedgerEntry


class LedgerIntegrityError(ConflictError):
    def __init__(self, message: str):
        super().__init__(message, code="LEDGER_INTEGRITY")


def post(db: Session, *, school_id: uuid.UUID, student_id: uuid.UUID,
         academic_year_id: uuid.UUID, entry_type: str, category: str,
         amount_pesewas: int, occurred_on: date, term_id: uuid.UUID | None = None,
         description: str | None = None, fee_charge_id: uuid.UUID | None = None,
         payment_id: uuid.UUID | None = None, waiver_id: uuid.UUID | None = None,
         adjustment_id: uuid.UUID | None = None, refund_id: uuid.UUID | None = None,
         reversed_entry_id: uuid.UUID | None = None,
         idempotency_key: str | None = None,
         actor_id: uuid.UUID | None = None,
         request: Request | None = None, quiet: bool = False) -> LedgerEntry:
    """Insert one immutable ledger entry. `quiet` skips audit (callers with their
    own domain audit event — e.g. payment confirmation — set this)."""
    if amount_pesewas <= 0:
        raise LedgerIntegrityError("Ledger amounts must be positive; sign comes from entry_type.")
    if category == "REVERSAL" and reversed_entry_id is None:
        raise LedgerIntegrityError("REVERSAL entries must reference the original entry.")
    if idempotency_key is not None:
        existing = db.scalar(select(LedgerEntry).where(
            LedgerEntry.idempotency_key == idempotency_key))
        if existing is not None:
            return existing  # duplicate webhook/retry → same entry, no double post (BR-F10)
    entry = LedgerEntry(
        id=uuid7(), school_id=school_id, student_id=student_id,
        academic_year_id=academic_year_id, term_id=term_id, entry_type=entry_type,
        category=category, amount_pesewas=int(amount_pesewas), occurred_on=occurred_on,
        description=description, fee_charge_id=fee_charge_id, payment_id=payment_id,
        waiver_id=waiver_id, adjustment_id=adjustment_id, refund_id=refund_id,
        reversed_entry_id=reversed_entry_id, idempotency_key=idempotency_key,
        created_by=actor_id)
    db.add(entry)
    db.flush()
    if not quiet:
        audit(db, actor_id=actor_id, action="ledger.posted", entity_type="ledger_entry",
              entity_id=entry.id,
              new={"type": entry_type, "category": category,
                   "amount_pesewas": int(amount_pesewas),
                   "student_id": str(student_id)}, request=request)
    return entry


def reverse(db: Session, entry: LedgerEntry, *, reason: str, actor_id: uuid.UUID,
            occurred_on: date, request: Request | None = None) -> LedgerEntry:
    """Counter-entry correction — the original is never touched (BR-F02/F08)."""
    if entry.category == "REVERSAL":
        raise LedgerIntegrityError("A reversal cannot itself be reversed; reverse the original.")
    counter_type = "CREDIT" if entry.entry_type == "DEBIT" else "DEBIT"
    counter = post(db, school_id=entry.school_id, student_id=entry.student_id,
                   academic_year_id=entry.academic_year_id, term_id=entry.term_id,
                   entry_type=counter_type, category="REVERSAL",
                   amount_pesewas=entry.amount_pesewas, occurred_on=occurred_on,
                   description=f"Reversal: {reason[:120]}",
                   fee_charge_id=entry.fee_charge_id, payment_id=entry.payment_id,
                   reversed_entry_id=entry.id, actor_id=actor_id, request=request)
    audit(db, actor_id=actor_id, action="ledger.reversed", entity_type="ledger_entry",
          entity_id=entry.id,
          previous={"type": entry.entry_type, "category": entry.category,
                    "amount_pesewas": int(entry.amount_pesewas)},
          new={"counter_entry_id": str(counter.id)}, reason=reason, request=request)
    return counter


def get_entry(db: Session, school_id: uuid.UUID, entry_id: uuid.UUID) -> LedgerEntry:
    e = db.get(LedgerEntry, entry_id)
    if e is None or e.school_id != school_id:
        raise NotFoundError("Ledger entry not found.")
    return e


def _sum(db: Session, stmt) -> int:
    return int(db.scalar(stmt) or 0)


def balance(db: Session, student_id: uuid.UUID, *,
            academic_year_id: uuid.UUID | None = None,
            term_id: uuid.UUID | None = None) -> int:
    """Derived balance in pesewas (positive = owing). Never stored (REQ-FIN-01)."""
    debits = select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
        LedgerEntry.student_id == student_id, LedgerEntry.entry_type == "DEBIT")
    credits_ = select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
        LedgerEntry.student_id == student_id, LedgerEntry.entry_type == "CREDIT")
    for stmt in (debits, credits_):
        if academic_year_id is not None:
            stmt = stmt.where(LedgerEntry.academic_year_id == academic_year_id)
        if term_id is not None:
            stmt = stmt.where(LedgerEntry.term_id == term_id)
    # rebuild with filters applied consistently
    def filtered(entry_type: str):
        s = select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
            LedgerEntry.student_id == student_id, LedgerEntry.entry_type == entry_type)
        if academic_year_id is not None:
            s = s.where(LedgerEntry.academic_year_id == academic_year_id)
        if term_id is not None:
            s = s.where(LedgerEntry.term_id == term_id)
        return s
    return _sum(db, filtered("DEBIT")) - _sum(db, filtered("CREDIT"))


def entries_for(db: Session, student_id: uuid.UUID, *,
                academic_year_id: uuid.UUID | None = None, limit: int = 100) -> list[LedgerEntry]:
    stmt = select(LedgerEntry).where(LedgerEntry.student_id == student_id)
    if academic_year_id is not None:
        stmt = stmt.where(LedgerEntry.academic_year_id == academic_year_id)
    return list(db.scalars(stmt.order_by(LedgerEntry.occurred_at.desc()).limit(limit)).all())


def term_totals(db: Session, student_id: uuid.UUID, term_id: uuid.UUID) -> dict:
    """Charged vs settled for one term — feeds clearance evaluation."""
    charged = db.scalar(select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
        LedgerEntry.student_id == student_id, LedgerEntry.term_id == term_id,
        LedgerEntry.entry_type == "DEBIT",
        LedgerEntry.category.in_(("CHARGE", "OPENING_BALANCE", "ADJUSTMENT")))) or 0
    settled = db.scalar(select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
        LedgerEntry.student_id == student_id, LedgerEntry.term_id == term_id,
        LedgerEntry.entry_type == "CREDIT",
        LedgerEntry.category.in_(("PAYMENT", "WAIVER", "ADJUSTMENT")))) or 0
    # reversals net out: subtract reversed amounts from each side
    reversed_debits = db.scalar(select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
        LedgerEntry.student_id == student_id, LedgerEntry.term_id == term_id,
        LedgerEntry.category == "REVERSAL", LedgerEntry.entry_type == "DEBIT")) or 0
    reversed_credits = db.scalar(select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
        LedgerEntry.student_id == student_id, LedgerEntry.term_id == term_id,
        LedgerEntry.category == "REVERSAL", LedgerEntry.entry_type == "CREDIT")) or 0
    return {"charged_pesewas": int(charged) - int(reversed_debits),
            "settled_pesewas": int(settled) - int(reversed_credits)}


def refresh_charge_status(db: Session, charge: FeeCharge) -> None:
    from app.models.finance import PaymentAllocation
    allocated = db.scalar(select(func.coalesce(
        func.sum(PaymentAllocation.amount_pesewas), 0)).where(
        PaymentAllocation.fee_charge_id == charge.id)) or 0
    waived = db.scalar(select(func.coalesce(func.sum(LedgerEntry.amount_pesewas), 0)).where(
        LedgerEntry.fee_charge_id == charge.id,
        LedgerEntry.category == "WAIVER", LedgerEntry.entry_type == "CREDIT")) or 0
    covered = int(allocated) + int(waived)
    if covered >= charge.amount_pesewas:
        charge.status = "SETTLED"
    elif covered > 0:
        charge.status = "PART_SETTLED"
    else:
        charge.status = "ACTIVE"
