"""Grade scale validation rules (REQ-GRD-01)."""
import pytest

from app.core.errors import ConflictError
from app.services.grading import validate_bands

BANDS = [
    {"min_score": 80, "max_score": 100, "code": "A", "remark": "Excellent", "rank": 1},
    {"min_score": 0, "max_score": 79.99, "code": "F", "remark": "Fail", "rank": 6},
]


def test_valid_bands_pass():
    validate_bands(BANDS)


def test_overlapping_bands_rejected():
    bad = BANDS + [{"min_score": 70, "max_score": 90, "code": "B", "remark": "x", "rank": 2}]
    with pytest.raises(ConflictError) as ei:
        validate_bands(bad)
    assert ei.value.code == "BANDS_OVERLAP"


def test_out_of_range_rejected():
    bad = [{"min_score": -1, "max_score": 50, "code": "A", "remark": "x", "rank": 1}]
    with pytest.raises(ConflictError) as ei:
        validate_bands(bad)
    assert ei.value.code == "BAND_RANGE_INVALID"


def test_inverted_range_rejected():
    bad = [{"min_score": 90, "max_score": 50, "code": "A", "remark": "x", "rank": 1}]
    with pytest.raises(ConflictError):
        validate_bands(bad)


def test_duplicate_codes_rejected():
    bad = BANDS + [{"min_score": 101, "max_score": 101, "code": "A", "remark": "x", "rank": 9}]
    with pytest.raises(ConflictError) as ei:
        validate_bands(bad)
    assert ei.value.code in ("BAND_RANGE_INVALID", "BAND_CODE_DUPLICATE")
