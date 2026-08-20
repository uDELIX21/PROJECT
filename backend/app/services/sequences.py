"""Per-school document sequences (admission codes, receipt numbers…)."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ids import uuid7
from app.models.core import DocumentSequence


def next_value(db: Session, school_id: uuid.UUID, key: str, prefix: str = "") -> tuple[str, int]:
    """Atomically increment and return ('PREFIX-000123', 123)."""
    row = db.scalar(select(DocumentSequence).where(
        DocumentSequence.school_id == school_id, DocumentSequence.key == key)
        .with_for_update())
    if row is None:
        row = DocumentSequence(id=uuid7(), school_id=school_id, key=key,
                               prefix=prefix, current_value=0)
        db.add(row)
        db.flush()
    row.current_value += 1
    db.flush()
    return f"{row.prefix}-{row.current_value:04d}", row.current_value
