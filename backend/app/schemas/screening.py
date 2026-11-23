from datetime import datetime

from pydantic import BaseModel


class ScreeningOut(BaseModel):
    """Seans na liście repertuaru (GET /screenings)."""

    screening_id: int
    film_id: int
    film_title: str
    duration_min: int
    age_rating: int
    room_id: int
    room_name: str
    start_time: datetime  # w bazie sekundy unix (UTC), w JSON ISO 8601, np. 2026-11-23T18:00:00Z
    base_price_grosze: int
