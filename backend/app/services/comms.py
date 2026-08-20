"""Communications: SMS provider abstraction + send engine + in-app notifications
(REQ-COM-*, BR-N). Providers are swappable; credentials live in env, never DB."""
import os
import re
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.core.phones import normalize_ghana_phone
from app.models.base import utcnow
from app.models.auth import User
from app.models.core import (ParentGuardian, ParentStudentRelationship,
                             SchoolSetting, Student)
from app.models.operations import (CommunicationTemplate, Notification, SMSMessage)

DEFAULT_TEMPLATES = {
    "PAYMENT_CONFIRMED": ("Hello {{guardian_name}}, we received {{amount}} for "
                          "{{student_name}} ({{year}} {{term}}). Receipt: {{receipt_no}}. "
                          "Balance: {{balance}}. — {{school_name}}"),
    "FEE_REMINDER": ("Hello {{guardian_name}}, a friendly reminder that {{student_name}}'s "
                     "fee balance is {{balance}}. Thank you. — {{school_name}}"),
    "REPORT_AVAILABLE": ("Hello {{guardian_name}}, {{student_name}}'s {{term}} report card is "
                         "now available. — {{school_name}}"),
    "EMERGENCY_BROADCAST": ("URGENT from {{school_name}}: {{message}}"),
    "ANNOUNCEMENT": ("{{school_name}}: {{message}}"),
    "DISCIPLINE_NOTICE": ("Hello {{guardian_name}}, please contact the school regarding "
                          "{{student_name}}. — {{school_name}}"),
}
EVENT_KIND_MAP = {
    "PAYMENT_CONFIRMED": "PAYMENT_CONFIRMED",
    "FEE_REMINDER": "FEE_REMINDER",
    "REPORT_AVAILABLE": "REPORT_AVAILABLE",
    "EMERGENCY_BROADCAST": "EMERGENCY_BROADCAST",
    "ANNOUNCEMENT": "ANNOUNCEMENT",
    "DISCIPLINE_NOTICE": "DISCIPLINE_NOTICE",
}


# --------------------------------------------------------------------------- providers

class SMSProvider:
    """Interface (design §11). Adapters must raise on transport failure."""
    code = "base"

    def send(self, to_e164: str, body: str, reference: str) -> str:
        raise NotImplementedError


class ConsoleSMSProvider(SMSProvider):
    """Dev adapter: records instead of sending (clearly simulated)."""
    code = "CONSOLE"

    def send(self, to_e164: str, body: str, reference: str) -> str:
        return f"CONSOLE-{reference}"


