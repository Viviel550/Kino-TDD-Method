import sqlite3
from datetime import UTC, date, datetime, time
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.db.session import guest_conn
from app.schemas.screening import ScreeningOut

router = APIRouter()

DAY_SECONDS = 86_400


@router.get("/screenings")
def list_screenings(
    day: Annotated[date, Query(alias="date")],
    title: str | None = None,
    genre: str | None = None,
    conn: sqlite3.Connection = Depends(guest_conn),
) -> list[ScreeningOut]:
    """Nadchodzące seanse z jednego dnia (doba UTC), opcjonalnie przefiltrowane."""
    day_start = int(datetime.combine(day, time.min, tzinfo=UTC).timestamp())

    # Widok v_upcoming_screenings zwraca tylko seanse, które jeszcze się nie zaczęły (BR1.1).
    # W tekście SQL są wyłącznie stałe fragmenty, wartości od użytkownika idą jako parametry.
    sql = "SELECT * FROM v_upcoming_screenings WHERE start_time >= ? AND start_time < ?"
    params: list[object] = [day_start, day_start + DAY_SECONDS]
    if title:
        sql += " AND instr(lower(film_title), lower(?)) > 0"
        params.append(title)
    if genre:
        sql += (
            " AND EXISTS (SELECT 1 FROM film_genres fg JOIN genres g ON g.id = fg.genre_id"
            " WHERE fg.film_id = v_upcoming_screenings.film_id AND g.name = ?)"
        )
        params.append(genre)
    sql += " ORDER BY start_time"  # BR1.2

    rows = conn.execute(sql, params).fetchall()
    return [ScreeningOut.model_validate(dict(row)) for row in rows]
