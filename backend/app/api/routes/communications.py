"""Communications endpoints: templates, broadcasts, SMS log, in-app notifications."""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, current_user, get_school, require
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.models.base import utcnow
from app.models.operations import CommunicationTemplate, Notification, SMSMessage
from app.schemas.requests import BroadcastIn, CommTemplatePutIn
from app.services import comms

router = APIRouter(prefix="/communications", tags=["communications"])


@router.get("/templates")
def list_templates(ctx: AuthContext = Depends(require(rbac.SEND_COMMUNICATION)),
                   db: Session = Depends(get_db)):
    school = get_school(db)
    comms.ensure_default_templates(db, school.id)
    db.commit()
    rows = db.scalars(select(CommunicationTemplate).where(
        CommunicationTemplate.school_id == school.id)).all()
    return {"items": [{"id": str(t.id), "event_code": t.event_code,
                       "channel": t.channel, "template": t.template,
                       "is_active": t.is_active} for t in rows]}


@router.put("/templates/{template_id}")
def put_template(template_id: uuid.UUID, body: CommTemplatePutIn, request: Request,
                 ctx: AuthContext = Depends(require(rbac.SEND_COMMUNICATION)),
                 db: Session = Depends(get_db)):
    school = get_school(db)
    t = db.get(CommunicationTemplate, template_id)
    if t is None or t.school_id != school.id:
        raise NotFoundError("Template not found.")
    if body.template is not None:
        t.template = body.template
    if body.is_active is not None:
        t.is_active = body.is_active
    db.commit()
    return {"id": str(t.id), "template": t.template}


@router.post("/broadcast")
def broadcast(body: BroadcastIn, request: Request,
              ctx: AuthContext = Depends(require(rbac.SEND_COMMUNICATION)),
              db: Session = Depends(get_db)):
    school = get_school(db)
    res = comms.broadcast(db, school=school, school_id=school.id,
                          event_code=body.event_code, message=body.message,
                          audience=body.audience, extra_vars=body.extra_vars,
                          class_stream_id=body.class_stream_id,
                          actor_id=ctx.user.id, request=request)
    db.commit()
    return res


@router.get("/sms-log")
def sms_log(status: str | None = None, limit: int = 50,
            ctx: AuthContext = Depends(require(rbac.SEND_COMMUNICATION)),
            db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(SMSMessage).where(SMSMessage.school_id == school.id)
    if status:
        stmt = stmt.where(SMSMessage.status == status)
    rows = db.scalars(stmt.order_by(SMSMessage.created_at.desc())
                      .limit(min(limit, 200))).all()
    return {"items": [{"id": str(m.id), "recipient_phone": m.recipient_phone,
                       "event_code": m.event_code, "provider_code": m.provider_code,
                       "status": m.status, "attempts": m.attempts, "error": m.error,
                       "body_preview": m.rendered_body[:80]} for m in rows]}


@router.get("/notifications")
def my_notifications(unread_only: bool = False,
                     ctx: AuthContext = Depends(current_user),
                     db: Session = Depends(get_db)):
    school = get_school(db)
    stmt = select(Notification).where(Notification.school_id == school.id,
                                      Notification.recipient_user_id == ctx.user.id)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    rows = db.scalars(stmt.order_by(Notification.created_at.desc()).limit(50)).all()
    return {"items": [{"id": str(n.id), "kind": n.kind, "title": n.title,
                       "body": n.body, "link": n.link, "read": n.read_at is not None,
                       "created_at": n.created_at.isoformat()} for n in rows]}


@router.post("/notifications/read")
def mark_read(ids: list[uuid.UUID], ctx: AuthContext = Depends(current_user),
              db: Session = Depends(get_db)):
    school = get_school(db)
    rows = db.scalars(select(Notification).where(
        Notification.school_id == school.id,
        Notification.recipient_user_id == ctx.user.id,
        Notification.id.in_(ids))).all()
    for n in rows:
        if n.read_at is None:
            n.read_at = utcnow()
    db.commit()
    return {"marked": len(rows)}
