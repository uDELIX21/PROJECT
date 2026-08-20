"""Payment processing: provider abstraction, webhook verification + idempotent apply,
allocations, receipts, reversals/refunds (REQ-PAY-*, BR-F05..F10, design §08)."""
import hashlib
import hmac
import json
import os
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.core import Enrollment, Student, Term
from app.models.finance import (FeeCharge, Payment, PaymentAllocation,
                                PaymentProviderConfig, Receipt, Refund, WebhookEvent)
from app.services import ledger, receipts as receipts_svc


# --------------------------------------------------------------------------- providers

class PaymentProvider:
    """Adapter interface — stubs now, aggregators later without core changes."""
    code = "base"
    method = "OTHER"

    def initiate(self, payment: Payment) -> dict:
        raise NotImplementedError

    def webhook_signature_ok(self, headers: dict, body: bytes, secret: str) -> bool:
        raise NotImplementedError


class StubMoMoProvider(PaymentProvider):
    """Simulated mobile-money provider (clearly labelled — Agent Rule 20).

    Issues a provider reference immediately; the simulator (or tests) then POSTs
    signed webhooks to /payments/webhooks/{code} exercising the exact same
    verification/idempotency path a live aggregator would.
    """
    def __init__(self, code: str, method: str):
        self.code = code
        self.method = method

    def initiate(self, payment: Payment) -> dict:
        ref = f"SIM-{self.method[:4]}-{str(payment.id)[:13].upper()}"
        return {"provider_reference": ref,
                "note": f"Simulated {self.method} prompt issued (test mode)"}

    def webhook_signature_ok(self, headers: dict, body: bytes, secret: str) -> bool:
        supplied = headers.get("x-webhook-signature", "")
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(supplied, expected)


PROVIDERS: dict[str, PaymentProvider] = {
    "MTN_MOMO_STUB": StubMoMoProvider("MTN_MOMO_STUB", "MTN_MOMO"),
    "TELECEL_CASH_STUB": StubMoMoProvider("TELECEL_CASH_STUB", "TELECEL_CASH"),
    "AT_MONEY_STUB": StubMoMoProvider("AT_MONEY_STUB", "AT_MONEY"),
}


def provider_for(db: Session, school_id: uuid.UUID, code: str) -> PaymentProviderConfig:
    cfg = db.scalar(select(PaymentProviderConfig).where(
        PaymentProviderConfig.school_id == school_id, PaymentProviderConfig.code == code))
    if cfg is None:
        raise NotFoundError("Payment provider not configured.", code="PROVIDER_UNKNOWN")
    return cfg


def provider_secret(cfg: PaymentProviderConfig) -> str:
    """Secrets come from the environment — never stored in the DB (REQ-SEC-02)."""
    return os.environ.get(cfg.webhook_secret_env, "dev-webhook-secret")


def ensure_default_providers(db: Session, school_id: uuid.UUID) -> None:
    for code, p in PROVIDERS.items():
        exists = db.scalar(select(PaymentProviderConfig).where(
            PaymentProviderConfig.school_id == school_id,
            PaymentProviderConfig.code == code))
        if exists is None:
            db.add(PaymentProviderConfig(id=uuid7(), school_id=school_id, code=code,
                                         display_name=code.replace("_", " ").title(),
                                         method=p.method, kind="STUB",
                                         webhook_secret_env="SMS_WEBHOOK_SECRET"))
    db.flush()


# --------------------------------------------------------------------------- initiate

