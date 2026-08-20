"""Sliding-window rate limiter units (design §06)."""
import time

from app.core.ratelimit import SlidingWindowLimiter


def test_allows_up_to_limit_then_blocks():
    lim = SlidingWindowLimiter()
    for _ in range(5):
        assert lim.allow("k", 5, 60) is True
    assert lim.allow("k", 5, 60) is False


def test_keys_are_independent():
    lim = SlidingWindowLimiter()
    for _ in range(3):
        lim.allow("a", 3, 60)
    assert lim.allow("a", 3, 60) is False
    assert lim.allow("b", 3, 60) is True  # other key unaffected


def test_window_expiry_reopens():
    lim = SlidingWindowLimiter()
    for _ in range(2):
        assert lim.allow("w", 2, 1) is True
    assert lim.allow("w", 2, 1) is False
    time.sleep(1.05)
    assert lim.allow("w", 2, 1) is True  # window slid past


def test_reset_clears_state():
    lim = SlidingWindowLimiter()
    lim.allow("r", 1, 60)
    assert lim.allow("r", 1, 60) is False
    lim.reset()
    assert lim.allow("r", 1, 60) is True
