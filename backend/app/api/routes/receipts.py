"""Receipt endpoints: view, PDF, controlled void (REQ-RCP-*)."""
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, assert_student_visible, get_school, require
from app.core.db import get_db
from app.core.errors import ConflictError
from app.models.core import School, Student
from app.models.finance import Receipt
from app.schemas.requests import ReceiptVoidIn
from app.services import files, receipts as svc

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.get("")
def list_receipts(student_id: uuid.UUID | None = None, limit: int = 50,
                  ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                  db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(Receipt).where(Receipt.school_id == school.id)
    if student_id:
        assert_student_visible(ctx, db, student_id)
        stmt = stmt.where(Receipt.student_id == student_id)
    rows = db.scalars(stmt.order_by(Receipt.created_at.desc()).limit(min(limit, 200))).all()
    return {"items": [{"id": str(r.id), "receipt_no": r.receipt_no,
                       "student_id": str(r.student_id), "amount_pesewas": int(r.amount_pesewas),
                       "method": r.method, "issued_on": str(r.issued_on),
                       "status": r.status} for r in rows]}


@router.get("/{receipt_id}")
def get_receipt(receipt_id: uuid.UUID,
                ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    r = svc.get_receipt(db, school.id, receipt_id)
    assert_student_visible(ctx, db, r.student_id)
    return {"id": str(r.id), "receipt_no": r.receipt_no, "student_id": str(r.student_id),
            "payer_name": r.payer_name, "amount_pesewas": int(r.amount_pesewas),
            "method": r.method, "issued_on": str(r.issued_on),
            "transaction_ref": r.transaction_ref,
            "balance_after_pesewas": int(r.balance_after_pesewas), "status": r.status,
            "void_reason": r.void_reason}


@router.get("/{receipt_id}/pdf")
def receipt_pdf(receipt_id: uuid.UUID,
                ctx: AuthContext = Depends(require(rbac.VIEW_FINANCE)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    r = svc.get_receipt(db, school.id, receipt_id)
    assert_student_visible(ctx, db, r.student_id)
    if r.pdf_file_id is None:
        raise ConflictError("Receipt PDF not available; regenerate via re-issue workflow.",
                            code="PDF_MISSING")
    stored, data = files.read_file(r.pdf_file_id, db)
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition":
                             f'inline; filename="receipt-{r.receipt_no}.pdf"'})


@router.post("/{receipt_id}/void")
def void_receipt(receipt_id: uuid.UUID, body: ReceiptVoidIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.VOID_PAYMENT)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    r = svc.get_receipt(db, school.id, receipt_id)
    svc.void(db, r, reason=body.reason, actor_id=ctx.user.id, request=request)
    db.commit()
    return {"status": r.status}
