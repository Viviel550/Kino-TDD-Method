from datetime import UTC, date, datetime

from app.core.timezone import day_bounds


def test_winter_day_starts_at_23_utc_the_day_before():
    start, end = day_bounds(date(2026, 11, 23))
    assert start == int(datetime(2026, 11, 22, 23, 0, tzinfo=UTC).timestamp())
    assert end - start == 24 * 3600


def test_summer_day_starts_at_22_utc_the_day_before():
    start, _ = day_bounds(date(2026, 7, 15))
    assert start == int(datetime(2026, 7, 14, 22, 0, tzinfo=UTC).timestamp())


def test_day_of_spring_time_change_has_23_hours():
    start, end = day_bounds(date(2026, 3, 29))
    assert end - start == 23 * 3600


def test_day_of_autumn_time_change_has_25_hours():
    start, end = day_bounds(date(2026, 10, 25))
    assert end - start == 25 * 3600
