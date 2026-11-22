"""Mapowanie błędów bazy (kody z triggerów i constraintów) na status HTTP."""

from __future__ import annotations

import sqlite3

ERROR_MAP: dict[str, int] = {
    "SEAT_TAKEN": 409,
    "SCREENING_OVERLAP": 409,
    "FILM_HAS_ACTIVE_RESERVATIONS": 409,
    "FILM_HAS_FUTURE_SCREENINGS": 409,
    "ROOM_HAS_FUTURE_SCREENINGS": 409,
    "SCREENING_HAS_RESERVATIONS": 409,
    "RESERVATION_NOT_ACTIVE": 409,
    "SEAT_WRONG_ROOM": 422,
    "SCREENING_IN_PAST": 422,
    "SCREENING_NOT_BOOKABLE": 422,
    "CANT_CANCEL_LESS_THAN_30_MIN_BEFORE": 422,
    "TOO_MANY_SEATS": 400,
    "SCREENING_NOT_FOUND": 404,
    "FILM_DELETED": 404,
}


def classify_error(exc: sqlite3.Error) -> tuple[int, str]:
    """Zamienia wyjątek sqlite3 na (status HTTP, kod błędu)."""
    msg = str(exc)
    if msg in ERROR_MAP:
        return ERROR_MAP[msg], msg
    if "reservation_seats.screening_id, reservation_seats.seat_id" in msg:
        return 409, "SEAT_TAKEN"
    if isinstance(exc, sqlite3.IntegrityError):
        if "FOREIGN KEY" in msg:
            return 409, "FOREIGN_KEY"  # np. usunięcie seansu z rezerwacjami
        if msg.startswith("CHECK constraint failed"):
            return 400, "VALIDATION"
    return 500, "INTERNAL"
