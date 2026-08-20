"""File storage abstraction (REQ-TECH-04): metadata in DB, bytes in storage backend.

Local-disk backend for dev; S3-compatible backend slots in for prod without
touching business logic (design §13).
"""
import hashlib
import os
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.ids import uuid7
from app.models.academic import StoredFile

STORAGE_ROOT = Path(os.environ.get("SMS_STORAGE_DIR", "./storage"))


class StorageBackend:
    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...


class LocalDiskBackend(StorageBackend):
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = key.replace("..", "").lstrip("/")
        return self.root / safe

    def put(self, key: str, data: bytes) -> None:
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()


_backend: StorageBackend | None = None


def get_backend() -> StorageBackend:
    global _backend
    if _backend is None:
        _backend = LocalDiskBackend(STORAGE_ROOT)
    return _backend


def set_backend(backend: StorageBackend) -> None:
    """Used by tests / future S3 adapter."""
    global _backend
    _backend = backend


def store_file(db: Session, *, purpose: str, mime: str, data: bytes,
               actor_id: uuid.UUID | None = None, key_hint: str = "") -> StoredFile:
    digest = hashlib.sha256(data).hexdigest()[:16]
    key = f"{purpose.lower()}/{uuid7()}{('-' + key_hint) if key_hint else ''}.{digest}"
    get_backend().put(key, data)
    row = StoredFile(id=uuid7(), storage_key=key, purpose=purpose, mime=mime,
                     size_bytes=len(data), checksum=hashlib.sha256(data).hexdigest(),
                     created_by=actor_id)
    db.add(row)
    db.flush()
    return row


def read_file(file_id: uuid.UUID, db: Session) -> tuple[StoredFile, bytes]:
    row = db.get(StoredFile, file_id)
    if row is None:
        from app.core.errors import NotFoundError
        raise NotFoundError("File not found.")
    return row, get_backend().get(row.storage_key)
