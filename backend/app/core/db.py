"""Engine & session factory."""
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def build_engine(database_url: str | None = None, echo: bool | None = None):
    settings = get_settings()
    url = database_url or settings.database_url
    echo_flag = settings.database_echo if echo is None else echo
    kwargs: dict = {"echo": echo_flag, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.close()
    return engine


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False,
                                     expire_on_commit=False, future=True)
    return _SessionLocal


def reset_engine_cache() -> None:
    """Used by tests to rebind after swapping DATABASE_URL."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    get_settings.cache_clear()


def get_db() -> Iterator[Session]:
    factory = get_session_factory()
    db = factory()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
