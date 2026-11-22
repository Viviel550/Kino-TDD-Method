"""Role bazy: SQLite nie ma użytkowników ani GRANT, więc "uprawnienia" realizuje authorizer.

Role:
  owner  - migracje, seed, testy (bez ograniczeń; nie używać w obsłudze żądań HTTP)
  guest  - endpointy publiczne
  admin  - endpointy /admin/* po zweryfikowaniu sesji
  auth   - logowanie i weryfikacja sesji; jedyna rola widząca admin_accounts

Operacje z triggerów i widoków (argument `source` != None) są dopuszczane: instrukcja najwyższego
poziomu jest już sprawdzona, a triggery/widoki to zaufane obiekty schematu. Authorizer ogranicza
tabele i kolumny, nie wiersze: kody rezerwacji chroni zapytanie z WHERE id = ? i rate limiting.
"""
from __future__ import annotations

import sqlite3
from typing import Callable

# Kody akcji authorizera (stałe SQLite; nie wszystkie wersje Pythona je eksportują)
A_DELETE, A_INSERT, A_PRAGMA, A_READ, A_SELECT = 9, 18, 19, 20, 21
A_TRANSACTION, A_UPDATE, A_FUNCTION, A_SAVEPOINT, A_RECURSIVE = 22, 23, 31, 32, 33

ALL = "*"
SENSITIVE = {"admin_accounts", "admin_sessions"}

POLICIES: dict[str, dict] = {
    "guest": {
        # odczyt top-level (widoki są czytane przez `source`)
        "read": {"v_films_public": ALL, "v_screenings": ALL, "v_upcoming_screenings": ALL,
                 "v_seat_map": ALL, "v_reservation_details": ALL, "v_reservation_seats": ALL,
                 "v_rooms": ALL, "genres": ALL, "film_genres": ALL,
                 # Kolumny kluczy: SQLite sprawdza klucze obce jako zwykłe instrukcje top-level
                 # (source=None), a UPDATE ... WHERE id=? AND status='active' czyta id i status.
                 "reservations": {"id", "status", "screening_id"},
                 "screenings": {"id"}, "seats": {"id"},
                 "reservation_seats": {"reservation_id", "screening_id", "seat_id"}},
        "insert": {"reservations", "reservation_seats"},
        "update": {"reservations": {"status", "cancelled_at"}},
        "delete": set(),
    },
    "admin": {
        "read": {t: ALL for t in (
            "films", "genres", "film_genres", "rooms", "seats", "screenings",
            "reservations", "reservation_seats", "v_rooms", "v_films_public", "v_screenings",
            "v_upcoming_screenings", "v_seat_map", "v_reservation_details", "v_reservation_seats")},
        "insert": {"films", "genres", "film_genres", "screenings"},
        "update": {"films": ALL, "screenings": ALL,
                   "reservations": {"status", "cancelled_at", "confirmed"}},
        "delete": {"film_genres", "screenings"},       # filmy: soft delete (UPDATE films.deleted_at)
    },
    "auth": {
        "read": {"admin_accounts": ALL, "admin_sessions": ALL},
        "insert": {"admin_sessions"},
        "update": {"admin_sessions": {"expires_at"}},
        "delete": {"admin_sessions"},
    },
}


def _allowed(spec, table: str, column: str | None = None) -> bool:
    if isinstance(spec, set):                       # insert/delete: zbiór tabel
        return table in spec
    cols = spec.get(table)
    if cols is None:
        return False
    return cols == ALL or column in cols


def make_authorizer(role: str) -> Callable:
    policy = POLICIES[role]

    def authorizer(action, arg1, arg2, dbname, source):
        if source is not None:                       # trigger lub widok
            return sqlite3.SQLITE_OK
        if action in (A_SELECT, A_FUNCTION, A_TRANSACTION, A_SAVEPOINT, A_RECURSIVE):
            return sqlite3.SQLITE_OK
        if action == A_READ:
            if arg2 in (None, ""):
                # Odczyt bez kolumny (rowid / zliczanie / spłaszczone JOIN-y widoków) ujawnia co najwyżej
                # liczbę wierszy. Blokujemy go tylko dla tabel z danymi uwierzytelniającymi.
                ok = arg1 not in SENSITIVE or arg1 in policy["read"]
            else:
                ok = _allowed(policy["read"], arg1, arg2)
        elif action == A_INSERT:
            ok = _allowed(policy["insert"], arg1)
        elif action == A_DELETE:
            ok = _allowed(policy["delete"], arg1)
        elif action == A_UPDATE:
            ok = _allowed(policy["update"], arg1, arg2)
        else:                                        # DDL, ATTACH, PRAGMA, ...
            ok = False
        return sqlite3.SQLITE_OK if ok else sqlite3.SQLITE_DENY

    return authorizer
