"""Receipts: sequential numbering, PDF, immutable issue, controlled void (REQ-RCP-*)."""
import uuid
from datetime import date

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.models.core import School, Student
from app.models.finance import Payment, Receipt
from app.services import files, ledger, sequences


def issue(db: Session, *, payment: Payment, actor_id: uuid.UUID | None = None,
          request: Request | None = None) -> Receipt:
    """Called inside the payment-confirmation transaction (atomicity, BR-F07)."""
    school = db.get(School, payment.school_id)
    student = db.get(Student, payment.student_id)
    receipt_no, _ = sequences.next_value(db, payment.school_id, "RECEIPT_NO",
                                         prefix=(school.settings or {}).get(
                                             "receipt_prefix", "RCPT")
                                         if isinstance(school.settings, dict) else "RCPT")
    balance_after = ledger.balance(db, payment.student_id)
    receipt = Receipt(id=uuid7(), school_id=payment.school_id, receipt_no=receipt_no,
                      payment_id=payment.id, student_id=payment.student_id,
                      payer_name=payment.payer_name or (student.full_name if student else None),
                      amount_pesewas=payment.amount_pesewas, method=payment.method,
                      issued_on=date.today(), transaction_ref=payment.provider_reference,
                      academic_year_id=None, term_id=payment.term_id,
                      balance_after_pesewas=balance_after, created_by=actor_id)
    db.add(receipt)
    db.flush()
    # render PDF eagerly (small; stored for immutability)
    try:
        pdf_bytes = render_receipt_pdf(db, school, student, receipt)
        stored = files.store_file(db, purpose="RECEIPT", mime="application/pdf",
                                  data=pdf_bytes, actor_id=actor_id,
                                  key_hint=receipt_no)
        receipt.pdf_file_id = stored.id
    except Exception:
        # PDF failure must not fail the payment itself (REQ-ERR-01: retryable separately)
        receipt.pdf_file_id = None
    audit(db, actor_id=actor_id, action="receipt.issued", entity_type="receipt",
          entity_id=receipt.id,
          new={"receipt_no": receipt_no, "amount_pesewas": int(receipt.amount_pesewas)},
          request=request)
    return receipt


def void(db: Session, receipt: Receipt, *, reason: str, actor_id: uuid.UUID | None,
         request: Request | None = None) -> Receipt:
    """Controlled void (BR-F08): the original row stays; state flips + audit."""
    if receipt.status == "VOIDED":
        raise ConflictError("Receipt already voided.", code="ALREADY_VOIDED")
    from app.models.base import utcnow
    receipt.status = "VOIDED"
    receipt.voided_at = utcnow()
    receipt.voided_by = actor_id
    receipt.void_reason = reason
    audit(db, actor_id=actor_id, action="receipt.voided", entity_type="receipt",
          entity_id=receipt.id, new={"receipt_no": receipt.receipt_no},
          reason=reason, request=request)
    db.flush()
    return receipt


def get_receipt(db: Session, school_id: uuid.UUID, receipt_id: uuid.UUID) -> Receipt:
    r = db.get(Receipt, receipt_id)
    if r is None or r.school_id != school_id:
        raise NotFoundError("Receipt not found.")
    return r


def render_receipt_pdf(db: Session, school: School, student: Student | None,
                       receipt: Receipt) -> bytes:
    """fpdf2 rendering (dependency-free); mirrors the report renderer abstraction."""
    from app.services.reports import FpdfRenderer

    class ReceiptPdf(FpdfRenderer):
        pass

    t = ReceiptPdf._t
    from fpdf import FPDF
    pdf = FPDF(format="A5")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 7, t(school.name), align="C", new_x="LMARGIN", new_y="NEXT")
    if school.motto:
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 4, t(school.motto), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "OFFICIAL RECEIPT", align="C", new_x="LMARGIN", new_y="NEXT")
    if receipt.status == "VOIDED":
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 6, "*** VOID ***", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    rows = [
        ("Receipt No.", receipt.receipt_no),
        ("Date", str(receipt.issued_on)),
        ("Student", student.full_name if student else "-"),
        ("Payer", receipt.payer_name or "-"),
        ("Method", receipt.method.replace("_", " ")),
        ("Reference", receipt.transaction_ref or "-"),
        ("Amount (GHS)", f"{receipt.amount_pesewas / 100:,.2f}"),
        ("Balance after (GHS)", f"{receipt.balance_after_pesewas / 100:,.2f}"),
    ]
    for k, v in rows:
        pdf.cell(50, 6, t(k), border=0)
        pdf.cell(0, 6, t(str(v)), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 7)
    pdf.cell(0, 4, "This receipt is immutable once issued; voids are recorded separately.",
             new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
