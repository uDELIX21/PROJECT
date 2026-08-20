"""Shared dependencies: session resolution, RBAC gate, resource scoping.

Authorization fails closed (BR-U04): anything uncertain ⇒ 401/403/404.
Frontend hiding is never relied upon — every guard here is server-side (Agent Rule 6).
"""
import uuid
from dataclasses import dataclass, field
from datetime import timedelta

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import ForbiddenError, NotFoundError, UnauthorizedError
from app.models.auth import SessionRecord, User
from app.models.base import ensure_aware, utcnow
from app.models.core import (ClassStream, Enrollment, ParentStudentRelationship,
                             School, Teacher, TeacherAssignment)
from app.services.auth_service import _perms_for


@dataclass
class AuthContext:
    user: User
    session: SessionRecord
    roles: set[str] = field(default_factory=set)
    permissions: set[str] = field(default_factory=set)

    def has(self, permission: str) -> bool:
        return permission in self.permissions


def get_school(db: Session) -> School:
    school = db.scalar(select(School).order_by(School.created_at))
    if school is None:
        raise NotFoundError("School not initialized.", code="NO_SCHOOL")
    return school


def current_user(request: Request, db: Session = Depends(get_db)) -> AuthContext:
    settings = get_settings()
    raw = request.cookies.get(settings.session_cookie_name)
    if not raw:
        raise UnauthorizedError()
    from app.services.auth_service import get_session_row
    session = get_session_row(db, raw)
    now = utcnow()
    if session is None or session.revoked_at is not None \
            or ensure_aware(session.expires_at) < now:
        raise UnauthorizedError("Session expired. Please log in again.")
    if ensure_aware(session.last_seen_at) + timedelta(hours=settings.session_idle_hours) < now:
        session.revoked_at = now
        db.flush()
        raise UnauthorizedError("Session expired due to inactivity.")
    user = db.get(User, session.user_id)
    if user is None or user.status == "DEACTIVATED":
        raise UnauthorizedError("Account unavailable.")
    # CSRF double-submit on mutating methods (design §06)
    if request.method in ("POST", "PATCH", "PUT", "DELETE"):
        supplied = request.headers.get(settings.csrf_header, "")
        if not supplied or supplied != session.csrf_token:
            raise ForbiddenError("CSRF token missing or invalid.", code="CSRF_INVALID")
    # refresh idle window (cheap: one UPDATE per request)
    session.last_seen_at = now
    ctx = AuthContext(user=user, session=session,
                      roles={r.code for r in user.roles},
                      permissions=_perms_for(user))
    return ctx


def require(permission: str):
    def dep(ctx: AuthContext = Depends(current_user)) -> AuthContext:
        if not ctx.has(permission):
            raise ForbiddenError(f"Missing permission: {permission}.",
                                 code="PERMISSION_DENIED")
        return ctx
    return dep


def optional_user(request: Request, db: Session = Depends(get_db)) -> AuthContext | None:
    try:
        return current_user(request, db)
    except (UnauthorizedError, ForbiddenError):
        return None


# ---------------------------------------------------------------------------
# Resource scoping (design §06 §5)
# ---------------------------------------------------------------------------

def student_scope(ctx: AuthContext, db: Session) -> set[uuid.UUID] | None:
    """None ⇒ unrestricted (school staff). Otherwise the exact set of visible students."""
    user = ctx.user
    if user.parent_id is not None:
        rows = db.scalars(select(ParentStudentRelationship.student_id).where(
            ParentStudentRelationship.parent_id == user.parent_id,
            ParentStudentRelationship.effective_to.is_(None))).all()
        return set(rows)
    if user.student_id is not None:
        return {user.student_id}
    if user.teacher_id is not None:
        # Teachers: students enrolled in their assigned streams this year.
        year = db.scalar(select(TeacherAssignment.academic_year_id).where(
            TeacherAssignment.teacher_id == user.teacher_id,
            TeacherAssignment.is_active.is_(True)).limit(1))
        if year is None:
            return set()
        stream_ids = db.scalars(select(TeacherAssignment.class_stream_id).where(
            TeacherAssignment.teacher_id == user.teacher_id,
            TeacherAssignment.academic_year_id == year,
            TeacherAssignment.is_active.is_(True))).all()
        rows = db.scalars(select(Enrollment.student_id).where(
            Enrollment.class_stream_id.in_(stream_ids),
            Enrollment.status == "ACTIVE")).all() if stream_ids else []
        return set(rows)
    return None  # staff without profile link (admin/bursar/head)


def assert_student_visible(ctx: AuthContext, db: Session, student_id: uuid.UUID) -> None:
    scope = student_scope(ctx, db)
    if scope is not None and student_id not in scope:
        raise NotFoundError("Student not found.")  # uniform 404 — no scope probing


def teacher_stream_scope(ctx: AuthContext, db: Session) -> set[uuid.UUID] | None:
    """Assigned stream ids for teacher users; None for unrestricted staff;
    empty set for parent/student logins (they get no class-level views)."""
    user = ctx.user
    if user.teacher_id is None:
        return None if (user.parent_id is None and user.student_id is None) else set()
    rows = db.scalars(select(TeacherAssignment.class_stream_id).where(
        TeacherAssignment.teacher_id == user.teacher_id,
        TeacherAssignment.is_active.is_(True))).all()
    return set(rows)


def assert_stream_visible(ctx: AuthContext, db: Session, stream_id: uuid.UUID) -> None:
    """Teachers may only touch their assigned classes (REQ-TCH-02, journey J8)."""
    scope = teacher_stream_scope(ctx, db)
    if scope is not None and stream_id not in scope:
        raise NotFoundError("Class stream not found.")  # uniform 404 — no probing
