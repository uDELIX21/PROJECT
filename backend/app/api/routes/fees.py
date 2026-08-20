"""Fee management endpoints: structures, billing, charges, waivers, plans, clearance."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, assert_student_visible, get_school, require
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.models.core import Enrollment, SchoolSetting, Student
from app.models.finance import FeeCharge, FeeStructure, PaymentPlan
from app.schemas.requests import (AdjustmentIn, BillingRunIn, ClearanceOverrideIn,
                                  ClearancePolicyIn, ManualChargeIn, PaymentPlanIn,
                                  StructureCreateIn, WaiverIn)
from app.services import clearance, fees, ledger

router = APIRouter(prefix="/fees", tags=["fees"])


def _enrollment_or_404(db: Session, school_id: uuid.UUID, enrollment_id: uuid.UUID) -> Enrollment:
    e = db.get(Enrollment, enrollment_id)
    if e is None or e.school_id != school_id:
        raise NotFoundError("Enrollment not found.")
    return e


# --------------------------------------------------------------------------- structures

@router.get("/structures")
def list_structures(academic_year_id: uuid.UUID,
                    ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    rows = fees.structures_for(db, school.id, academic_year_id)
    return {"items": [{"id": str(s.id), "name": s.name,
                       "grade_id": str(s.grade_id) if s.grade_id else None,
                       "band": s.band, "status": s.status,
                       "items": [{"fee_type": i.fee_type, "display_name": i.display_name,
                                  "amount_pesewas": int(i.amount_pesewas),
                                  "period": i.period} for i in fees.items_for(db, s.id)]}
                      for s in rows]}


@router.post("/structures", status_code=201)
def create_structure(body: StructureCreateIn, request: Request,
                     ctx: AuthContext = Depends(require(rbac.MANAGE_FEES)),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    s = fees.create_structure(db, school_id=school.id, actor_id=ctx.user.id,
                              request=request, **body.model_dump(exclude_none=True))
    db.commit()
    return {"id": str(s.id), "name": s.name}


@router.post("/billing/preview")
def billing_preview(body: BillingRunIn, ctx: AuthContext = Depends(require(rbac.MANAGE_FEES)),
                    db: Session = Depends(get_db)):
    school = get_school(db)
    return {"items": fees.preview_billing(db, school_id=school.id,
                                          academic_year_id=body.academic_year_id,
                                          term_id=body.term_id)}


@router.post("/billing/apply")
def billing_apply(body: BillingRunIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_FEES)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    res = fees.apply_billing(db, school_id=school.id,
                             academic_year_id=body.academic_year_id,
                             term_id=body.term_id, actor_id=ctx.user.id, request=request)
    db.commit()
    return res


# --------------------------------------------------------------------------- charges & balances

@router.get("/charges")
def list_charges(student_id: uuid.UUID | None = None, status: str | None = None,
                 limit: int = Query(default=50, ge=1, le=200),
                 ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    if student_id:
        assert_student_visible(ctx, db, student_id)
    stmt = select(FeeCharge).where(FeeCharge.school_id == school.id)
    if student_id:
        stmt = stmt.where(FeeCharge.student_id == student_id)
    if status:
        stmt = stmt.where(FeeCharge.status == status)
    rows = db.scalars(stmt.order_by(FeeCharge.created_at.desc()).limit(limit)).all()
    return {"items": [{"id": str(c.id), "student_id": str(c.student_id),
                       "fee_type": c.fee_type, "display_name": c.display_name,
                       "amount_pesewas": int(c.amount_pesewas), "status": c.status,
                       "source": c.source, "term_id": str(c.term_id) if c.term_id else None}
                      for c in rows]}


@router.post("/charges", status_code=201)
def manual_charge(body: ManualChargeIn, request: Request,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_FEES)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    enrollment = _enrollment_or_404(db, school.id, body.enrollment_id)
    charge = fees.add_manual_charge(db, school_id=school.id, enrollment=enrollment,
                                    fee_type=body.fee_type, display_name=body.display_name,
                                    amount_pesewas=body.amount_pesewas, term_id=body.term_id,
                                    actor_id=ctx.user.id, request=request)
    db.commit()
    return {"id": str(charge.id), "amount_pesewas": int(charge.amount_pesewas)}


@router.get("/balances")
def balances(student_id: uuid.UUID,
             academic_year_id: uuid.UUID | None = None,
             term_id: uuid.UUID | None = None,
             ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
             db: Session = Depends(get_db)):
    assert_student_visible(ctx, db, student_id)
    bal = ledger.balance(db, student_id, academic_year_id=academic_year_id,
                         term_id=term_id)
    entries = ledger.entries_for(db, student_id, academic_year_id=academic_year_id, limit=25)
    return {"balance_pesewas": bal,
            "entries": [{"id": str(e.id), "entry_type": e.entry_type,
                         "category": e.category, "amount_pesewas": int(e.amount_pesewas),
                         "occurred_on": str(e.occurred_on), "description": e.description}
                        for e in entries]}


# --------------------------------------------------------------------------- waivers & adjustments

@router.post("/waivers", status_code=201)
def grant_waiver(body: WaiverIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.GRANT_WAIVER)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    enrollment = _enrollment_or_404(db, school.id, body.enrollment_id)
    w = fees.grant_waiver(db, school_id=school.id, enrollment=enrollment, kind=body.kind,
                          amount_pesewas=body.amount_pesewas, pct=body.pct,
                          reason=body.reason, approver_id=ctx.user.id,
                          term_id=body.term_id, fee_charge_id=body.fee_charge_id,
                          request=request)
    db.commit()
    resolved = getattr(w, "_resolved_amount", None) or int(w.amount_pesewas or 0)
    return {"id": str(w.id), "amount_pesewas": int(resolved)}


@router.post("/adjustments", status_code=201)
def add_adjustment(body: AdjustmentIn, request: Request,
                   ctx: AuthContext = Depends(require(rbac.GRANT_WAIVER)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    enrollment = _enrollment_or_404(db, school.id, body.enrollment_id)
    a = fees.add_adjustment(db, school_id=school.id, enrollment=enrollment,
                            direction=body.direction, amount_pesewas=body.amount_pesewas,
                            reason=body.reason, approver_id=ctx.user.id,
                            term_id=body.term_id, request=request)
    db.commit()
    return {"id": str(a.id)}


@router.post("/payment-plans", status_code=201)
def create_plan(body: PaymentPlanIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.MANAGE_FEES)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    enrollment = _enrollment_or_404(db, school.id, body.enrollment_id)
    plan = fees.create_plan(db, school_id=school.id, enrollment=enrollment,
                            term_id=body.term_id,
                            installments=[i.model_dump() for i in body.installments],
                            approver_id=ctx.user.id, note=body.note, request=request)
    db.commit()
    return {"id": str(plan.id), "status": plan.status}


# --------------------------------------------------------------------------- clearance

@router.get("/clearance")
def clearance_states(term_id: uuid.UUID, clearance_type: str = "REPORT_CARD",
                     state: str | None = None,
                     ctx: AuthContext = Depends(require(rbac.MANAGE_CLEARANCE)),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    from app.models.finance import FinancialClearance
    stmt = select(FinancialClearance).where(FinancialClearance.school_id == school.id,
                                            FinancialClearance.term_id == term_id,
                                            FinancialClearance.clearance_type == clearance_type)
    if state:
        stmt = stmt.where(FinancialClearance.state == state)
    rows = db.scalars(stmt.limit(500)).all()
    return {"items": [{"student_id": str(r.student_id), "state": r.state,
                       "paid_pesewas": int(r.paid_pesewas),
                       "charged_pesewas": int(r.charged_pesewas),
                       "override_reason": r.override_reason} for r in rows]}


@router.post("/clearance/evaluate")
def clearance_evaluate(student_id: uuid.UUID, term_id: uuid.UUID,
                       clearance_type: str = "REPORT_CARD",
                       ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                       db: Session = Depends(get_db)):
    school = get_school(db)
    assert_student_visible(ctx, db, student_id)
    res = clearance.evaluate(db, school_id=school.id, student_id=student_id,
                             term_id=term_id, clearance_type=clearance_type)
    db.commit()
    return res


@router.post("/clearance/override")
def clearance_override(body: ClearanceOverrideIn, request: Request,
                       ctx: AuthContext = Depends(require(rbac.MANAGE_CLEARANCE)),
                       db: Session = Depends(get_db)):
    school = get_school(db)
    row = clearance.override(db, school_id=school.id, student_id=body.student_id,
                             term_id=body.term_id, clearance_type=body.clearance_type,
                             state=body.state, reason=body.reason,
                             actor_id=ctx.user.id, request=request)
    db.commit()
    return {"state": row.state}


@router.post("/clearance/policies", status_code=201)
def set_policy(body: ClearancePolicyIn, request: Request,
               ctx: AuthContext = Depends(require(rbac.MANAGE_CLEARANCE)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    p = clearance.create_policy(db, school_id=school.id, actor_id=ctx.user.id,
                                request=request, **body.model_dump(exclude_none=True))
    db.commit()
    return {"id": str(p.id)}


@router.get("/clearance/policies")
def list_policies(academic_year_id: uuid.UUID,
                  ctx: AuthContext = Depends(require(rbac.MANAGE_CLEARANCE)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    from app.models.finance import ClearancePolicy
    rows = db.scalars(select(ClearancePolicy).where(
        ClearancePolicy.school_id == school.id,
        ClearancePolicy.academic_year_id == academic_year_id)).all()
    return {"items": [{"id": str(p.id), "clearance_type": p.clearance_type,
                       "mode": p.mode, "threshold": int(p.threshold),
                       "band": p.band,
                       "term_id": str(p.term_id) if p.term_id else None} for p in rows]}
