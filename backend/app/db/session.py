"""Zależności FastAPI: połączenie na żądanie, osobne dla każdej roli.
GuesConn - gość
AdminConn - Admin
AuthConn - Weryfikacja
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import Depends

from app.core.clock import Clock, system_clock
from app.core.config import get_settings
from app.db.connection import connect


def get_clock() -> Clock:
    return system_clock


ClockDep = Annotated[Clock, Depends(get_clock)]


def _connection_dependency(role: str) -> Callable[..., Iterator[sqlite3.Connection]]:
    def dependency(clock: ClockDep) -> Iterator[sqlite3.Connection]:
        conn = connect(get_settings().db_path, role, clock)
        try:
            yield conn
        finally:
            conn.close()

    dependency.__name__ = f"{role}_conn"
    return dependency


guest_conn = _connection_dependency("guest")  # endpointy publiczne
admin_conn = _connection_dependency("admin")  # /admin/*, po sprawdzeniu sesji
auth_conn = _connection_dependency("auth")  # logowanie i weryfikacja sesji

GuestConn = Annotated[sqlite3.Connection, Depends(guest_conn)]
AdminConn = Annotated[sqlite3.Connection, Depends(admin_conn)]
AuthConn = Annotated[sqlite3.Connection, Depends(auth_conn)]
