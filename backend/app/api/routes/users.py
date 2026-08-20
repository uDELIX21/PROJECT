"""User administration: accounts, roles, unlock, reset links (REQ-RBAC-01)."""
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import rbac
from app.api.deps import AuthContext, current_user, get_school, require
from app.core.audit import audit
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import ConflictError, NotFoundError
from app.core.ids import uuid7
from app.core import security
from app.models.auth import Role, User, UserRole
from app.schemas.requests import RoleGrantIn, UserCreateIn, UserPatchIn
from app.services import auth_service

router = APIRouter(prefix="/users", tags=["users"])


def _summary(u: User) -> dict:
    return {"id": str(u.id), "username": u.username, "display_name": u.display_name,
            "email": u.email, "status": u.status,
            "roles": sorted({r.code for r in u.roles}),
            "teacher_id": str(u.teacher_id) if u.teacher_id else None,
            "parent_id": str(u.parent_id) if u.parent_id else None,
            "student_id": str(u.student_id) if u.student_id else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None}


def _get_role(db: Session, school_id: uuid.UUID, code: str) -> Role:
    role = db.scalar(select(Role).where(Role.school_id == school_id, Role.code == code))
    if role is None:
        raise NotFoundError(f"Role '{code}' not found.", code="ROLE_UNKNOWN")
    return role


@router.get("")
def list_users(role_code: str | None = None, status: str | None = None,
               limit: int = Query(default=20, ge=1, le=100),
               offset: int = Query(default=0, ge=0),
               ctx: AuthContext = Depends(require(rbac.MANAGE_USERS)),
               db: Session = Depends(get_db)):
    stmt = select(User)
    if role_code:
        stmt = stmt.join(User.roles).where(Role.code == role_code)
    if status:
        stmt = stmt.where(User.status == status)
    rows = db.scalars(stmt.order_by(User.username).limit(limit).offset(offset)).all()
    return {"items": [_summary(u) for u in rows], "limit": limit, "offset": offset}


@router.post("", status_code=201)
def create_user(data: UserCreateIn, request: Request,
                ctx: AuthContext = Depends(require(rbac.MANAGE_USERS)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    dup = db.scalar(select(User).where(User.username == data.username))
    if dup is not None:
        raise ConflictError("Username already taken.", code="USERNAME_EXISTS")
    profiles = [p for p in (data.teacher_id, data.parent_id, data.student_id) if p]
    if len(profiles) > 1:
        raise ConflictError("A user may link to at most one profile.", code="PROFILE_CONFLICT")
    user = User(id=uuid7(), username=data.username,
                password_hash=security.hash_password(data.password, get_settings()),
                display_name=data.display_name, email=data.email,
                teacher_id=data.teacher_id, parent_id=data.parent_id,
                student_id=data.student_id)
    db.add(user)
    db.flush()
    for code in data.role_codes:
        role = _get_role(db, school.id, code)
        db.add(UserRole(user_id=user.id, role_id=role.id, granted_by=ctx.user.id))
    audit(db, actor_id=ctx.user.id, action="user.created", entity_type="user",
          entity_id=user.id, new={"username": user.username, "roles": data.role_codes},
          request=request)
    db.commit()
    return _summary(user)


@router.get("/me")
def me_alias(ctx: AuthContext = Depends(current_user)):
    return _summary(ctx.user)


@router.patch("/{user_id}")
def patch_user(user_id: uuid.UUID, data: UserPatchIn, request: Request,
               ctx: AuthContext = Depends(require(rbac.MANAGE_USERS)),
               db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    if user.id == ctx.user.id and data.status == "DEACTIVATED":
        raise ConflictError("You cannot deactivate your own account.", code="SELF_DEACTIVATE")
    previous, new = {}, {}
    if data.status and user.status != data.status:
        previous["status"] = user.status
        user.status = data.status
        new["status"] = data.status
        if data.status == "DEACTIVATED":
            auth_service.revoke_user_sessions(db, user.id)
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.email is not None:
        user.email = data.email
    if new:
        audit(db, actor_id=ctx.user.id, action="user.status_changed", entity_type="user",
              entity_id=user.id, previous=previous, new=new, request=request)
    db.commit()
    return _summary(user)


@router.post("/{user_id}/roles")
def grant_role(user_id: uuid.UUID, data: RoleGrantIn, request: Request,
               ctx: AuthContext = Depends(require(rbac.MANAGE_USERS)),
               db: Session = Depends(get_db)):
    school = get_school(db)
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    role = _get_role(db, school.id, data.role_code)
    exists = db.scalar(select(UserRole).where(UserRole.user_id == user.id,
                                              UserRole.role_id == role.id))
    if exists is None:
        db.add(UserRole(user_id=user.id, role_id=role.id, granted_by=ctx.user.id))
        audit(db, actor_id=ctx.user.id, action="role.granted", entity_type="user",
              entity_id=user.id, new={"role": role.code}, reason=data.reason, request=request)
    db.commit()
    return _summary(user)


@router.delete("/{user_id}/roles/{role_code}", status_code=200)
def revoke_role(user_id: uuid.UUID, role_code: str, request: Request,
                ctx: AuthContext = Depends(require(rbac.MANAGE_USERS)),
                db: Session = Depends(get_db)):
    school = get_school(db)
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    role = _get_role(db, school.id, role_code)
    row = db.scalar(select(UserRole).where(UserRole.user_id == user.id,
                                           UserRole.role_id == role.id))
    if row is not None:
        # bootstrap guard: never strip the last SUPER_ADMIN
        if role.code == rbac.SUPER_ADMIN:
            admins = db.scalars(select(User).join(User.roles).where(Role.code == rbac.SUPER_ADMIN)).all()
            if len([a for a in admins]) <= 1:
                raise ConflictError("Cannot remove the last Super Admin.", code="LAST_ADMIN")
        db.delete(row)
        audit(db, actor_id=ctx.user.id, action="role.revoked", entity_type="user",
              entity_id=user.id, previous={"role": role.code}, request=request)
    db.commit()
    return _summary(user)


@router.post("/{user_id}/unlock")
def unlock(user_id: uuid.UUID, request: Request,
           ctx: AuthContext = Depends(require(rbac.MANAGE_USERS)),
           db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    user.locked_until = None
    user.failed_login_count = 0
    if user.status == "LOCKED":
        user.status = "ACTIVE"
    audit(db, actor_id=ctx.user.id, action="user.unlocked", entity_type="user",
          entity_id=user.id, request=request)
    db.commit()
    return _summary(user)


@router.post("/{user_id}/password-reset-link")
def issue_reset_link(user_id: uuid.UUID, request: Request,
                     ctx: AuthContext = Depends(require(rbac.MANAGE_USERS)),
                     db: Session = Depends(get_db)):
    """Assisted recovery (design §06): admin issues a one-time token in person."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    token = auth_service.create_reset_token(db, user, purpose="RECOVERY", request=request)
    audit(db, actor_id=ctx.user.id, action="recovery.code_issued", entity_type="user",
          entity_id=user.id, request=request)
    db.commit()
    return {"ok": True, "dev_token": token if get_settings().dev_mode else None}
