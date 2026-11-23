"""UC1: przeglądanie repertuaru, GET /screenings?date=YYYY-MM-DD[&title=...][&genre=...]."""

from datetime import UTC, datetime

import pytest


def test_lists_the_days_screenings_sorted_by_start_time(
    client, add_film, add_screening, at
):  # UC1-M, UC1-BR1.2
    night_train = add_film("Nocny Pociąg")
    little_trip = add_film("Mała Wielka Podróż")
    # dodane w innej kolejności niż godziny, żeby sortowanie nie wyszło "przypadkiem"
    evening = add_screening(night_train, start_time=at("2026-11-23", 18))
    morning = add_screening(little_trip, start_time=at("2026-11-23", 10), room_id=2)
    afternoon = add_screening(night_train, start_time=at("2026-11-23", 14))

    res = client.get("/screenings", params={"date": "2026-11-23"})

    assert res.status_code == 200
    assert [item["screening_id"] for item in res.json()] == [morning, afternoon, evening]


def test_screening_item_has_the_agreed_fields(client, add_film, add_screening, at):  # UC1-M
    film_id = add_film("Nocny Pociąg", duration_min=98)
    screening_id = add_screening(
        film_id, start_time=at("2026-11-23", 18), room_id=1, price_grosze=2599
    )

    res = client.get("/screenings", params={"date": "2026-11-23"})

    [item] = res.json()
    # czas jako ISO 8601 z oznaczeniem UTC (np. "2026-11-23T18:00:00Z"), nie liczba
    start_time = datetime.fromisoformat(item.pop("start_time"))
    assert start_time == datetime(2026, 11, 23, 18, 0, tzinfo=UTC)
    assert item == {
        "screening_id": screening_id,
        "film_id": film_id,
        "film_title": "Nocny Pociąg",
        "duration_min": 98,
        "age_rating": 12,
        "room_id": 1,
        "room_name": "Sala 1",
        "base_price_grosze": 2599,
    }


def test_screening_that_has_already_started_is_not_returned(
    client, clock, add_film, add_screening, at
):  # UC1-BR1.1
    film_id = add_film("Nocny Pociąg")
    add_screening(film_id, start_time=at("2026-11-22", 18))
    upcoming = add_screening(film_id, start_time=at("2026-11-22", 21), room_id=2)
    clock.advance(7 * 3600)  # jest 19:00 UTC: seans z 18:00 już trwa, ten z 21:00 jeszcze nie

    res = client.get("/screenings", params={"date": "2026-11-22"})

    assert [item["screening_id"] for item in res.json()] == [upcoming]


def test_day_without_screenings_returns_empty_list(client, add_film, add_screening, at):  # UC1-A1
    film_id = add_film("Nocny Pociąg")
    add_screening(film_id, start_time=at("2026-11-24", 18))  # seans, ale innego dnia

    res = client.get("/screenings", params={"date": "2026-11-23"})

    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.parametrize(
    "filters",
    [
        {"title": "Nieistniejący tytuł"},
        {"genre": "Horror"},
        {"title": "Nocny", "genre": "Komedia"},
    ],
)
def test_filter_without_results_returns_empty_list(
    client, add_film, add_screening, at, filters
):  # UC1-A2
    film_id = add_film("Nocny Pociąg", genres=["Thriller", "Dramat"])
    add_screening(film_id, start_time=at("2026-11-23", 18))  # seans tego dnia, ale nie pasuje

    res = client.get("/screenings", params={"date": "2026-11-23", **filters})

    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.parametrize("bad_date", ["2026-13-45", "23-11-2026", "jutro", ""])
def test_invalid_date_format_is_rejected(client, bad_date):  # UC1-A3
    res = client.get("/screenings", params={"date": bad_date})

    assert res.status_code == 422  # walidację robi FastAPI
    assert res.json()["detail"][0]["loc"] == ["query", "date"]