def initiate_payment(db: Session, *, school: "object", school_id: uuid.UUID,
                     student_id: uuid.UUID, amount_pesewas: int, method: str,
                     term_id: uuid.UUID | None = None, payer_name: str | None = None,
                     payer_phone: str | None = None, actor_id: uuid.UUID | None = None,
                     request: Request | None = None) -> Payment:
    if amount_pesewas <= 0:
        raise ConflictError("Amount must be positive.", code="AMOUNT_INVALID")
    student = db.get(Student, student_id)
    if student is None or student.school_id != school_id:
        raise NotFoundError("Student not found.")
    enrollment = db.scalar(select(Enrollment).where(
        Enrollment.student_id == student_id, Enrollment.status == "ACTIVE").limit(1))
    payment = Payment(id=uuid7(), school_id=school_id, student_id=student_id,
                      enrollment_id=enrollment.id if enrollment else None,
                      term_id=term_id, amount_pesewas=int(amount_pesewas), method=method,
                      payer_name=payer_name, payer_phone=payer_phone,
                      status="INITIATED", created_by=actor_id)
    db.add(payment)
    db.flush()

    if method == "CASH":
        # cash is confirmed immediately by the bursar (receipt inside the txn)
        return confirm_payment(db, payment, actor_id=actor_id, request=request,
                               reference=f"CASH-{str(payment.id)[:13].upper()}")

    provider_code = next((c for c, p in PROVIDERS.items() if p.method == method), None)
    if provider_code is None:
        raise ConflictError(f"No provider configured for method {method}.",
                            code="PROVIDER_UNAVAILABLE")
    ensure_default_providers(db, school_id)  # idempotent registry bootstrap
    cfg = provider_for(db, school_id, provider_code)
    adapter = PROVIDERS[cfg.code]
    result = adapter.initiate(payment)
    payment.provider_code = cfg.code
    payment.provider_reference = result["provider_reference"]
    payment.status = "PENDING"
    audit(db, actor_id=actor_id, action="payment.initiated", entity_type="payment",
          entity_id=payment.id,
          new={"method": method, "amount_pesewas": int(amount_pesewas),
               "provider": cfg.code}, request=request)
    db.flush()
    return payment


# --------------------------------------------------------------------------- confirm

def _allocate_fifo(db: Session, payment: Payment) -> None:
    """Oldest-due-first allocation (BR-F05); remainder stays as credit balance."""
    from sqlalchemy import func
    remaining = payment.amount_pesewas
    charges = db.scalars(
        select(FeeCharge)
        .where(FeeCharge.student_id == payment.student_id,
               FeeCharge.status.in_(("ACTIVE", "PART_SETTLED")))
        .order_by(FeeCharge.due_on.asc(), FeeCharge.created_at.asc())).all()
    for charge in charges:
        if remaining <= 0:
            break
        allocated_already = db.scalar(select(func.coalesce(
            func.sum(PaymentAllocation.amount_pesewas), 0)).where(
            PaymentAllocation.fee_charge_id == charge.id)) or 0
        open_amount = charge.amount_pesewas - int(allocated_already)
        if open_amount <= 0:
            continue
        take = min(open_amount, remaining)
        db.add(PaymentAllocation(id=uuid7(), school_id=payment.school_id,
                                 payment_id=payment.id, fee_charge_id=charge.id,
                                 amount_pesewas=take))
        db.flush()  # allocation must be visible to the status recompute below
        remaining -= take
        ledger.refresh_charge_status(db, charge)
    # any remainder is an overpayment credit (visible via derived balance)


def confirm_payment(db: Session, payment: Payment, *, actor_id: uuid.UUID | None,
                    reference: str | None = None, request: Request | None = None,
                    quiet_audit: bool = False) -> Payment:
    """Idempotent confirmation: ledger + allocations + receipt in one transaction."""
    if payment.status == "CONFIRMED":
        return payment  # duplicate webhook/retry → no double posting (BR-F10)
    if payment.status in ("FAILED", "REVERSED", "REFUNDED"):
        raise ConflictError(f"Payment already {payment.status.lower()}.",
                            code="PAYMENT_TERMINAL")
    from app.models.base import utcnow
    payment.status = "CONFIRMED"
    payment.confirmed_at = utcnow()
    if reference:
        payment.provider_reference = reference
    _allocate_fifo(db, payment)
    ledger.post(db, school_id=payment.school_id, student_id=payment.student_id,
                academic_year_id=_year_for(db, payment), term_id=payment.term_id,
                entry_type="CREDIT", category="PAYMENT",
                amount_pesewas=payment.amount_pesewas, occurred_on=date.today(),
                description=f"{payment.method} payment", payment_id=payment.id,
                idempotency_key=f"pay:{payment.id}", actor_id=actor_id,
                request=request, quiet=True)
    receipt = receipts_svc.issue(db, payment=payment, actor_id=actor_id, request=request)
    payment.receipt_id = receipt.id
    if not quiet_audit:
        audit(db, actor_id=actor_id, action="payment.confirmed", entity_type="payment",
              entity_id=payment.id,
              new={"amount_pesewas": int(payment.amount_pesewas),
                   "receipt_no": receipt.receipt_no}, request=request)
    # communications event: receipt confirmation to guardians (REQ-COM-01)
    try:
        from app.models.core import School
        from app.services import comms as comms_svc
        school = db.get(School, payment.school_id)
        student = db.get(Student, payment.student_id)
        if school and student:
            comms_svc.payment_confirmed_comms(
                db, school_id=payment.school_id, school_name=school.name,
                student=student, payment=payment, receipt=receipt,
                balance_pesewas=ledger.balance(db, payment.student_id))
    except Exception:
        # notification failures must never roll back a confirmed payment
        pass
    db.flush()
    return payment


