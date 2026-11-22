"""Hasła administratorów (BR7.1): bcrypt.

bcrypt używa tylko pierwszych 72 bajtów hasła, a nowsze wersje biblioteki odrzucają dłuższe hasła
błędem. Dlatego limit jest jawny: hasło dłuższe niż 72 bajty w UTF-8 (to bajty, nie znaki, więc
polskie litery liczą się podwójnie) jest odrzucane już przy ustawianiu.
"""
from __future__ import annotations

import bcrypt

MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Hasło może mieć najwyżej {MAX_PASSWORD_BYTES} bajtów (UTF-8).")
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("ascii")


def verify_password(password_hash: str, password: str) -> bool:
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:        # takiego hasła nie dało się ustawić, więc nie może pasować
        return False
    try:
        return bcrypt.checkpw(raw, password_hash.encode("ascii"))
    except ValueError:                       # uszkodzony hash w bazie
        return False
