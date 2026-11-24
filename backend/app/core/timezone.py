from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

CINEMA_TZ = ZoneInfo("Europe/Warsaw")


def day_bounds(day: date) -> tuple[int, int]:
    """Początek i koniec doby w czasie kina jako unix epoch (UTC), koniec wyłącznie."""
    start = datetime.combine(day, time.min, tzinfo=CINEMA_TZ)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=CINEMA_TZ)
    return int(start.timestamp()), int(end.timestamp())