def _year_for(db: Session, payment: Payment) -> uuid.UUID:
    if payment.term_id:
        term = db.get(Term, payment.term_id)
        if term:
            return term.academic_year_id
    if payment.enrollment_id:
        e = db.get(Enrollment, payment.enrollment_id)
        if e:
            return e.academic_year_id
    raise ConflictError("Cannot resolve academic year for payment.", code="YEAR_REQUIRED")


# --------------------------------------------------------------------------- webhooks

def handle_webhook(db: Session, *, school_id: uuid.UUID, provider_code: str,
                   headers: dict, body: bytes) -> dict:
    """Verify → persist event → dedupe → apply. Invalid signatures never apply."""
    ensure_default_providers(db, school_id)  # registry bootstrap (idempotent)
    cfg = provider_for(db, school_id, provider_code)
    adapter = PROVIDERS.get(cfg.code)
    try:
        payload = json.loads(body or b"{}")
    except Exception:
        payload = {}
    event_id = payload.get("event_id")
    sig_status = ("VALID" if adapter and adapter.webhook_signature_ok(
        headers, body, provider_secret(cfg)) else "INVALID")
    event = WebhookEvent(id=uuid7(), school_id=school_id, provider_code=provider_code,
                         external_event_id=event_id, event_type=payload.get("type"),
                         payload=payload, signature_status=sig_status)
    db.add(event)
    db.flush()

    if sig_status != "VALID":
        audit(db, actor_id=None, action="webhook.invalid_signature",
              entity_type="webhook_event", entity_id=event.id,
              new={"provider": provider_code}, request=None)
        return {"applied": False, "reason": "INVALID_SIGNATURE"}

    if event_id:
        dup = db.scalars(select(WebhookEvent).where(
            WebhookEvent.provider_code == provider_code,
            WebhookEvent.external_event_id == event_id,
            WebhookEvent.processed.is_(True))).all()
        if len(dup) > 1 or (len(dup) == 1 and dup[0].id != event.id):
            event.processed = True
            db.flush()
            return {"applied": False, "reason": "DUPLICATE_EVENT"}

    ref = payload.get("provider_reference")
    payment = db.scalar(select(Payment).where(
        Payment.provider_code == provider_code, Payment.provider_reference == ref))
    if payment is None:
        return {"applied": False, "reason": "PAYMENT_NOT_FOUND"}
    event.payment_id = payment.id

    etype = (payload.get("type") or "").upper()
    if etype in ("PAYMENT.SUCCESS", "SUCCESS", "CONFIRMED"):
        if payment.status == "CONFIRMED":
            event.processed = True
            db.flush()
            return {"applied": False, "reason": "ALREADY_CONFIRMED"}
        if payment.status in ("FAILED", "REVERSED", "REFUNDED"):
            # terminal state: late success events are recorded but never applied
            event.processed = True
            db.flush()
            return {"applied": False, "reason": "PAYMENT_TERMINAL"}
        confirm_payment(db, payment, actor_id=None, request=None, quiet_audit=False)
    elif etype in ("PAYMENT.FAILED", "FAILED"):
        payment.status = "FAILED"
        payment.failure_reason = payload.get("reason", "provider failure")
        audit(db, actor_id=None, action="payment.failed", entity_type="payment",
              entity_id=payment.id, new={"reason": payment.failure_reason})
    elif etype in ("PAYMENT.REVERSED", "REVERSED"):
        reverse_payment(db, payment, reason="provider reversal webhook", actor_id=None)
    else:
        return {"applied": False, "reason": "UNKNOWN_EVENT_TYPE"}

    event.processed = True
    db.flush()
    return {"applied": True, "payment_status": payment.status}


