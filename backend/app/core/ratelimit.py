"""In-memory sliding-window rate limiter (Redis-backed replacement later, design §06)."""
import time
import threading
from collections import defaultdict

from fastapi import Request

from app.core.errors import RateLimitedError


class SlidingWindowLimiter:
    def __init__(self) -> None:
        self._events: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            events = self._events[key]
            cutoff = now - window_seconds
            while events and events[0] < cutoff:
                events.pop(0)
            if len(events) >= limit:
                return False
            events.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


limiter = SlidingWindowLimiter()


def rate_limit(request: Request, group: str, key: str, limit: int, window_seconds: int) -> None:
    """Raise 429 when the bucket is exhausted (fail-closed on abuse)."""
    from app.core.config import get_settings
    if not get_settings().ratelimit_enabled:
        return
    bucket = f"{group}:{key or (request.client.host if request.client else 'global')}"
    if not limiter.allow(bucket, limit, window_seconds):
        raise RateLimitedError(retry_after=window_seconds)
