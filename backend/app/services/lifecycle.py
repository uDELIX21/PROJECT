"""Student lifecycle state machine (REQ-STU-01, BR-S01)."""
from app.core.errors import ConflictError

# status -> allowed next statuses
TRANSITIONS: dict[str, set[str]] = {
    "APPLICANT": {"ADMITTED", "WITHDRAWN"},
    "ADMITTED": {"ENROLLED", "WITHDRAWN"},
    "ENROLLED": {"ACTIVE", "WITHDRAWN", "TRANSFERRED", "SUSPENDED"},
    "ACTIVE": {"PROMOTED", "REPEATED", "WITHDRAWN", "TRANSFERRED", "SUSPENDED", "GRADUATED"},
    "SUSPENDED": {"ACTIVE", "WITHDRAWN", "TRANSFERRED"},
    "PROMOTED": {"ACTIVE"},
    "REPEATED": {"ACTIVE"},
    "WITHDRAWN": {"APPLICANT"},  # re-application starts a fresh admission
    "TRANSFERRED": set(),
    "GRADUATED": set(),
}

ALL_STATUSES = set(TRANSITIONS)


def can_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, set())


def assert_transition(current: str, target: str) -> None:
    if target not in ALL_STATUSES:
        raise ConflictError(f"Unknown student status '{target}'.", code="STATUS_UNKNOWN")
    if not can_transition(current, target):
        raise ConflictError(
            f"Illegal student status transition: {current} → {target}.",
            code="ILLEGAL_TRANSITION")
