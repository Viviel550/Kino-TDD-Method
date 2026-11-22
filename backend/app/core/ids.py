from __future__ import annotations

import os
import time
import uuid


def uuid7(now_s: float | None = None) -> str:
    """UUIDv7 (RFC 9562): 48 bitów czasu w ms + 74 bity losowe. Zapis małymi literami.
    Używany jako id i kod rezerwacji."""
    ts_ms = int((time.time() if now_s is None else now_s) * 1000)
    b = bytearray(ts_ms.to_bytes(6, "big") + os.urandom(10))
    b[6] = (b[6] & 0x0F) | 0x70
    b[8] = (b[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(b)))
