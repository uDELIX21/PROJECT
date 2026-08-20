"""UUIDv7 generation (RFC 9562): time-ordered, unenumerable primary keys."""
import os
import time
import uuid


def uuid7() -> uuid.UUID:
    ts_ms = int(time.time() * 1000)
    rand = os.urandom(10)
    raw = bytearray(ts_ms.to_bytes(6, "big") + rand)
    raw[6] = (raw[6] & 0x0F) | 0x70  # version 7
    raw[8] = (raw[8] & 0x3F) | 0x80  # RFC 4122 variant
    return uuid.UUID(bytes=bytes(raw))
