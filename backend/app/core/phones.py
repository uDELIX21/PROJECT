"""Ghana phone normalization → +233XXXXXXXXX (REQ-COM-02, BR-N01)."""
import re

_MOBILE_NATIONAL = re.compile(r"^[25]\d{8}$")


def normalize_ghana_phone(raw: str | None) -> str | None:
    """Return E.164 Ghana format or None if not a valid Ghana number."""
    if not raw:
        return None
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("+"):
        digits = digits[1:]
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) == 10:
        digits = "233" + digits[1:]
    if digits.startswith("233") and len(digits) == 12 and _MOBILE_NATIONAL.match(digits[3:]):
        return "+" + digits
    return None