class ArkeselSMSProvider(SMSProvider):
    """Live adapter (skeleton): requires ARKESEL_API_KEY env; never hard-coded."""
    code = "ARKesel"

    def __init__(self):
        self.api_key = os.environ.get("ARKESEL_API_KEY")
        self.sender_id = os.environ.get("ARKESEL_SENDER_ID", "SCHOOL")

    def send(self, to_e164: str, body: str, reference: str) -> str:
        if not self.api_key:
            raise RuntimeError("ARKESEL_API_KEY not configured")
        import json
        import urllib.request
        req = urllib.request.Request(
            "https://sms.arkesel.com/sms/api",
            data=json.dumps({"action": "send-sms", "api_key": self.api_key,
                             "to": to_e164.lstrip("+"), "from": self.sender_id,
                             "sms": body}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if data.get("code") != "1100":
            raise RuntimeError(f"Arkesel error: {data.get('message')}")
        return str(data.get("message_id") or reference)


class HubtelSMSProvider(SMSProvider):
    """Live adapter (skeleton): requires HUBTEL_CLIENT_ID/SECRET env."""
    code = "HUBTEL"

    def __init__(self):
        self.client_id = os.environ.get("HUBTEL_CLIENT_ID")
        self.client_secret = os.environ.get("HUBTEL_CLIENT_SECRET")
        self.from_id = os.environ.get("HUBTEL_FROM_ID", "SchoolSMS")

    def send(self, to_e164: str, body: str, reference: str) -> str:
        if not (self.client_id and self.client_secret):
            raise RuntimeError("HUBTEL credentials not configured")
        import base64
        import json
        import urllib.request
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        req = urllib.request.Request(
            "https://sms.hubtel.com/v1/messages/send",
            data=json.dumps({"From": self.from_id, "To": to_e164.lstrip("+"),
                             "Content": body, "ClientReference": reference}).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Basic {auth}"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if data.get("Status") != 0:
            raise RuntimeError(f"Hubtel error: {data}")
        return str(data.get("MessageId") or reference)


def get_sms_provider(db: Session, school_id: uuid.UUID) -> SMSProvider:
    """Provider chosen via school setting `comms.provider` (config, not code)."""
    row = db.scalar(select(SchoolSetting).where(
        SchoolSetting.school_id == school_id, SchoolSetting.key == "comms.provider"))
    code = (row.value if row and isinstance(row.value, str) else "CONSOLE").upper()
    if code == "ARKesel":
        return ArkeselSMSProvider()
    if code == "HUBTEL":
        return HubtelSMSProvider()
    return ConsoleSMSProvider()


# --------------------------------------------------------------------------- templates

def ensure_default_templates(db: Session, school_id: uuid.UUID) -> None:
    for event, tpl in DEFAULT_TEMPLATES.items():
        exists = db.scalar(select(CommunicationTemplate).where(
            CommunicationTemplate.school_id == school_id,
            CommunicationTemplate.event_code == event,
            CommunicationTemplate.channel == "SMS"))
        if exists is None:
            db.add(CommunicationTemplate(id=uuid7(), school_id=school_id,
                                         event_code=event, channel="SMS", template=tpl))
    db.flush()


def render(db: Session, school_id: uuid.UUID, event_code: str, vars: dict) -> str:
    tpl = db.scalar(select(CommunicationTemplate).where(
        CommunicationTemplate.school_id == school_id,
        CommunicationTemplate.event_code == event_code,
        CommunicationTemplate.channel == "SMS",
        CommunicationTemplate.is_active.is_(True)))
    text = tpl.template if tpl else DEFAULT_TEMPLATES.get(event_code, "{{message}}")

    def repl(m):
        return str(vars.get(m.group(1), ""))
    return re.sub(r"\{\{(\w+)\}\}", repl, text)


# --------------------------------------------------------------------------- sending

def notify_user(db: Session, *, school_id: uuid.UUID, user_id: uuid.UUID, kind: str,
                title: str, body: str, link: str | None = None,
                student_id: uuid.UUID | None = None) -> Notification:
    n = Notification(id=uuid7(), school_id=school_id, recipient_user_id=user_id,
                     kind=kind, title=title, body=body, link=link, student_id=student_id)
    db.add(n)
    db.flush()
    return n


def guardian_users(db: Session, student_id: uuid.UUID) -> list[User]:
    """Parent logins linked to this student."""
    from app.models.core import ParentStudentRelationship
    parent_ids = db.scalars(select(ParentStudentRelationship.parent_id).where(
        ParentStudentRelationship.student_id == student_id,
        ParentStudentRelationship.effective_to.is_(None))).all()
    if not parent_ids:
        return []
    return list(db.scalars(select(User).where(User.parent_id.in_(parent_ids),
                                              User.status == "ACTIVE")).all())


def send_sms(db: Session, *, school_id: uuid.UUID, phone: str, body: str,
             event_code: str | None = None, guardian_id: uuid.UUID | None = None,
             student_id: uuid.UUID | None = None,
             max_attempts: int = 3) -> SMSMessage:
    """Single send with retries (BR-N03). Invalid numbers are SKIPPED, not fatal."""
    normalized = normalize_ghana_phone(phone)
    msg = SMSMessage(id=uuid7(), school_id=school_id, recipient_guardian_id=guardian_id,
                     recipient_phone=normalized or (phone or ""), event_code=event_code,
                     rendered_body=body, provider_code=get_sms_provider(db, school_id).code,
                     student_id=student_id)
    db.add(msg)
    db.flush()
    if normalized is None:
        msg.status = "SKIPPED"
        msg.error = "invalid_ghana_number"
        db.flush()
        return msg
    guardian = db.get(ParentGuardian, guardian_id) if guardian_id else None
    if guardian is not None and guardian.sms_opt_out and event_code not in (
            "PAYMENT_CONFIRMED",):
        msg.status = "SKIPPED"
        msg.error = "opted_out"
        db.flush()
        return msg
    provider = get_sms_provider(db, school_id)
    last_error = None
    for attempt in range(1, max_attempts + 1):
        msg.attempts = attempt
        msg.status = "SENDING"
        db.flush()
        try:
            msg.provider_message_id = provider.send(normalized, body, str(msg.id))
            msg.status = "SENT"
            msg.sent_at = utcnow()
            msg.error = None
            db.flush()
            return msg
        except Exception as exc:  # provider outage → retry then FAILED (BR-N03)
            last_error = str(exc)[:250]
    msg.status = "FAILED"
    msg.error = last_error
    db.flush()
    return msg


def broadcast(db: Session, *, school: "object", school_id: uuid.UUID, event_code: str,
              message: str | None, audience: str, extra_vars: dict | None = None,
              class_stream_id: uuid.UUID | None = None,
              actor_id: uuid.UUID | None = None, request=None) -> dict:
    """Bulk send to guardian audience (school | ecd | primary | jhs | class | debtors)."""
    if event_code not in EVENT_KIND_MAP:
        raise ConflictError(f"Unknown event code {event_code}.", code="EVENT_UNKNOWN")
    from app.models.core import ClassStream, Enrollment, Grade
    from app.models.finance import LedgerEntry
    from sqlalchemy import func

    # audience resolution → distinct guardians w/ their students
    pairs: list[tuple[ParentGuardian, Student]] = []
    rel_q = select(ParentGuardian, Student).join(
        ParentStudentRelationship,
        ParentStudentRelationship.parent_id == ParentGuardian.id).join(
        Student, Student.id ==
        ParentStudentRelationship.student_id).where(
        ParentGuardian.school_id == school_id)
    if audience == "ecd" or audience == "primary" or audience == "jhs":
        band = {"ecd": "EARLY_CHILDHOOD", "primary": "PRIMARY", "jhs": "JHS"}[audience]
        rel_q = rel_q.join(Enrollment, Enrollment.student_id == Student.id).join(
            ClassStream, Enrollment.class_stream_id == ClassStream.id).join(
            Grade, ClassStream.grade_id == Grade.id).where(
            Enrollment.status == "ACTIVE", Grade.band == band)
    elif audience == "class":
        if class_stream_id is None:
            raise ConflictError("class_stream_id required for class audience.",
                                code="AUDIENCE_CLASS_REQUIRED")
        rel_q = rel_q.join(Enrollment, Enrollment.student_id == Student.id).where(
            Enrollment.status == "ACTIVE", Enrollment.class_stream_id == class_stream_id)
    elif audience == "debtors":
        from sqlalchemy import case
        owing = select(LedgerEntry.student_id).group_by(LedgerEntry.student_id).having(
            func.sum(case((LedgerEntry.entry_type == "DEBIT",
                           LedgerEntry.amount_pesewas),
                          else_=-LedgerEntry.amount_pesewas)) > 0)
        rel_q = rel_q.where(Student.id.in_(owing))
    elif audience != "school":
        raise ConflictError(f"Unknown audience {audience}.", code="AUDIENCE_UNKNOWN")
    pairs = db.execute(rel_q).all()

    from app.services import calendar
    term = calendar.active_term(db, school_id)
    year_row = calendar.active_year(db, school_id)
    sent = skipped = 0
    seen: set[uuid.UUID] = set()
    for guardian, student in pairs:
        vars = {"guardian_name": guardian.name.split()[0],
                "student_name": student.full_name,
                "school_name": school.name,
                "year": year_row.name if year_row else "",
                "term": term.name if term else "",
                "message": message or "",
                **(extra_vars or {})}
        body = render(db, school_id, event_code, vars)
        # one SMS per guardian per broadcast (dedupe), but an in-app notice per child
        if guardian.id not in seen:
            seen.add(guardian.id)
            msg = send_sms(db, school_id=school_id, phone=guardian.phone, body=body,
                           event_code=event_code, guardian_id=guardian.id,
                           student_id=student.id)
            if msg.status in ("SENT", "QUEUED", "SENDING"):
                sent += 1
            else:
                skipped += 1
        for u in guardian_users(db, student.id):
            notify_user(db, school_id=school_id, user_id=u.id,
                        kind=EVENT_KIND_MAP[event_code],
                        title=event_code.replace("_", " ").title(),
                        body=body, student_id=student.id)
    audit(db, actor_id=actor_id, action="comms.broadcast", entity_type="broadcast",
          entity_id=str(uuid7()),
          new={"event": event_code, "audience": audience, "sent": sent, "skipped": skipped},
          request=request)
    db.flush()
    return {"sent": sent, "skipped": skipped, "recipients": len(seen)}


def payment_confirmed_comms(db: Session, *, school_id: uuid.UUID, school_name: str,
                            student: Student, payment, receipt, balance_pesewas: int) -> None:
    """Hook called after payment confirmation (REQ-COM-01 event)."""
    term_name = year_name = ""
    if payment.term_id:
        from app.models.core import Term
        t = db.get(Term, payment.term_id)
        if t:
            term_name = t.name
            from app.models.core import AcademicYear
            y = db.get(AcademicYear, t.academic_year_id)
            year_name = y.name if y else ""
    vars = {"guardian_name": "", "student_name": student.full_name,
            "school_name": school_name, "year": year_name, "term": term_name,
            "amount": f"GHS {payment.amount_pesewas / 100:,.2f}",
            "receipt_no": receipt.receipt_no if receipt else "",
            "balance": f"GHS {balance_pesewas / 100:,.2f}"}
    body = render(db, school_id, "PAYMENT_CONFIRMED", vars)
    for guardian in db.scalars(select(ParentGuardian).join(
            ParentStudentRelationship,
            ParentStudentRelationship.parent_id == ParentGuardian.id).where(
            ParentStudentRelationship.student_id == student.id)).all():
        vars_g = {**vars, "guardian_name": guardian.name.split()[0]}
        send_sms(db, school_id=school_id, phone=guardian.phone,
                 body=render(db, school_id, "PAYMENT_CONFIRMED", vars_g),
                 event_code="PAYMENT_CONFIRMED", guardian_id=guardian.id,
                 student_id=student.id)
        for u in db.scalars(select(User).where(User.parent_id == guardian.id,
                                               User.status == "ACTIVE")).all():
            notify_user(db, school_id=school_id, user_id=u.id, kind="PAYMENT_CONFIRMED",
                        title="Payment received", body=body, student_id=student.id,
                        link=f"/students/{student.id}")


def report_available_comms(db: Session, *, school_id: uuid.UUID, school_name: str,
                           student: Student, term_name: str) -> None:
    body_tpl = render(db, school_id, "REPORT_AVAILABLE",
                      {"guardian_name": "", "student_name": student.full_name,
                       "school_name": school_name, "term": term_name})
    for u in guardian_users(db, student.id):
        notify_user(db, school_id=school_id, user_id=u.id, kind="REPORT_AVAILABLE",
                    title="Report card available", body=body_tpl, student_id=student.id,
                    link="/reports")
    for guardian in db.scalars(select(ParentGuardian).join(
            ParentStudentRelationship,
            ParentStudentRelationship.parent_id == ParentGuardian.id).where(
            ParentStudentRelationship.student_id == student.id)).all():
        send_sms(db, school_id=school_id, phone=guardian.phone,
                 body=render(db, school_id, "REPORT_AVAILABLE",
                             {"guardian_name": guardian.name.split()[0],
                              "student_name": student.full_name,
                              "school_name": school_name, "term": term_name}),
                 event_code="REPORT_AVAILABLE", guardian_id=guardian.id,
                 student_id=student.id)
