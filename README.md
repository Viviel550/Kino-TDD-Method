# Kino-TDD-Method

Strona internetowa kina (frontend + backend) tworzona metodą **TDD (Test Driven Development)**. Gość przegląda repertuar, wybiera miejsca na mapie sali i rezerwuje je na imię i e-mail (płatność w kasie). Administrator zarządza filmami, seansami i rezerwacjami.

Projekt studencki, więc świadomie pomijamy bramkę płatniczą i rozbudowany system kont użytkowników.

## Spis treści

1. [Tech stack](#tech-stack)
2. [Wymagania](#wymagania)
3. [Szybki start](#szybki-start)
4. [Gdzie co znaleźć](#gdzie-co-znaleźć)
5. [Architektura](#architektura)
6. [Podejście TDD](#podejście-tdd)
7. [Testy](#testy)
8. [Praca w zespole](#praca-w-zespole)

## Tech stack

| Warstwa | Technologia | Uwagi |
|---|---|---|
| Frontend | **Astro 7** + TypeScript | renderowanie na serwerze (SSR, adapter Node) |
| Interaktywność | **Preact** | tylko tam, gdzie potrzeba („wyspy"), np. wybór miejsc |
| Backend | **FastAPI** (Python 3.14) | REST API, automatyczna dokumentacja OpenAPI |
| Baza danych | **SQLite** | plik, bez serwera i bez Dockera |
| ORM i migracje | SQLAlchemy + Alembic | |
| Testy backendu | **pytest** (+ pytest-cov, httpx) | jednostkowe, integracyjne, API |
| Testy frontendu | **Vitest** + Testing Library + **MSW** | jednostkowe, komponenty, mockowanie API |
| Testy E2E | **Playwright** | testy całej aplikacji w przeglądarce |
| Jakość kodu | ruff, mypy (backend), `astro check` (frontend) | linter, formatowanie, typy |
| Pakiety | **uv** (backend), **npm** (frontend) | lockfile'e w repozytorium |
| Kontrakt API | OpenAPI (`docs/openapi.json`) | generowany z backendu, z niego powstają typy frontendu |
| CI | GitHub Actions | planowane, jeszcze nie skonfigurowane |

## Wymagania

| Narzędzie | Wersja | Do czego |
|---|---|---|
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | aktualna | backend (sam pobierze Pythona 3.14 i utworzy `.venv`) |
| [Node.js](https://nodejs.org/) | 22.23.4 lub nowsza | frontend |
| Git | dowolna | kontrola wersji |

SQLite jest wbudowane w Pythona, więc nie trzeba niczego dodatkowo instalować.

## Szybki start

```bash
git clone <adres-repozytorium>
cd Kino-TDD-Method
```

**Backend** (http://localhost:8000):

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Sprawdzenie: http://localhost:8000/health, dokumentacja API: http://localhost:8000/docs

**Frontend** (http://localhost:4321), w drugim terminalu:

```bash
cd frontend
npm ci
npm run dev
```

Szczegóły, komendy testów i opis pakietów są w README każdej części: [backend/README.md](backend/README.md) i [frontend/README.md](frontend/README.md).

## Gdzie co znaleźć

```
Kino-TDD-Method/
├── README.md                  ← jesteś tutaj
├── docs/
│   └── use-cases.md           # Use Case'y UC1–UC10, reguły biznesowe i lista testów
├── backend/                   # FastAPI + SQLite
│   ├── README.md              # uruchamianie, testy, pakiety, rady
│   ├── pyproject.toml         # zależności i konfiguracja narzędzi
│   ├── uv.lock                # dokładne wersje pakietów
│   ├── app/                   # kod aplikacji
│   │   ├── routes/            #   warstwa HTTP
│   │   ├── services/          #   logika biznesowa (reguły z UC)
│   │   ├── repositories/      #   dostęp do bazy
│   │   ├── models/            #   tabele
│   │   ├── schemas/           #   modele Pydantic (wejście/wyjście API)
│   │   ├── db/                #   sesja, seed
│   │   └── core/              #   zegar, hasła, sesje
│   └── tests/
│       ├── unit/              #   testy logiki
│       ├── integration/       #   testy z prawdziwym SQLite
│       └── api/               #   testy endpointów
└── frontend/                  # Astro + Preact
    ├── README.md              # uruchamianie, testy, pakiety, rady
    ├── package.json           # zależności i skrypty
    ├── src/
    │   ├── pages/             #   strony i routing
    │   ├── layouts/           #   wspólny układ stron
    │   ├── components/        #   komponenty, w tym islands/ (interaktywne)
    │   └── lib/               #   klient API, logika, formatowanie
    └── tests/
        ├── unit/              #   testy Vitest
        ├── mocks/             #   serwer MSW (udawany backend)
        └── e2e/               #   testy Playwright
```

Niektóre z tych katalogów są jeszcze puste lub nie istnieją. Pełny wykaz tego, co jest, a czego brakuje, znajduje się w README backendu i frontendu w sekcjach „Znane braki".

| Szukasz… | Zajrzyj do |
|---|---|
| wymagań i scenariuszy | [docs/use-cases.md](docs/use-cases.md) |
| jak uruchomić backend i jego testy | [backend/README.md](backend/README.md) |
| jak uruchomić frontend i jego testy | [frontend/README.md](frontend/README.md) |
| listy pakietów i do czego służą | README backendu i frontendu, sekcje „Pakiety" |
| kontraktu API | `/docs` działającego backendu, docelowo `docs/openapi.json` |

## Architektura

```
Przeglądarka  →  Astro (SSR + wyspy Preact)  →  REST API (FastAPI)  →  SQLite
```

- **Frontend** renderuje strony na serwerze (repertuar, szczegóły filmu). Interaktywne są tylko wyspy, np. wybór miejsc w sali i formularz rezerwacji.
- **Backend** wystawia REST API i zawiera całą logikę biznesową. Jest podzielony na warstwy, a zależności idą tylko w dół: `routes` → `services` → `repositories` → `models`.
- **Reguła biznesowa** (np. limit 6 miejsc, seans musi być w przyszłości) trafia zawsze do `services`, nigdy do route'a ani repozytorium. Dzięki temu da się ją przetestować bez bazy i bez HTTP.
- **Baza** pilnuje spójności niezależnie od kodu: ograniczenie `UNIQUE(screening_id, seat_id)` uniemożliwia podwójną rezerwację tego samego miejsca.
- **Kontrakt API** jest jednym źródłem prawdy dla obu części. Backend generuje `openapi.json`, a z niego powstają typy TypeScript we frontendzie (`npm run gen:api`).

### Aktorzy i Use Case'y

| Aktor | Use Case'y |
|---|---|
| Gość | UC1 repertuar, UC2 szczegóły filmu, UC3 mapa sali, UC4 rezerwacja miejsc, UC5 podgląd rezerwacji po kodzie, UC6 anulowanie |
| Administrator | UC7 logowanie, UC8 zarządzanie filmami, UC9 zarządzanie seansami, UC10 rezerwacje na seans |

Pełne scenariusze, reguły biznesowe i oczekiwane wyniki testów są w [docs/use-cases.md](docs/use-cases.md).

## Podejście TDD

Najpierw opisujemy zachowanie **testem**, a dopiero potem piszemy kod. Pracujemy w cyklu:

1. **Red:** napisz test dla jednego scenariusza i uruchom go. Test musi **paść**, bo kodu jeszcze nie ma. Jeśli przechodzi, test nic nie sprawdza.
2. **Green:** napisz **minimum** kodu, żeby test przeszedł.
3. **Refactor:** popraw strukturę kodu, nie zmieniając zachowania. Testy pilnują, że nic się nie zepsuło.
4. Wróć do punktu 1 z następnym scenariuszem.

### Jak wybieramy, co testować

1. Wybierz jeden UC z [docs/use-cases.md](docs/use-cases.md) i uzgodnij go w zespole.
2. Każdy scenariusz (przebieg główny i alternatywne) oraz każda reguła biznesowa ma co najmniej jeden test. Tabele w dokumencie są gotową listą testów.
3. Zacznij od najniższej warstwy: testy jednostkowe logiki, potem integracyjne (baza), potem API, a na końcu E2E dla przebiegu głównego.

Zalecana kolejność Use Case'ów: UC1 → UC2 → UC3 → UC4 → UC7 → UC9 → UC5 → UC6 → UC8 → UC10.

### Zasady

- **Test jest wymaganiem.** Nie zmieniamy testu tylko po to, żeby przeszedł. Najpierw ustalamy, czy zmienia się wymaganie.
- **Oznaczamy testy identyfikatorem UC**, np. `UC4-A1` (UC4, przebieg alternatywny 1), w komentarzu lub w nazwie. Dzięki temu widać pokrycie wymagań.
- **Nazwy opisują zachowanie:** `test_taken_seat_returns_409`, a nie `test1`.
- **Testy są niezależne** i nie zakładają kolejności wykonania.
- **Czas jest zależnością.** Serwisy dostają zegar (`Clock`), zamiast wołać `datetime.now()`, żeby testy były powtarzalne.
- **Mały krok.** Jeden test, jeden fragment kodu, jeden commit.

## Testy

Piramida testów: dużo szybkich testów jednostkowych, mniej integracyjnych, kilka E2E.

| Poziom | Backend | Frontend |
|---|---|---|
| Jednostkowe | pytest + atrapy repozytoriów | Vitest (+ MSW dla serwisów API) |
| Komponenty | | Vitest + Testing Library |
| Integracyjne / API | pytest + SQLite + `TestClient` | MSW udaje backend |
| E2E | | Playwright (rezerwacja, logowanie admina, dodanie seansu) |
| Analiza statyczna | ruff, mypy | `astro check` (TypeScript) |

### Najczęstsze komendy

```bash
# backend (z katalogu backend/)
uv run pytest                       # wszystkie testy
uv run pytest --cov=app             # z pokryciem kodu
uv run ruff check . && uv run mypy app

# frontend (z katalogu frontend/)
npm test                            # wszystkie testy
npm run test:watch                  # tryb ciągły, wygodny w TDD
npm run typecheck                   # sprawdzenie typów
```

Pełne zestawy komend (pojedyncze pliki, filtry, pokrycie) są w README backendu i frontendu.

### Co oznacza „zielone"

Zanim wypchniesz kod, uruchom lokalnie:

| Część | Komenda |
|---|---|
| Backend | `uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest` |
| Frontend | `npm run typecheck && npm test && npm run build` |

## Praca w zespole

### Git

- `main` ma być zawsze zielona (testy przechodzą). Nie commitujemy na nią bezpośrednio.
- Pracujemy na gałęziach z numerem UC, np. `feature/uc4-reservation`, i scalamy przez pull request.
- Commity w małych krokach, najlepiej parą test + implementacja:
  - `test(uc4): taken seat returns 409`
  - `feat(uc4): reserve seats`
- Opis pull requesta: który UC, które scenariusze pokrywa, jak uruchomić testy.
- Przed scaleniem ktoś inny przegląda kod (code review).

### Czego nie commitujemy

`.venv/`, `node_modules/`, `dist/`, `.astro/`, `coverage/`, `htmlcov/`, `.env`, pliki baz (`*.db`, `*.db-wal`, `*.db-shm`), `__pycache__/`.

**Commitujemy za to** pliki blokujące wersje: `backend/uv.lock` i `frontend/package-lock.json`. Dzięki nim wszyscy mają te same wersje pakietów.

### Zależności

- Backend: `uv add pakiet` albo `uv add --dev pakiet`, potem commit `pyproject.toml` razem z `uv.lock`.
- Frontend: `npm install pakiet` albo `npm install -D pakiet`, potem commit `package.json` razem z `package-lock.json`.
- Do zwykłego instalowania po `git pull` używamy `uv sync` i `npm ci`.

### Wspólne ustalenia do podjęcia

| Temat | Do uzgodnienia |
|---|---|
| Kod błędu dla niepoprawnych danych | FastAPI domyślnie zwraca 422 |
| Format pól JSON | `camelCase` (`seatIds`) czy `snake_case`. Wpływa na kontrakt z frontendem. |
| Sposób przekazywania sesji admina | ciasteczko sesyjne, przy frontendzie i backendzie na różnych portach trzeba rozwiązać CORS i `SameSite` |
| Wartości reguł | limit miejsc (6), czas anulowania (30 min), przerwa między seansami (15 min) trzymać w jednym miejscu (`config.py`) |
