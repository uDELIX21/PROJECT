"""Alembic migration applies cleanly on a fresh database (REQ-DB-01)."""
import os
import sqlite3
import tempfile

from alembic import command
from alembic.config import Config


def test_upgrade_head_on_fresh_db(monkeypatch):
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    url = f"sqlite:///{tmp.name}"
    # env.py honors DATABASE_URL — point it at the scratch DB for this test
    monkeypatch.setenv("DATABASE_URL", url)
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini"))
    cfg.set_main_option("script_location",
                        os.path.join(os.path.dirname(__file__), "..", "..", "migrations"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")

    con = sqlite3.connect(tmp.name)
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for required in ("schools", "users", "roles", "permissions", "students",
                     "enrollments", "academic_years", "terms", "class_streams",
                     "parent_guardians", "teacher_assignments", "audit_log",
                     "sessions", "document_sequences"):
        assert required in tables, f"migration missing table {required}"
    os.unlink(tmp.name)
