"""Otwieranie połączeń SQLite z pragmami, funkcją app_now() i authorizerem roli."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

from app.core.clock import Clock, system_clock
from app.db.permissions import make_authorizer


def connect(path: str | os.PathLike, role: str = "owner", clock: Clock = system_clock) -> sqlite3.Connection:
    """Nowe połączenie dla danej roli (owner/guest/admin/auth).

    `clock` zasila funkcję SQL app_now() używaną przez triggery i widoki; w testach można go przesuwać.
    check_same_thread=False: zależności FastAPI mogą otworzyć i zamknąć połączenie w różnych wątkach
    puli. To bezpieczne, bo każde żądanie ma własne połączenie używane sekwencyjnie.
    """
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False)   # transakcje: write_tx
    conn.row_factory = sqlite3.Row
    conn.create_function("app_now", 0, lambda: int(clock()))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA recursive_triggers = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    if str(path) != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")
    if role != "owner":
        conn.set_authorizer(make_authorizer(role))
    return conn


@contextmanager
def write_tx(conn: sqlite3.Connection):
    """Transakcja zapisu. BEGIN IMMEDIATE zajmuje blokadę zapisu od razu, więc dwa równoległe
    żądania na to samo miejsce wykonują się szeregowo."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    else:
        conn.execute("COMMIT")
