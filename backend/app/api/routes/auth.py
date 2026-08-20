"""Authentication endpoints: login, logout, me, csrf, password change/reset."""
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, current_user, get_school
from app.core.audit import audit
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import NotFoundError
from app.core.ratelimit import rate_limit
from app.models.auth import User
from app.schemas.requests import (LoginIn, PasswordChangeIn, PasswordResetConfirmIn,
                                  PasswordResetRequestIn)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(response: Response, token: str) -> None:
    s = get_settings()
    response.set_cookie(
        key=s.session_cookie_name, value=token, httponly=True, secure=s.session_cookie_secure,
        samesite="lax", path="/", max_age=s.session_absolute_days * 24 * 3600,
        domain=s.session_cookie_domain or None)


def _clear_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(s.session_cookie_name, path="/",
                           domain=s.session_cookie_domain or None)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response,
          db: Session = Depends(get_db)):
    rate_limit(request, "login", body.username.lower(), 10, 60)
    settings = get_settings()
    user = auth_service.authenticate(db, body.username, body.password, request, settings)
    token, session = auth_service.create_session(db, user, request, settings)
    db.commit()
    _set_cookie(response, token)
    return {
        "user": _user_summary(user),
        "roles": sorted({r.code for r in user.roles}),
        "permissions": sorted(auth_service._perms_for(user)),
        "csrf_token": session.csrf_token,
    }


@router.post("/logout")
def logout(request: Request, response: Response,
           ctx: AuthContext = Depends(current_user), db: Session = Depends(get_db)):
    from app.models.base import utcnow
    ctx.session.revoked_at = utcnow()
    audit(db, actor_id=ctx.user.id, action="logout", entity_type="user",
          entity_id=ctx.user.id, request=request)
    db.commit()
    _clear_cookie(response)
    return {"ok": True}


@router.get("/csrf")
def csrf(ctx: AuthContext = Depends(current_user)):
    return {"csrf_token": ctx.session.csrf_token}


@router.get("/me")
def me(ctx: AuthContext = Depends(current_user), db: Session = Depends(get_db)):
    school = get_school(db)
    from app.services import calendar
    return {
        "user": _user_summary(ctx.user),
        "roles": sorted(ctx.roles),
        "permissions": sorted(ctx.permissions),
        "school": {"id": str(school.id), "name": school.name, "motto": school.motto,
                   "logo_file_id": str(school.logo_file_id) if school.logo_file_id else None},
        "active_year": _year_or_none(calendar.active_year(db, school.id)),
        "active_term": _term_or_none(calendar.active_term(db, school.id)),
    }


@router.post("/password/change")
def password_change(body: PasswordChangeIn, request: Request,
                    ctx: AuthContext = Depends(current_user), db: Session = Depends(get_db)):
    auth_service.change_password(db, ctx.user, body.current_password, body.new_password,
                                 request)
    db.commit()
    return {"ok": True, "sessions_revoked": True}


@router.post("/password/reset-request")
def reset_request(body: PasswordResetRequestIn, request: Request,
                  db: Session = Depends(get_db)):
    rate_limit(request, "reset", body.username.lower(), 3, 3600)
    user = db.scalar(select(User).where(User.username == body.username))
    dev_token = None
    if user is not None and user.status != "DEACTIVATED":
        token = auth_service.create_reset_token(db, user, request=request)
        if get_settings().dev_mode:
            dev_token = token  # prod: delivered via SMS/email only
        db.commit()
    # uniform response: no account enumeration (design §12)
    return {"sent": True, "dev_token": dev_token}


@router.post("/password/reset-confirm")
def reset_confirm(body: PasswordResetConfirmIn, request: Request,
                  db: Session = Depends(get_db)):
    rate_limit(request, "reset-confirm", None, 10, 60)
    auth_service.consume_reset_token(db, body.token, body.new_password, request)
    db.commit()
    return {"ok": True}


def _user_summary(user: User) -> dict:
    return {"id": str(user.id), "username": user.username, "email": user.email,
            "display_name": user.display_name, "status": user.status,
            "teacher_id": str(user.teacher_id) if user.teacher_id else None,
            "parent_id": str(user.parent_id) if user.parent_id else None,
            "student_id": str(user.student_id) if user.student_id else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None}


def _year_or_none(y):
    from app.schemas import common
    return common.year(y) if y else None


def _term_or_none(t):
    from app.schemas import common
    return common.term(t) if t else None
