"""Model registry — import all models so Base.metadata is complete."""
from app.models.base import Base  # noqa: F401
from app.models import (academic, audit, auth, core, finance, imports,  # noqa: F401
                        operations, sync)

__all__ = ["Base", "academic", "audit", "auth", "core", "finance", "imports",
           "operations", "sync"]
