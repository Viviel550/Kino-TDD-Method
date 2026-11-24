from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.clock import FakeClock
from app.db.connection import connect
from app.db.init_db import init_database
from app.db.session import get_clock
from app.main import create_app

# Ustalone "teraz" we wszystkich testach: 2026-11-22 12:00 UTC.
NOW = datetime(2026, 11, 22, 12, 0, tzinfo=UTC)


@pytest.fixture
def clock():
    return FakeClock(NOW.timestamp())


@pytest.fixture
def db_path(tmp_path, clock):
    """Świeża baza (schemat + dane stałe: gatunki, sale, miejsca) w pliku tymczasowym."""
    path = tmp_path / "test.db"
    init_database(path, clock)
    return path


@pytest.fixture
def client(db_path, clock, monkeypatch):
    """Klient API na bazie testowej i zegarze testowym."""
    monkeypatch.setenv("CINEMA_DB_PATH", str(db_path))
    app = create_app()
    app.dependency_overrides[get_clock] = lambda: clock
    return TestClient(app)


@pytest.fixture
def at():
    """at("2026-11-23", 18) -> unix epoch (UTC) dla 23.11.2026 18:00 UTC."""

    def _at(day, hour, minute=0):
        moment = datetime.fromisoformat(f"{day}T{hour:02d}:{minute:02d}:00+00:00")
        return int(moment.timestamp())

    return _at


@pytest.fixture
def add_film(db_path, clock):
    """Dodaje film (rola owner) i zwraca jego id. Gatunki podaje się po nazwie, np. "Dramat"."""

    def _add_film(title, duration_min=100, genres=()):
        conn = connect(db_path, "owner", clock)
        try:
            cur = conn.execute(
                "INSERT INTO films (title, duration_min, age_rating) VALUES (?, ?, ?)",
                (title, duration_min, 12),
            )
            film_id = cur.lastrowid
            for name in genres:
                conn.execute(
                    "INSERT INTO film_genres (film_id, genre_id) "
                    "SELECT ?, id FROM genres WHERE name = ?",
                    (film_id, name),
                )
            return film_id
        finally:
            conn.close()

    return _add_film


@pytest.fixture
def add_screening(db_path, clock):
    """Dodaje seans (rola owner) i zwraca jego id. end_time liczy z czasu filmu i przerwy sali."""

    def _add_screening(film_id, start_time, room_id=1, price_grosze=2500):
        conn = connect(db_path, "owner", clock)
        try:
            row = conn.execute(
                "SELECT f.duration_min + r.cleaning_buffer_min AS total_min "
                "FROM films f, rooms r WHERE f.id = ? AND r.id = ?",
                (film_id, room_id),
            ).fetchone()
            end_time = start_time + row["total_min"] * 60
            cur = conn.execute(
                "INSERT INTO screenings (film_id, room_id, start_time, end_time, "
                "base_price_grosze) VALUES (?, ?, ?, ?, ?)",
                (film_id, room_id, start_time, end_time, price_grosze),
            )
            return cur.lastrowid
        finally:
            conn.close()

    return _add_screening
