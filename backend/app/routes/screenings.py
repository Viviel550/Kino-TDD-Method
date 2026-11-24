from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.timezone import CINEMA_TZ, day_bounds
from app.db.session import ClockDep, GuestConn
from app.schemas.screening import ScreeningOut

router = APIRouter()

DAY_SECONDS = 86_400


@router.get("/screenings")
def list_screenings(
    clock: ClockDep,
    conn: GuestConn,
    title: str | None = None,
    genre: str | None = None,
    day: Annotated[date | None, Query(alias="date")] = None,
) -> list[ScreeningOut]:
    """Nadchodzące seanse z jednego dnia (doba UTC), opcjonalnie przefiltrowane.

    Bez parametru date zwraca seanse z dzisiaj."""
    if day is None:
        day = datetime.fromtimestamp(clock(), CINEMA_TZ).date()
    day_start, day_end = day_bounds(day)
    # Widok v_upcoming_screenings zwraca tylko seanse, które jeszcze się nie zaczęły (BR1.1).
    # W tekście SQL są wyłącznie stałe fragmenty, wartości od użytkownika idą jako parametry.
    sql = "SELECT * FROM v_upcoming_screenings WHERE start_time >= ? AND start_time < ?"
    params: list[object] = [day_start, day_end]
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
