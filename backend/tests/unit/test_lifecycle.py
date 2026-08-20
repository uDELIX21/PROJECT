"""Student lifecycle state machine (REQ-STU-01, BR-S01)."""
import pytest

from app.core.errors import ConflictError
from app.services.lifecycle import TRANSITIONS, assert_transition, can_transition


def test_happy_path():
    for a, b in [("APPLICANT", "ADMITTED"), ("ADMITTED", "ENROLLED"),
                 ("ENROLLED", "ACTIVE"), ("ACTIVE", "PROMOTED"),
                 ("PROMOTED", "ACTIVE"), ("ACTIVE", "GRADUATED")]:
        assert can_transition(a, b), f"{a} -> {b} should be allowed"


def test_terminal_states():
    assert TRANSITIONS["GRADUATED"] == set()
    assert TRANSITIONS["TRANSFERRED"] == set()


def test_illegal_transitions():
    for a, b in [("APPLICANT", "ACTIVE"), ("ADMITTED", "GRADUATED"),
                 ("GRADUATED", "ACTIVE"), ("WITHDRAWN", "ACTIVE"),
                 ("TRANSFERRED", "ACTIVE"), ("ACTIVE", "ADMITTED")]:
        assert not can_transition(a, b), f"{a} -> {b} should be rejected"


def test_assert_raises_on_illegal():
    with pytest.raises(ConflictError) as ei:
        assert_transition("GRADUATED", "ACTIVE")
    assert ei.value.code == "ILLEGAL_TRANSITION"


def test_unknown_status():
    with pytest.raises(ConflictError) as ei:
        assert_transition("ACTIVE", "FROBNICATED")
    assert ei.value.code == "STATUS_UNKNOWN"
