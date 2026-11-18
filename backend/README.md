# Backend: Kino API (FastAPI)

REST API strony kina: repertuar, seanse, rezerwacje miejsc i panel administratora. Projekt rozwijamy metodą **TDD** (test najpierw, potem kod). Scenariusze i reguły biznesowe są w [`../docs/use-cases.md`](../docs/use-cases.md).

> **Stan na dziś:** szkielet projektu. Działa endpoint `GET /health` z testem. Warstwy `routes`, `services`, `repositories`, `models`, `schemas`, `db`, `core` są puste (tylko `__init__.py`) i będą uzupełniane przy kolejnych Use Case'ach.

## Technologie

| Obszar | Wybór |
|---|---|
| Język | Python 3.14 (wersja przypięta w `.python-version`) |
| Framework | FastAPI |
| Baza danych | SQLite (plik, bez serwera i bez Dockera) |
| ORM i migracje | SQLAlchemy + Alembic |
| Testy | pytest |
| Zarządzanie pakietami | uv |

## Wymagania

- [**uv**](https://docs.astral.sh/uv/getting-started/installation/). To jedyne narzędzie, które trzeba zainstalować samemu. `uv` sam pobierze właściwą wersję Pythona (3.14) i utworzy środowisko wirtualne `.venv/`.
- Git.

Nie instalujemy pakietów globalnie i nie aktywujemy `.venv` ręcznie. Wszystko uruchamiamy przez `uv run ...`.

## Szybki start

```bash
cd backend
uv sync                                   # tworzy .venv i instaluje zależności z uv.lock
uv run uvicorn app.main:app --reload      # serwer na http://localhost:8000
```

Po uruchomieniu:

| Adres | Co to jest |
|---|---|
| http://localhost:8000/health | sprawdzenie, czy API działa |
| http://localhost:8000/docs | interaktywna dokumentacja (Swagger UI), można klikać „Try it out" |
| http://localhost:8000/openapi.json | kontrakt API w formacie OpenAPI |

## Testy

Wszystkie komendy wykonujemy z katalogu `backend/`.

| Komenda | Co robi |
|---|---|
| `uv run pytest` | uruchamia wszystkie testy z `tests/` |
| `uv run pytest -v` | wypisuje nazwę każdego testu |
| `uv run pytest tests/api` | tylko testy z jednego katalogu |
| `uv run pytest tests/api/test_health.py` | tylko jeden plik |
| `uv run pytest -k "taken_seat"` | tylko testy, w których nazwie jest fraza |
| `uv run pytest -x` | zatrzymuje się na pierwszym błędzie |
| `uv run pytest --lf` | powtarza tylko testy, które ostatnio padły |
| `uv run pytest --cov=app` | pokazuje pokrycie kodu testami |
| `uv run pytest --cov=app --cov-report=term-missing` | pokrycie z numerami linii bez testów |
| `uv run pytest --cov=app --cov-report=html` | raport w `htmlcov/index.html` |

### Rodzaje testów i gdzie je pisać

| Katalog | Rodzaj | Co sprawdza | Baza danych |
|---|---|---|---|
| `tests/unit/` | jednostkowe | logikę w `services/` (reguły z UC) | brak, atrapy (`fakes.py`) |
| `tests/integration/` | integracyjne | `repositories/` na prawdziwym SQLite, np. `UNIQUE(screening_id, seat_id)` | plik tymczasowy na test |
| `tests/api/` | API | endpointy przez `TestClient`: kody statusu, format JSON | atrapa lub SQLite |

W katalogu `tests/` są na razie tylko `api/test_health.py` i pusty `unit/`. Katalog `integration/`, `conftest.py` i `fakes.py` utworzymy przy pierwszym Use Case'ie.

### Zasady pisania testów

1. **Test przed kodem.** Napisz test, uruchom go i zobacz, że **pada** (Red). Dopiero potem pisz minimum kodu, żeby przeszedł (Green), a na końcu refaktoryzuj.
2. **Jeden scenariusz = jeden test.** Każdy scenariusz i każda reguła z `use-cases.md` ma mieć test.
3. **Oznaczaj testy identyfikatorem UC**, np. `# UC4-A1` w komentarzu lub w nazwie. Dzięki temu łatwo uzupełnić macierz śledzenia.
4. **Nazwy opisują zachowanie**: `test_taken_seat_returns_409`, a nie `test1`.
5. **Unikalne nazwy plików testowych.** Nie twórz `unit/test_reservation.py` i `api/test_reservation.py`, bo pytest zgłosi konflikt. Używaj `test_reservation_service.py` i `test_reservations_api.py`.
6. **Czas wstrzykuj jako zależność** (`Clock`), zamiast wołać `datetime.now()` w serwisach. Bez tego testy zależą od daty uruchomienia (UC4-A4, UC6-A3).
7. **Testy muszą być niezależne.** Żaden test nie zakłada, że poprzedni się wykonał. Każdy dostaje świeżą bazę.

### Przykład cyklu Red → Green

```python
# tests/api/test_reservations_api.py
def test_taken_seat_returns_409(client, repo):  # UC4-A1
    repo.add_taken_seat(screening_id=1, seat_id=1)
    res = client.post(
        "/reservations",
        json={
            "screeningId": 1,
            "seatIds": [1],
            "name": "Jan Kowalski",
            "email": "jan@example.com",
        },
    )
    assert res.status_code == 409
```

## Jakość kodu

| Komenda | Co robi |
|---|---|
| `uv run ruff check .` | linter: nieużywane importy, typowe błędy |
| `uv run ruff check . --fix` | naprawia automatycznie to, co się da |
| `uv run ruff format .` | formatuje kod |
| `uv run ruff format --check .` | sprawdza format bez zmian (używa tego CI) |
| `uv run mypy app` | sprawdza typy |

Przed każdym pushem uruchom: `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest`.

### Konfiguracja w `pyproject.toml`

| Sekcja | Ustawienie | Znaczenie |
|---|---|---|
| `[tool.pytest.ini_options]` | `testpaths = ["tests"]` | pytest szuka testów tylko w `tests/` |
| `[tool.ruff]` | `line-length = 100` | maksymalna długość linii |
| `[tool.mypy]` | `strict = true` | najostrzejsze sprawdzanie typów, wymaga adnotacji we wszystkich funkcjach |
| `[tool.mypy]` | `plugins = ["pydantic.mypy"]` | mypy rozumie modele Pydantic |

## Struktura

Poniżej układ docelowy. Elementy oznaczone `(brak)` jeszcze nie istnieją.

```
backend/
├── app/
│   ├── main.py            # create_app(), endpoint /health
│   ├── config.py          # (brak) ustawienia ze zmiennych środowiskowych
│   ├── deps.py            # (brak) Depends: sesja, serwisy, zegar, require_admin
│   ├── errors.py          # (brak) wyjątki domenowe → kody HTTP
│   ├── routes/            # warstwa HTTP: parsowanie, kody statusu
│   ├── services/          # logika biznesowa (reguły z UC)
│   ├── repositories/      # dostęp do bazy
│   ├── models/            # tabele SQLAlchemy
│   ├── schemas/           # modele Pydantic (żądania, odpowiedzi)
│   ├── db/                # sesja, seed
│   └── core/              # zegar (Clock), hasła, sesje
├── migrations/            # (brak) Alembic
├── scripts/               # (brak) np. export_openapi.py
└── tests/
    ├── api/
    ├── unit/
    ├── integration/       # (brak)
    ├── conftest.py        # (brak)
    └── fakes.py           # (brak)
```

**Zasada warstw** (zależności idą tylko w dół):

| Warstwa | Robi | Nie robi |
|---|---|---|
| `routes` | przyjmuje żądanie, woła serwis, zwraca odpowiedź | nie zawiera reguł biznesowych ani SQL |
| `services` | wszystkie reguły z UC | nie zna FastAPI ani szczegółów bazy |
| `repositories` | zapytania i zapisy do bazy | nie podejmuje decyzji biznesowych |
| `models` | struktura tabel i ograniczenia | bez logiki |

Reguła biznesowa zawsze trafia do `services`. To ułatwia testowanie bez bazy i bez HTTP.

## Pakiety

Definicje są w `pyproject.toml`, a dokładne wersje w `uv.lock`.

### Uruchomieniowe

| Pakiet | Do czego służy |
|---|---|
| `fastapi` | framework API, automatycznie generuje dokumentację OpenAPI |
| `uvicorn[standard]` | serwer, który uruchamia aplikację FastAPI (wersja `standard` dodaje m.in. auto-przeładowanie) |
| `sqlalchemy` | ORM: praca z bazą przez obiekty Pythona |
| `alembic` | migracje: wersjonowanie zmian schematu bazy |
| `pydantic[email]` | walidacja danych wejściowych i schematy; dodatek `email` daje typ `EmailStr` |
| `pydantic-settings` | wczytywanie konfiguracji ze zmiennych środowiskowych i pliku `.env` |
| `argon2-cffi` | bezpieczne hashowanie haseł administratora (UC7) |
| `itsdangerous` | podpisywanie ciasteczek sesyjnych (panel admina) |

### Deweloperskie

| Pakiet | Do czego służy |
|---|---|
| `pytest` | uruchamianie testów |
| `pytest-cov` | raport pokrycia kodu testami |
| `httpx` | klient HTTP, wymagany przez `TestClient` z FastAPI (sami go nie wołamy) |
| `ruff` | linter i formatter |
| `mypy` | sprawdzanie typów bez uruchamiania kodu |

### Zarządzanie pakietami

| Zadanie | Komenda |
|---|---|
| zainstalować wszystko (np. po `git pull`) | `uv sync` |
| dodać pakiet do aplikacji | `uv add nazwa-pakietu` |
| dodać pakiet deweloperski | `uv add --dev nazwa-pakietu` |
| usunąć pakiet | `uv remove nazwa-pakietu` |
| zaktualizować lockfile | `uv lock` |
| uruchomić dowolne polecenie w środowisku projektu | `uv run <polecenie>` |

Po każdej zmianie zależności **commitujemy razem `pyproject.toml` i `uv.lock`**.

## Zmienne środowiskowe

Planowane (kod ich jeszcze nie czyta). Wzór w pliku `.env.example`, którego jeszcze nie ma:

```
DATABASE_URL=sqlite:///./cinema.db
```

Prawdziwy `.env` nigdy nie trafia do gita.

## Znane problemy i braki

- **`uv run backend` nie działa.** W `pyproject.toml` jest skrypt `backend = "app.main:main"`, ale w `app/main.py` funkcja `main()` używa `uvicorn` bez importu (`import uvicorn`), więc kończy się `NameError`. Poprawka: dodać `import uvicorn` na górze pliku. Do tego czasu uruchamiamy `uv run uvicorn app.main:app --reload`.
- **`mypy` z `strict = true` zgłosi błędy w `main.py`**, bo funkcje nie mają adnotacji typów (`def main() -> None`, `def health() -> dict[str, str]`).
- Brak `.github/workflows/ci.yml`, więc testy nie uruchamiają się jeszcze automatycznie po pushu.
- Brak `migrations/` (Alembic) i `scripts/export_openapi.py`.

## Rady dla osób pracujących nad backendem

**Praca z gitem**
- Pracuj na gałęzi, nie na `main`, np. `feature/uc4-reservation`. Numer UC w nazwie ułatwia śledzenie.
- Commituj małymi krokami. W TDD dobrze wygląda para: `test(uc4): taken seat returns 409` i `feat(uc4): reserve seats`.
- Przed pushem uruchom pełny zestaw: ruff, mypy, pytest.
- Nie commituj: `.venv/`, `*.db`, `*.db-wal`, `*.db-shm`, `.env`, `htmlcov/`, `.coverage`. Wpisy `*.db` już są w `.gitignore`, ale `-wal`, `-shm` i raporty pokrycia warto dopisać.

**Praca z kodem**
- Zaczynaj od testu. Jeśli nie wiesz, jak napisać test, scenariusz w `use-cases.md` jest niedoprecyzowany. Wróć do niego i uzgodnij go w zespole.
- Nie zmieniaj testu tylko po to, żeby przeszedł. Test opisuje wymaganie, więc najpierw ustal, czy zmienia się wymaganie.
- Trzymaj route'y cienkie. Gdy w route pojawia się `if` z regułą biznesową, przenieś go do serwisu.
- Zapytania do bazy pisz przez SQLAlchemy z parametrami (nigdy sklejanie SQL z danych użytkownika).
- Miejsca w rezerwacji chroni ograniczenie `UNIQUE(screening_id, seat_id)` w bazie. Nie zastępuj go samym sprawdzeniem w kodzie, bo dwa równoległe żądania je ominą. Przechwytuj `IntegrityError` i zamieniaj na 409.
- Przy SQLite włącz dla każdego połączenia `PRAGMA foreign_keys=ON`, bo domyślnie klucze obce są wyłączone.
- Daty trzymaj w UTC.
- Błędy walidacji FastAPI domyślnie zwraca jako **422**, a w `use-cases.md` zapisano **400**.

**Gdy coś nie działa**
- `ModuleNotFoundError`: uruchom `uv sync` albo użyj `uv run` zamiast zwykłego `python` lub `pytest`.
- Testy lokalnie przechodzą, w CI nie: sprawdź, czy `uv.lock` jest zacommitowany i aktualny (`uv lock`).
- `database is locked` (SQLite): zamknij podgląd bazy (np. DB Browser) lub ustaw `PRAGMA busy_timeout`.
