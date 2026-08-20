"""Authentication business logic: login w/ lockout, sessions, password reset (design §06)."""
import uuid
from datetime import timedelta

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import security
from app.core.audit import audit
from app.core.config import Settings, get_settings
from app.core.errors import ConflictError, ForbiddenError, UnauthorizedError
from app.core.ids import uuid7
from app.models.auth import PasswordResetToken, SessionRecord, User
from app.models.base import ensure_aware, utcnow


def _perms_for(user: User) -> set[str]:
    perms: set[str] = set()
    for role in user.roles:
        perms.update(p.code for p in role.permissions)
    return perms


def authenticate(db: Session, username: str, password: str, request: Request | None = None,
                 settings: Settings | None = None) -> User:
    s = settings or get_settings()
    user = db.scalar(select(User).where(User.username == username))
    now = utcnow()
    if user is None:
        raise UnauthorizedError("Invalid credentials.", code="INVALID_CREDENTIALS")
    if user.status == "DEACTIVATED":
        raise UnauthorizedError("Account is deactivated.", code="ACCOUNT_DEACTIVATED")
    # NOTE: failure counters below are committed (db.commit) before raising —
    # otherwise the rollback-on-exception would silently reset lockout state.
    if ensure_aware(user.locked_until) and ensure_aware(user.locked_until) > now:
        raise UnauthorizedError("Account temporarily locked. Try again later.",
                                code="ACCOUNT_LOCKED")
    if not security.verify_password(user.password_hash, password, s):
        user.failed_login_count += 1
        if user.failed_login_count >= s.login_max_failures:
            user.locked_until = now + timedelta(minutes=s.login_lock_minutes)
            user.failed_login_count = 0
            audit(db, actor_id=user.id, action="login.locked", entity_type="user",
                  entity_id=user.id, new={"locked_until": str(user.locked_until)},
                  request=request)
        audit(db, actor_id=user.id, action="login.failed", entity_type="user",
              entity_id=user.id, new={"failed_count": user.failed_login_count},
              request=request)
        db.commit()  # persist failure counter / lockout before raising
        raise UnauthorizedError("Invalid credentials.", code="INVALID_CREDENTIALS")
    # success
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = now
    if user.status == "LOCKED":
        user.status = "ACTIVE"
    audit(db, actor_id=user.id, action="login.success", entity_type="user",
          entity_id=user.id, request=request)
    db.flush()
    return user


def create_session(db: Session, user: User, request: Request | None = None,
                   settings: Settings | None = None) -> tuple[str, SessionRecord]:
    """Returns (raw_token, session_row). Only the token hash is stored."""
    s = settings or get_settings()
    now = utcnow()
    token = security.new_token()
    rec = SessionRecord(
        id=uuid7(),
        user_id=user.id,
        token_hash=security.sha256_hex(token),
        csrf_token=security.new_token(24),
        ip=request.client.host if request is not None and request.client else None,
        user_agent=(request.headers.get("user-agent") or "")[:512] if request is not None else None,
        created_at=now,
        last_seen_at=now,
        expires_at=now + timedelta(days=s.session_absolute_days),
    )
    db.add(rec)
    db.flush()
    return token, rec


def get_session_row(db: Session, raw_token: str) -> SessionRecord | None:
    return db.scalar(select(SessionRecord).where(
        SessionRecord.token_hash == security.sha256_hex(raw_token)))


def revoke_user_sessions(db: Session, user_id: uuid.UUID) -> int:
    rows = db.scalars(select(SessionRecord).where(
        SessionRecord.user_id == user_id, SessionRecord.revoked_at.is_(None))).all()
    now = utcnow()
    for row in rows:
        row.revoked_at = now
    return len(rows)


def create_reset_token(db: Session, user: User, purpose: str = "RESET",
                       request: Request | None = None) -> str:
    token = security.new_token(24)
    db.add(PasswordResetToken(id=uuid7(), user_id=user.id,
                              token_hash=security.sha256_hex(token),
                              purpose=purpose,
                              expires_at=utcnow() + timedelta(hours=1)))
    audit(db, actor_id=user.id, action="password.reset_requested", entity_type="user",
          entity_id=user.id, new={"purpose": purpose}, request=request)
    db.flush()
    return token


def consume_reset_token(db: Session, token: str, new_password: str,
                        request: Request | None = None,
                        settings: Settings | None = None) -> User:
    s = settings or get_settings()
    row = db.scalar(select(PasswordResetToken).where(
        PasswordResetToken.token_hash == security.sha256_hex(token)))
    if row is None or row.used_at is not None or ensure_aware(row.expires_at) < utcnow():
        raise UnauthorizedError("Reset token is invalid or expired.", code="TOKEN_INVALID")
    user = db.get(User, row.user_id)
    if user is None:
        raise UnauthorizedError("Reset token is invalid or expired.", code="TOKEN_INVALID")
    if len(new_password) < s.password_min_length:
        raise ConflictError(f"Password must be at least {s.password_min_length} characters.",
                            code="PASSWORD_TOO_SHORT")
    user.password_hash = security.hash_password(new_password, s)
    row.used_at = utcnow()
    revoke_user_sessions(db, user.id)
    audit(db, actor_id=user.id, action="password.reset_used", entity_type="user",
          entity_id=user.id, request=request)
    db.flush()
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str,
                    request: Request | None = None, settings: Settings | None = None) -> None:
    s = settings or get_settings()
    if not security.verify_password(user.password_hash, current_password, s):
        raise ForbiddenError("Current password is incorrect.", code="PASSWORD_MISMATCH")
    if len(new_password) < s.password_min_length:
        raise ConflictError(f"Password must be at least {s.password_min_length} characters.",
                            code="PASSWORD_TOO_SHORT")
    user.password_hash = security.hash_password(new_password, s)
    revoke_user_sessions(db, user.id)
    audit(db, actor_id=user.id, action="password.changed", entity_type="user",
          entity_id=user.id, request=request)
    db.flush()
