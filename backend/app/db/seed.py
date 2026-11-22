"""Dane demonstracyjne (opcjonalne, flaga --demo): filmy i seanse na 3 dni do przodu.

Dane stałe (gatunki, sale, miejsca) są w seed.sql i ładują się zawsze. Seanse muszą mieć daty
w przyszłości, więc powstają w Pythonie względem bieżącego czasu zegara.
Czasy slotów są w UTC; seanse w jednej sali co 3 godziny, więc przerwy techniczne się mieszczą.
"""

from __future__ import annotations

import sqlite3

from app.core.clock import Clock, system_clock
from app.db.connection import write_tx

DAY = 86_400
SLOT_HOURS = (10, 13, 16, 19)
PRICE_CENTS = {1: 2599, 2: 2299}

DEMO_FILMS = [
    # tytuł, opis, czas (min), wiek, gatunki, data premiery
    (
        "Nocny Pociąg",
        "Pasażerowie ostatniego kursu odkrywają, że ktoś z nich nie wsiadał na żadnej stacji.",
        98,
        16,
        ("Thriller", "Dramat"),
        "2026-10-09",
    ),
    (
        "Mała Wielka Podróż",
        "Dwie wiewiórki wyruszają przez cały las, żeby oddać zgubiony kasztan.",
        85,
        0,
        ("Animacja", "Komedia"),
        "2026-09-25",
    ),
    (
        "Granica Ciszy",
        "Tłumaczka z zawodu musi zdecydować, co przekazać, a co przemilczeć.",
        112,
        12,
        ("Dramat", "Romans"),
        "2026-11-06",
    ),
    (
        "Kod Orion",
        "Załoga stacji badawczej odbiera sygnał, który nie powinien istnieć.",
        140,
        12,
        ("Sci-Fi", "Akcja"),
        "2026-11-13",
    ),
]


def seed_demo(conn: sqlite3.Connection, clock: Clock = system_clock) -> int:
    """Wstawia filmy i seanse. Zwraca liczbę utworzonych seansów. Wymaga połączenia `owner`."""
    genre_id = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM genres")}
    buffer_min = {
        r["id"]: r["cleaning_buffer_min"]
        for r in conn.execute("SELECT id, cleaning_buffer_min FROM rooms")
    }
    created = 0
    with write_tx(conn):
        films = []
        for title, desc, minutes, age, genres, released in DEMO_FILMS:
            cur = conn.execute(
                "INSERT INTO films (title, description, duration_min, age_rating, release_date) VALUES (?,?,?,?,?)",
                (title, desc, minutes, age, released),
            )
            fid = cur.lastrowid
            films.append((fid, minutes))
            conn.executemany(
                "INSERT INTO film_genres (film_id, genre_id) VALUES (?,?)",
                [(fid, genre_id[g]) for g in genres],
            )

        first_midnight = (int(clock()) // DAY + 1) * DAY  # najbliższa północ UTC
        n = 0
        for day in range(3):
            for room_id in sorted(buffer_min):
                for hour in SLOT_HOURS:
                    film_id, minutes = films[n % len(films)]
                    n += 1
                    start = first_midnight + day * DAY + hour * 3600
                    end = start + (minutes + buffer_min[room_id]) * 60
                    conn.execute(
                        "INSERT INTO screenings (film_id, room_id, start_time, end_time, base_price_grosze) "
                        "VALUES (?,?,?,?,?)",
                        (film_id, room_id, start, end, PRICE_CENTS[room_id]),
                    )
                    created += 1
    return created
