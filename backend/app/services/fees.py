"""Fee structures, billing runs, charges, waivers, adjustments, plans (design §08)."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.core import Enrollment, Grade, Student, Term
from app.models.finance import (Adjustment, FeeCharge, FeeStructure, FeeStructureItem,
                                LedgerEntry, PaymentPlan, PaymentPlanInstallment, Waiver)
from app.services import ledger

FEE_TYPES = ("TUITION", "FEEDING", "ICT_LAB", "PTA_LEVY", "TRANSPORT", "EXAMINATION", "OTHER")


# --------------------------------------------------------------------------- structures

def create_structure(db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID,
                     name: str, items: list[dict], grade_id: uuid.UUID | None = None,
                     band: str | None = None, actor_id: uuid.UUID | None = None,
                     request: Request | None = None) -> FeeStructure:
    if grade_id is None and band is None:
        raise ConflictError("A fee structure must target a grade or a band.",
                            code="STRUCTURE_SCOPE_REQUIRED")
    if not items:
        raise ConflictError("At least one fee item is required.", code="NO_ITEMS")
    for it in items:
        if it["fee_type"] not in FEE_TYPES:
            raise ConflictError(f"Unknown fee type {it['fee_type']}.", code="FEE_TYPE_INVALID")
        if int(it["amount_pesewas"]) < 0:
            raise ConflictError("Amounts must be non-negative.", code="AMOUNT_INVALID")
    structure = FeeStructure(id=uuid7(), school_id=school_id,
                             academic_year_id=academic_year_id, name=name,
                             grade_id=grade_id, band=band, created_by=actor_id)
    db.add(structure)
    db.flush()
    for it in items:
        db.add(FeeStructureItem(id=uuid7(), school_id=school_id, structure_id=structure.id,
                                fee_type=it["fee_type"],
                                display_name=it.get("display_name") or it["fee_type"].title(),
                                amount_pesewas=int(it["amount_pesewas"]),
                                period=it.get("period", "PER_TERM"),
                                term_id=it.get("term_id")))
    audit(db, actor_id=actor_id, action="fee_structure.created", entity_type="fee_structure",
          entity_id=structure.id, new={"name": name, "items": len(items)}, request=request)
    db.flush()
    return structure


def structures_for(db: Session, school_id: uuid.UUID,
                   academic_year_id: uuid.UUID) -> list[FeeStructure]:
    return list(db.scalars(select(FeeStructure).where(
        FeeStructure.school_id == school_id,
        FeeStructure.academic_year_id == academic_year_id,
        FeeStructure.status == "ACTIVE")).all())


def items_for(db: Session, structure_id: uuid.UUID) -> list[FeeStructureItem]:
    return list(db.scalars(select(FeeStructureItem).where(
        FeeStructureItem.structure_id == structure_id)).all())


def resolve_structure(db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID,
                      grade_id: uuid.UUID, band: str) -> FeeStructure | None:
    """Grade-specific wins over band-wide; newest-created wins within a scope
    (a replacement structure supersedes its predecessor)."""
    s = db.scalar(select(FeeStructure).where(
        FeeStructure.school_id == school_id,
        FeeStructure.academic_year_id == academic_year_id,
        FeeStructure.grade_id == grade_id, FeeStructure.status == "ACTIVE")
        .order_by(FeeStructure.created_at.desc()).limit(1))
    if s is not None:
        return s
    return db.scalar(select(FeeStructure).where(
        FeeStructure.school_id == school_id,
        FeeStructure.academic_year_id == academic_year_id,
        FeeStructure.band == band, FeeStructure.grade_id.is_(None),
        FeeStructure.status == "ACTIVE")
        .order_by(FeeStructure.created_at.desc()).limit(1))


# --------------------------------------------------------------------------- billing

def _term_fee_items(db: Session, structure_id: uuid.UUID, term_id: uuid.UUID):
    items = items_for(db, structure_id)
    out = []
    for it in items:
        if it.period == "PER_TERM" and (it.term_id is None or str(it.term_id) == str(term_id)):
            out.append(it)
    return out


def preview_billing(db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID,
                    term_id: uuid.UUID) -> list[dict]:
    term = db.get(Term, term_id)
    if term is None or str(term.academic_year_id) != str(academic_year_id):
        raise NotFoundError("Term not found for that academic year.")
    from app.models.core import ClassStream
    enrollments = db.execute(
        select(Enrollment, Student, Grade)
        .join(Student, Enrollment.student_id == Student.id)
        .join(ClassStream, Enrollment.class_stream_id == ClassStream.id)
        .join(Grade, ClassStream.grade_id == Grade.id)
        .where(Enrollment.academic_year_id == academic_year_id,
               Enrollment.status.in_(("ACTIVE", "COMPLETED")))).all()
    out = []
    for enrollment, student, grade in enrollments:
        structure = resolve_structure(db, school_id=school_id,
                                      academic_year_id=academic_year_id,
                                      grade_id=grade.id, band=grade.band)
        if structure is None:
            continue
        rows = []
        for it in _term_fee_items(db, structure.id, term_id):
            exists = db.scalar(select(FeeCharge).where(
                FeeCharge.enrollment_id == enrollment.id, FeeCharge.term_id == term_id,
                FeeCharge.fee_type == it.fee_type, FeeCharge.source == "STRUCTURE"))
            rows.append({"fee_type": it.fee_type, "display_name": it.display_name,
                         "amount_pesewas": int(it.amount_pesewas),
                         "already_charged": exists is not None})
        if rows:
            out.append({"student_id": str(student.id), "student_name": student.full_name,
                        "admission_code": student.admission_code,
                        "enrollment_id": str(enrollment.id),
                        "grade": grade.name, "charges": rows})
    return out


def apply_billing(db: Session, *, school_id: uuid.UUID, academic_year_id: uuid.UUID,
                  term_id: uuid.UUID, actor_id: uuid.UUID,
                  request: Request | None = None) -> dict:
    """Create charges + CHARGE debits for every eligible enrollment (idempotent)."""
    preview = preview_billing(db, school_id=school_id, academic_year_id=academic_year_id,
                              term_id=term_id)
    term = db.get(Term, term_id)
    created = skipped = 0
    for row in preview:
        for ch in row["charges"]:
            if ch["already_charged"]:
                skipped += 1
                continue
            charge = FeeCharge(id=uuid7(), school_id=school_id,
                               enrollment_id=uuid.UUID(row["enrollment_id"]),
                               student_id=uuid.UUID(row["student_id"]),
                               academic_year_id=academic_year_id, term_id=term_id,
                               fee_type=ch["fee_type"], display_name=ch["display_name"],
                               amount_pesewas=ch["amount_pesewas"],
                               due_on=term.starts_on, source="STRUCTURE",
                               created_by=actor_id)
            db.add(charge)
            db.flush()
            ledger.post(db, school_id=school_id, student_id=charge.student_id,
                        academic_year_id=academic_year_id, term_id=term_id,
                        entry_type="DEBIT", category="CHARGE",
                        amount_pesewas=charge.amount_pesewas, occurred_on=date.today(),
                        description=ch["display_name"], fee_charge_id=charge.id,
                        idempotency_key=f"billing:{charge.id}", actor_id=actor_id,
                        request=request, quiet=True)
            created += 1
    audit(db, actor_id=actor_id, action="billing.applied", entity_type="billing_run",
          entity_id=str(term_id), new={"created": created, "skipped": skipped},
          request=request)
    db.flush()
    return {"created": created, "skipped_existing": skipped}


# --------------------------------------------------------------------------- charges

def add_manual_charge(db: Session, *, school_id: uuid.UUID, enrollment: Enrollment,
                      fee_type: str, display_name: str, amount_pesewas: int,
                      term_id: uuid.UUID | None, actor_id: uuid.UUID,
                      request: Request | None = None) -> FeeCharge:
    if fee_type not in FEE_TYPES:
        raise ConflictError(f"Unknown fee type {fee_type}.", code="FEE_TYPE_INVALID")
    if amount_pesewas <= 0:
        raise ConflictError("Charge amount must be positive.", code="AMOUNT_INVALID")
    charge = FeeCharge(id=uuid7(), school_id=school_id, enrollment_id=enrollment.id,
                       student_id=enrollment.student_id,
                       academic_year_id=enrollment.academic_year_id, term_id=term_id,
                       fee_type=fee_type, display_name=display_name,
                       amount_pesewas=amount_pesewas, due_on=date.today(),
                       source="MANUAL", created_by=actor_id)
    db.add(charge)
    db.flush()
    ledger.post(db, school_id=school_id, student_id=enrollment.student_id,
                academic_year_id=enrollment.academic_year_id, term_id=term_id,
                entry_type="DEBIT", category="CHARGE", amount_pesewas=amount_pesewas,
                occurred_on=date.today(), description=display_name,
                fee_charge_id=charge.id, idempotency_key=f"charge:{charge.id}",
                actor_id=actor_id, request=request, quiet=True)
    audit(db, actor_id=actor_id, action="charge.manual", entity_type="fee_charge",
          entity_id=charge.id,
          new={"fee_type": fee_type, "amount_pesewas": amount_pesewas}, request=request)
    return charge


def opening_balance(db: Session, *, school_id: uuid.UUID, enrollment: Enrollment,
                    amount_pesewas: int, actor_id: uuid.UUID, occurred_on: date,
                    note: str | None = None, request: Request | None = None) -> LedgerEntry:
    """Imported/setup opening debt (BR-F12, AM9)."""
    if amount_pesewas <= 0:
        raise ConflictError("Opening balance must be positive.", code="AMOUNT_INVALID")
    return ledger.post(db, school_id=school_id, student_id=enrollment.student_id,
                       academic_year_id=enrollment.academic_year_id,
                       entry_type="DEBIT", category="OPENING_BALANCE",
                       amount_pesewas=amount_pesewas, occurred_on=occurred_on,
                       description=note or "Opening balance",
                       idempotency_key=f"opening:{enrollment.id}",
                       actor_id=actor_id, request=request)


# --------------------------------------------------------------------------- waivers & adjustments

def grant_waiver(db: Session, *, school_id: uuid.UUID, enrollment: Enrollment,
                 kind: str, amount_pesewas: int | None, pct: float | None, reason: str,
                 approver_id: uuid.UUID, term_id: uuid.UUID | None = None,
                 fee_charge_id: uuid.UUID | None = None,
                 request: Request | None = None) -> Waiver:
    if kind not in ("WAIVER", "DISCOUNT", "SCHOLARSHIP"):
        raise ConflictError("Invalid waiver kind.", code="KIND_INVALID")
    if (amount_pesewas is None) == (pct is None):
        raise ConflictError("Provide exactly one of amount or percentage.",
                            code="WAIVER_AMOUNT_REQUIRED")
    if pct is not None:
        # resolve amount from the student's charged total for the term
        if term_id is None:
            raise ConflictError("Percentage waivers need a term.", code="TERM_REQUIRED")
        totals = ledger.term_totals(db, enrollment.student_id, term_id)
        amount_pesewas = int(totals["charged_pesewas"] * float(pct) / 100)
        if amount_pesewas <= 0:
            raise ConflictError("Nothing to waive for this term.", code="NOTHING_TO_WAIVE")
        resolved = int(amount_pesewas)
        amount_pesewas = None  # store pct only; ledger carries the resolved amount
    else:
        resolved = int(amount_pesewas)
    waiver = Waiver(id=uuid7(), school_id=school_id, fee_charge_id=fee_charge_id,
                    enrollment_id=enrollment.id, student_id=enrollment.student_id,
                    term_id=term_id, kind=kind, amount_pesewas=amount_pesewas,
                    pct=pct, reason=reason, approved_by=approver_id, created_by=approver_id)
    db.add(waiver)
    db.flush()
    ledger.post(db, school_id=school_id, student_id=enrollment.student_id,
                academic_year_id=enrollment.academic_year_id, term_id=term_id,
                entry_type="CREDIT", category="WAIVER", amount_pesewas=resolved,
                occurred_on=date.today(), description=f"{kind.title()}: {reason[:80]}",
                fee_charge_id=fee_charge_id, waiver_id=waiver.id,
                idempotency_key=f"waiver:{waiver.id}", actor_id=approver_id,
                request=request, quiet=True)
    audit(db, actor_id=approver_id, action="waiver.granted", entity_type="waiver",
          entity_id=waiver.id,
          new={"kind": kind, "amount_pesewas": resolved, "pct": pct},
          reason=reason, request=request)
    waiver._resolved_amount = resolved
    return waiver


def add_adjustment(db: Session, *, school_id: uuid.UUID, enrollment: Enrollment,
                   direction: str, amount_pesewas: int, reason: str,
                   approver_id: uuid.UUID, term_id: uuid.UUID | None = None,
                   request: Request | None = None) -> Adjustment:
    if direction not in ("DEBIT", "CREDIT"):
        raise ConflictError("Invalid adjustment direction.", code="DIRECTION_INVALID")
    if amount_pesewas <= 0:
        raise ConflictError("Adjustment amount must be positive.", code="AMOUNT_INVALID")
    adj = Adjustment(id=uuid7(), school_id=school_id, enrollment_id=enrollment.id,
                     student_id=enrollment.student_id, direction=direction,
                     amount_pesewas=amount_pesewas, reason=reason,
                     approved_by=approver_id, created_by=approver_id)
    db.add(adj)
    db.flush()
    ledger.post(db, school_id=school_id, student_id=enrollment.student_id,
                academic_year_id=enrollment.academic_year_id, term_id=term_id,
                entry_type=direction, category="ADJUSTMENT", amount_pesewas=amount_pesewas,
                occurred_on=date.today(), description=f"Adjustment: {reason[:80]}",
                adjustment_id=adj.id, idempotency_key=f"adjustment:{adj.id}",
                actor_id=approver_id, request=request, quiet=True)
    audit(db, actor_id=approver_id, action="adjustment.added", entity_type="adjustment",
          entity_id=adj.id,
          new={"direction": direction, "amount_pesewas": amount_pesewas},
          reason=reason, request=request)
    return adj


# --------------------------------------------------------------------------- payment plans

def create_plan(db: Session, *, school_id: uuid.UUID, enrollment: Enrollment,
                term_id: uuid.UUID, installments: list[dict], approver_id: uuid.UUID,
                note: str | None = None, request: Request | None = None) -> PaymentPlan:
    if not installments:
        raise ConflictError("A plan needs at least one installment.", code="NO_INSTALLMENTS")
    plan = PaymentPlan(id=uuid7(), school_id=school_id, student_id=enrollment.student_id,
                       enrollment_id=enrollment.id, term_id=term_id, status="APPROVED",
                       approved_by=approver_id, note=note, created_by=approver_id)
    db.add(plan)
    db.flush()
    for inst in installments:
        db.add(PaymentPlanInstallment(id=uuid7(), school_id=school_id, plan_id=plan.id,
                                      due_on=inst["due_on"],
                                      amount_pesewas=int(inst["amount_pesewas"])))
    audit(db, actor_id=approver_id, action="payment_plan.created", entity_type="payment_plan",
          entity_id=plan.id, new={"installments": len(installments)}, request=request)
    db.flush()
    return plan


def plan_state(db: Session, plan: PaymentPlan) -> str:
    installments = db.scalars(select(PaymentPlanInstallment).where(
        PaymentPlanInstallment.plan_id == plan.id)).all()
    if all(i.status == "PAID" for i in installments):
        return "COMPLETED"
    today = date.today()
    if any(i.status == "PENDING" and i.due_on < today for i in installments):
        return "DEFAULTED"
    return plan.status if plan.status in ("APPROVED", "ON_TRACK") else "APPROVED"
