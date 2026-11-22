"""UC1: przeglądanie repertuaru, GET /screenings?date=YYYY-MM-DD[&title=...][&genre=...]."""

import pytest


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