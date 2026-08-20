"""Ghana phone normalization (REQ-COM-02)."""
from app.core.phones import normalize_ghana_phone


def test_local_format():
    assert normalize_ghana_phone("0241234567") == "+233241234567"


def test_international_with_spaces():
    assert normalize_ghana_phone("+233 24 123 4567") == "+233241234567"


def test_double_zero_prefix():
    assert normalize_ghana_phone("00233201234567") == "+233201234567"


def test_already_normalized():
    assert normalize_ghana_phone("+233551234567") == "+233551234567"


def test_rejects_short_number():
    assert normalize_ghana_phone("02412345") is None


def test_rejects_non_ghana_country():
    assert normalize_ghana_phone("+441234567890") is None


def test_rejects_landline_style_prefix():
    # national numbers must start with 2 or 5 (mobile)
    assert normalize_ghana_phone("0311234567") is None


def test_rejects_empty():
    assert normalize_ghana_phone("") is None
    assert normalize_ghana_phone(None) is None