# --------------------------------------------------------------------------- reversals

def reverse_payment(db: Session, payment: Payment, *, reason: str,
                    actor_id: uuid.UUID | None, request: Request | None = None) -> Payment:
    if payment.status != "CONFIRMED":
        raise ConflictError("Only confirmed payments can be reversed.", code="NOT_CONFIRMED")
    payment.status = "REVERSED"
    # reverse the ledger entry (counter-entry; original preserved, BR-F08)
    entry = db.scalar(select(ledger.LedgerEntry).where(
        ledger.LedgerEntry.payment_id == payment.id,
        ledger.LedgerEntry.category == "PAYMENT"))
    if entry is not None:
        ledger.reverse(db, entry, reason=reason, actor_id=actor_id,
                       occurred_on=date.today(), request=request)
    # undo allocations & charge statuses
    for alloc in db.scalars(select(PaymentAllocation).where(
            PaymentAllocation.payment_id == payment.id)).all():
        charge = db.get(FeeCharge, alloc.fee_charge_id)
        db.delete(alloc)
        if charge:
            ledger.refresh_charge_status(db, charge)
    db.flush()
    if payment.receipt_id:
        receipts_svc.void(db, db.get(Receipt, payment.receipt_id), reason=reason,
                          actor_id=actor_id, request=request)
    audit(db, actor_id=actor_id, action="payment.reversed", entity_type="payment",
          entity_id=payment.id, new={"amount_pesewas": int(payment.amount_pesewas)},
          reason=reason, request=request)
    return payment


def refund_payment(db: Session, payment: Payment, *, amount_pesewas: int, reason: str,
                   actor_id: uuid.UUID, request: Request | None = None) -> Refund:
    if payment.status != "CONFIRMED":
        raise ConflictError("Only confirmed payments can be refunded.", code="NOT_CONFIRMED")
    if amount_pesewas <= 0 or amount_pesewas > payment.amount_pesewas:
        raise ConflictError("Refund amount out of range.", code="AMOUNT_INVALID")
    refund = Refund(id=uuid7(), school_id=payment.school_id, payment_id=payment.id,
                    student_id=payment.student_id, amount_pesewas=amount_pesewas,
                    reason=reason, authorized_by=actor_id, status="APPROVED",
                    created_by=actor_id)
    db.add(refund)
    db.flush()
    # a refund reduces the school's credit liability to the student ⇒ DEBIT
    ledger.post(db, school_id=payment.school_id, student_id=payment.student_id,
                academic_year_id=_year_for(db, payment), term_id=payment.term_id,
                entry_type="DEBIT", category="REFUND", amount_pesewas=amount_pesewas,
                occurred_on=date.today(), description=f"Refund: {reason[:80]}",
                payment_id=payment.id, refund_id=refund.id,
                idempotency_key=f"refund:{refund.id}", actor_id=actor_id,
                request=request, quiet=True)
    payment.status = "REFUNDED"
    audit(db, actor_id=actor_id, action="payment.refunded", entity_type="payment",
          entity_id=payment.id, new={"amount_pesewas": amount_pesewas},
          reason=reason, request=request)
    return refund


def get_payment(db: Session, school_id: uuid.UUID, payment_id: uuid.UUID) -> Payment:
    p = db.get(Payment, payment_id)
    if p is None or p.school_id != school_id:
        raise NotFoundError("Payment not found.")
    return p
