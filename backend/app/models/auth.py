"""Authentication & RBAC models: users, roles, permissions, sessions, reset tokens."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, IdMixin, TimestampMixin, utcnow


class Permission(Base):
    """Global permission catalog (no school scope); codes are fixed in code too."""
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(48), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))


class Role(Base, IdMixin, TimestampMixin):
    __tablename__ = "roles"

    school_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("schools.id"), index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_roles_school_code"),)

    permissions: Mapped[list["Permission"]] = relationship(
        secondary="role_permissions", lazy="selectin", viewonly=True)


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_code: Mapped[str] = mapped_column(
        String(48), ForeignKey("permissions.code", ondelete="CASCADE"), primary_key=True)


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE", index=True)  # ACTIVE|LOCKED|DEACTIVATED
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # at most one profile link of each kind
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("teachers.id"), unique=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parent_guardians.id"), unique=True)
    student_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("students.id"), unique=True)

    roles: Mapped[list["Role"]] = relationship(
        secondary="user_roles", lazy="selectin",
        primaryjoin="User.id == UserRole.user_id",
        secondaryjoin="Role.id == UserRole.role_id",
        foreign_keys="[UserRole.user_id, UserRole.role_id]")


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    granted_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SessionRecord(Base, IdMixin):
    """Server-side revocable session (design §06). Only the token hash is stored."""
    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    csrf_token: Mapped[str] = mapped_column(String(64), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordResetToken(Base, IdMixin):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(16), default="RESET")  # RESET|RECOVERY
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
