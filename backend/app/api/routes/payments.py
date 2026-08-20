"""Payment endpoints: initiate, cash confirm, webhooks, reverse/refund (REQ-PAY-*)."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, assert_student_visible, get_school, require
from app.core.db import get_db
from app.core.errors import ForbiddenError, NotFoundError
from app.models.finance import Payment, PaymentAllocation, WebhookEvent
from app.schemas.requests import (PaymentInitiateIn, PaymentReverseIn, RefundIn)
from app.services import payments as pay

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/providers")
def list_providers(ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    pay.ensure_default_providers(db, school.id)
    db.commit()
    from app.models.finance import PaymentProviderConfig
    rows = db.scalars(select(PaymentProviderConfig).where(
        PaymentProviderConfig.school_id == school.id)).all()
    # secrets never exposed (REQ-SEC-02) — only env var names
    return {"items": [{"code": r.code, "display_name": r.display_name, "method": r.method,
                       "kind": r.kind} for r in rows]}


@router.post("/initiate", status_code=201)
def initiate(body: PaymentInitiateIn, request: Request,
             ctx: AuthContext = Depends(require(rbac.CREATE_PAYMENT)),
             db: Session = Depends(get_db)):
    school = get_school(db)
    assert_student_visible(ctx, db, body.student_id)
    payment = pay.initiate_payment(
        db, school=school, school_id=school.id, student_id=body.student_id,
        amount_pesewas=body.amount_pesewas, method=body.method, term_id=body.term_id,
        payer_name=body.payer_name, payer_phone=body.payer_phone,
        actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(payment.id), "status": payment.status,
            "provider_reference": payment.provider_reference,
            "receipt_id": str(payment.receipt_id) if payment.receipt_id else None}


@router.get("/{payment_id}")
def get_payment(payment_id: uuid.UUID,
                ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    p = pay.get_payment(db, school.id, payment_id)
    assert_student_visible(ctx, db, p.student_id)
    allocs = db.scalars(select(PaymentAllocation).where(
        PaymentAllocation.payment_id == payment_id)).all()
    return {"id": str(p.id), "student_id": str(p.student_id), "status": p.status,
            "method": p.method, "provider_code": p.provider_code,
            "provider_reference": p.provider_reference,
            "amount_pesewas": int(p.amount_pesewas),
            "confirmed_at": p.confirmed_at.isoformat() if p.confirmed_at else None,
            "receipt_id": str(p.receipt_id) if p.receipt_id else None,
            "allocations": [{"fee_charge_id": str(a.fee_charge_id),
                             "amount_pesewas": int(a.amount_pesewas)} for a in allocs]}


@router.get("")
def list_payments(student_id: uuid.UUID | None = None, status: str | None = None,
                  limit: int = 50,
                  ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(Payment).where(Payment.school_id == school.id)
    if student_id:
        assert_student_visible(ctx, db, student_id)
        stmt = stmt.where(Payment.student_id == student_id)
    if status:
        stmt = stmt.where(Payment.status == status)
    rows = db.scalars(stmt.order_by(Payment.created_at.desc()).limit(min(limit, 200))).all()
    return {"items": [{"id": str(p.id), "student_id": str(p.student_id),
                       "status": p.status, "method": p.method,
                       "amount_pesewas": int(p.amount_pesewas),
                       "provider_reference": p.provider_reference,
                       "receipt_id": str(p.receipt_id) if p.receipt_id else None}
                      for p in rows]}


@router.post("/{payment_id}/reverse")
def reverse(payment_id: uuid.UUID, body: PaymentReverseIn, request: Request,
            ctx: AuthContext = Depends(require(rbac.VOID_PAYMENT)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    p = pay.get_payment(db, school.id, payment_id)
    pay.reverse_payment(db, p, reason=body.reason, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"status": p.status}


@router.post("/{payment_id}/refund")
def refund(payment_id: uuid.UUID, body: RefundIn, request: Request,
           ctx: AuthContext = Depends(require(rbac.VOID_PAYMENT)),
           db: Session = Depends(get_db)):
    school = get_school(db)
    p = pay.get_payment(db, school.id, payment_id)
    r = pay.refund_payment(db, p, amount_pesewas=body.amount_pesewas, reason=body.reason,
                           actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(r.id), "status": p.status}


@router.get("/webhook-log")
def webhook_log(ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                db: Session = Depends(get_db)):
    """Admin visibility into webhook processing (monitoring, REQ-OBS-01)."""
    school = get_school(db)
    rows = db.scalars(select(WebhookEvent).where(
        WebhookEvent.school_id == school.id)
        .order_by(WebhookEvent.received_at.desc()).limit(50)).all()
    return {"items": [{"id": str(w.id), "provider_code": w.provider_code,
                       "event_type": w.event_type, "signature_status": w.signature_status,
                       "processed": w.processed,
                       "received_at": w.received_at.isoformat()} for w in rows]}


@router.post("/webhooks/{provider_code}")
async def webhook(provider_code: str, request: Request, db: Session = Depends(get_db)):
    """Provider callback: verify signature → dedupe → apply (BR-F10).

    Unauthenticated by design; authenticity comes from the HMAC signature.
    """
    school = get_school(db)
    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    result = pay.handle_webhook(db, school_id=school.id, provider_code=provider_code,
                                headers=headers, body=body)
    db.commit()
    return result
