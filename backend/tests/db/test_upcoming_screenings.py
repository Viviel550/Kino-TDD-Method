"""UC1-BR1.1 na poziomie bazy: widok v_upcoming_screenings (bez API)."""

from app.db.connection import connect


def upcoming_ids(db_path, clock):
    conn = connect(db_path, "guest", clock)
    try:
        return [row["screening_id"] for row in conn.execute("SELECT * FROM v_upcoming_screenings")]
    finally:
        conn.close()


def test_screening_that_has_started_is_not_upcoming(db_path, clock, add_film, add_screening, at):
    film_id = add_film("Nocny Pociąg")
    started = add_screening(film_id, start_time=at("2026-11-22", 18))
    later = add_screening(film_id, start_time=at("2026-11-22", 21), room_id=2)
    assert upcoming_ids(db_path, clock) == [started, later]  # teraz 12:00, oba przed nami

    clock.advance(7 * 3600)  # 19:00: seans z 18:00 już trwa

    assert upcoming_ids(db_path, clock) == [later]


def test_screening_starting_exactly_now_is_not_upcoming(
    db_path, clock, add_film, add_screening, at
):
    film_id = add_film("Nocny Pociąg")
    add_screening(film_id, start_time=at("2026-11-22", 18))
    clock.advance(6 * 3600)  # dokładnie 18:00

    assert upcoming_ids(db_path, clock) == []  # start_time > teraz, nie >=


def test_screening_one_second_before_start_is_still_upcoming(
    db_path, clock, add_film, add_screening, at
):
    film_id = add_film("Nocny Pociąg")
    screening_id = add_screening(film_id, start_time=at("2026-11-22", 18))
    clock.advance(6 * 3600 - 1)  # 17:59:59

    assert upcoming_ids(db_path, clock) == [screening_id]
