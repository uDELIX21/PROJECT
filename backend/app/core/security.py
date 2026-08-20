"""Password hashing & token helpers (design §06)."""
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import Settings, get_settings


def _hasher(settings: Settings | None = None) -> PasswordHasher:
    s = settings or get_settings()
    return PasswordHasher(
        time_cost=s.argon_time_cost,
        memory_cost=s.argon_memory_cost_kib,
        parallelism=s.argon_parallelism,
    )


def hash_password(password: str, settings: Settings | None = None) -> str:
    return _hasher(settings).hash(password)


def verify_password(password_hash: str, password: str, settings: Settings | None = None) -> bool:
    try:
        return _hasher(settings).verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
