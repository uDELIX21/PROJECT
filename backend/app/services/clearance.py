"""Financial clearance: configurable policies, derived states, audited overrides
(REQ-CLR-01, BR-F11). Replaces the Phase-4 stub used by report publication."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.base import utcnow
from app.models.core import ClassStream, Enrollment, Grade, Student, Term
from app.models.finance import (ClearancePolicy, FinancialClearance, Payment,
                                PaymentPlan)

HUMAN_STATES = ("WAIVED", "PAYMENT_PLAN", "MANUAL_OVERRIDE")
PASS_STATES = ("CLEAR", "WAIVED", "MANUAL_OVERRIDE")


# --------------------------------------------------------------------------- policies

def create_policy(db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID,
                  clearance_type: str, mode: str, threshold: int,
                  term_id: uuid.UUID | None = None, band: str | None = None,
                  grade_id: uuid.UUID | None = None, actor_id: uuid.UUID | None = None,
                  request: Request | None = None) -> ClearancePolicy:
    if clearance_type not in ("REPORT_CARD", "EXAMINATION"):
        raise ConflictError("Invalid clearance type.", code="TYPE_INVALID")
    if mode not in ("PERCENT_OF_CHARGES", "FIXED_AMOUNT"):
        raise ConflictError("Invalid policy mode.", code="MODE_INVALID")
    if mode == "PERCENT_OF_CHARGES" and not (0 <= threshold <= 10000):
        raise ConflictError("Percentage threshold is basis points 0–10000 (100% = 10000).",
                            code="THRESHOLD_INVALID")
    policy = ClearancePolicy(id=uuid7(), school_id=school_id,
                             academic_year_id=academic_year_id, term_id=term_id,
                             clearance_type=clearance_type, mode=mode,
                             threshold=int(threshold), band=band, grade_id=grade_id,
                             created_by=actor_id)
    db.add(policy)
    audit(db, actor_id=actor_id, action="clearance_policy.created",
          entity_type="clearance_policy", entity_id=policy.id,
          new={"type": clearance_type, "mode": mode, "threshold": int(threshold)},
          request=request)
    db.flush()
    return policy


def resolve_policy(db: Session, *, school_id: uuid.UUID, term: Term,
                   clearance_type: str, grade: Grade) -> ClearancePolicy | None:
    """Most specific wins: (term+grade) → (term+band) → term-wide → year-wide."""
    def q(**kw):
        stmt = select(ClearancePolicy).where(
            ClearancePolicy.school_id == school_id,
            ClearancePolicy.clearance_type == clearance_type)
        for k, v in kw.items():
            col = getattr(ClearancePolicy, k)
            stmt = stmt.where(col == v) if v is not None else stmt.where(col.is_(None))
        return db.scalar(stmt.limit(1))
    return (q(term_id=term.id, grade_id=grade.id)
            or q(term_id=term.id, band=grade.band, grade_id=None)
            or q(term_id=term.id, band=None, grade_id=None)
            or q(term_id=None, grade_id=None, band=None,
                 academic_year_id=term.academic_year_id))


# --------------------------------------------------------------------------- evaluation

def evaluate(db: Session, *, school_id: uuid.UUID, student_id: uuid.UUID,
             term_id: uuid.UUID, clearance_type: str = "REPORT_CARD") -> dict:
    """Compute the clearance state for a student/term/type.

    Rules (design §08.3): computed CLEAR wins over everything; pending e-payments
    force PENDING_RECONCILIATION; human overrides (WAIVED/PAYMENT_PLAN/
    MANUAL_OVERRIDE) persist while unpaid; otherwise BLOCKED.
    """
    from app.services import ledger as ledger_svc
    term = db.get(Term, term_id)
    if term is None or term.school_id != school_id:
        raise NotFoundError("Term not found.")
    enrollment = db.scalar(select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.academic_year_id == term.academic_year_id,
        Enrollment.status.in_(("ACTIVE", "COMPLETED"))).limit(1))
    if enrollment is None:
        return {"type": clearance_type, "state": "BLOCKED",
                "note": "No enrollment for this year.", "paid_pesewas": 0,
                "charged_pesewas": 0}
    stream = db.get(ClassStream, enrollment.class_stream_id)
    grade = db.get(Grade, stream.grade_id)

    totals = ledger_svc.term_totals(db, student_id, term_id)
    charged, settled = totals["charged_pesewas"], totals["settled_pesewas"]
    pending_payments = db.scalar(select(Payment.id).where(
        Payment.student_id == student_id, Payment.status == "PENDING").limit(1))

    row = db.scalar(select(FinancialClearance).where(
        FinancialClearance.student_id == student_id,
        FinancialClearance.academic_year_id == term.academic_year_id,
        FinancialClearance.term_id == term_id,
        FinancialClearance.clearance_type == clearance_type))

    if charged <= 0:
        state = "CLEAR"  # nothing billed ⇒ nothing gates
    elif pending_payments is not None:
        state = "PENDING_RECONCILIATION"
    else:
        policy = resolve_policy(db, school_id=school_id, term=term,
                                clearance_type=clearance_type, grade=grade)
        if policy is None:
            state = "CLEAR"  # no policy configured ⇒ no gate (configurable by design)
        elif policy.mode == "PERCENT_OF_CHARGES":
            required = charged * int(policy.threshold) / 10000.0
            state = "CLEAR" if settled >= required else "BLOCKED"
        else:  # FIXED_AMOUNT
            state = "CLEAR" if settled >= int(policy.threshold) else "BLOCKED"

    # human states persist unless the student is now fully clear
    if row is not None and state != "CLEAR" and row.state in HUMAN_STATES \
            and row.override_by is not None:
        state = row.state

    if row is None:
        row = FinancialClearance(id=uuid7(), school_id=school_id, student_id=student_id,
                                 academic_year_id=term.academic_year_id, term_id=term_id,
                                 clearance_type=clearance_type, state=state)
        db.add(row)
    previous = row.state
    row.state = state
    row.computed_at = utcnow()
    row.paid_pesewas = max(settled, 0)
    row.charged_pesewas = max(charged, 0)
    if state == "CLEAR" and previous in HUMAN_STATES:
        row.override_by = None  # condition met on its own now
    db.flush()
    return {"type": clearance_type, "state": state, "paid_pesewas": row.paid_pesewas,
            "charged_pesewas": row.charged_pesewas,
            "override_reason": row.override_reason if state in HUMAN_STATES else None}


def override(db: Session, *, school_id: uuid.UUID, student_id: uuid.UUID,
             term_id: uuid.UUID, clearance_type: str, state: str, reason: str,
             actor_id: uuid.UUID, request: Request | None = None) -> FinancialClearance:
    """Manual override — WAIVED / MANUAL_OVERRIDE with mandatory reason (BR-F11)."""
    if state not in ("WAIVED", "MANUAL_OVERRIDE", "PAYMENT_PLAN"):
        raise ConflictError("Overrides may only set WAIVED, PAYMENT_PLAN or MANUAL_OVERRIDE.",
                            code="OVERRIDE_STATE_INVALID")
    if not reason or not reason.strip():
        raise ConflictError("A reason is required for clearance overrides.",
                            code="REASON_REQUIRED")
    term = db.get(Term, term_id)
    if term is None or term.school_id != school_id:
        raise NotFoundError("Term not found.")
    # materialize the computed state first so the audit "previous" reflects
    # reality (BLOCKED/PENDING/…) even on the first override for this scope
    evaluate(db, school_id=school_id, student_id=student_id, term_id=term_id,
             clearance_type=clearance_type)
    row = db.scalar(select(FinancialClearance).where(
        FinancialClearance.student_id == student_id,
        FinancialClearance.academic_year_id == term.academic_year_id,
        FinancialClearance.term_id == term_id,
        FinancialClearance.clearance_type == clearance_type))
    previous = row.state
    row.state = state
    row.override_by = actor_id
    row.override_reason = reason.strip()
    row.override_at = utcnow()
    audit(db, actor_id=actor_id, action="clearance.overridden",
          entity_type="financial_clearance", entity_id=row.id,
          previous={"state": previous}, new={"state": state},
          reason=reason.strip(), request=request)
    db.flush()
    return row


def active_plan(db: Session, student_id: uuid.UUID, term_id: uuid.UUID) -> PaymentPlan | None:
    plan = db.scalar(select(PaymentPlan).where(
        PaymentPlan.student_id == student_id, PaymentPlan.term_id == term_id,
        PaymentPlan.status.in_(("APPROVED", "ON_TRACK"))).limit(1))
    return plan
