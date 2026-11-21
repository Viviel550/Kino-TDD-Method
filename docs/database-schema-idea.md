# Schemat bazy danych (SQLite)

Początkowy schemat dla Use Case'ów UC1–UC10 z [use-cases.md](use-cases.md).

## Przegląd tabel

| Tabela | Co przechowuje |
|---|---|
| `movies` | filmy |
| `genres` | gatunki |
| `movie_genres` | powiązanie filmów z gatunkami (wiele-do-wielu) |
| `halls` | sale kinowe | 
| `seats` | miejsca w salach |
| `screenings` | seanse (film + sala + godzina) | 
| `reservations` | rezerwacje klientów | 
| `reservation_seats` | miejsca zajęte przez rezerwację |
| `admins` | konta administratorów |

Sesji administratora nie trzymamy w bazie. Wystarczy podpisane ciasteczko sesyjne.

## Opis tabel

Skróty: **PK** klucz główny, **FK** klucz obcy, **UNIQUE** wartość unikalna, **NOT NULL** pole wymagane.

### `movies`: filmy

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `id` | INTEGER | PK | identyfikator |
| `title` | TEXT | NOT NULL, niepusty | tytuł |
| `description` | TEXT | | opis fabuły |
| `duration_min` | INTEGER | NOT NULL, > 0 | czas trwania w minutach |
| `age_rating` | TEXT | | ograniczenie wiekowe (np. `b.o.`, `7`, `12`, `16`, `18`) |
| `poster_url` | TEXT | | adres plakatu |
| `release_date` | TEXT | | data premiery, format `YYYY-MM-DD` |

### `genres`: gatunki

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `id` | INTEGER | PK | identyfikator |
| `name` | TEXT | NOT NULL, UNIQUE | nazwa gatunku (np. `Dramat`) |

### `movie_genres`: filmy i gatunki

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `movie_id` | INTEGER | PK (część), FK → `movies.id`, usuwanie kaskadowe | film |
| `genre_id` | INTEGER | PK (część), FK → `genres.id`, usuwanie zablokowane | gatunek |

Klucz główny jest złożony: `(movie_id, genre_id)`, więc ten sam gatunek nie powtórzy się przy filmie.

### `halls`: sale

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `id` | INTEGER | PK | identyfikator |
| `name` | TEXT | NOT NULL, UNIQUE | nazwa sali (np. `Sala 1`) |

### `seats`: miejsca

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `id` | INTEGER | PK | identyfikator |
| `hall_id` | INTEGER | NOT NULL, FK → `halls.id`, usuwanie kaskadowe | sala |
| `row_label` | TEXT | NOT NULL | oznaczenie rzędu (`A`, `B`, ...) |
| `seat_number` | INTEGER | NOT NULL, > 0 | numer miejsca w rzędzie |

Ograniczenie: **UNIQUE `(hall_id, row_label, seat_number)`**, czyli w jednej sali nie ma dwóch miejsc `A1`.

### `screenings`: seanse

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `id` | INTEGER | PK | identyfikator |
| `movie_id` | INTEGER | NOT NULL, FK → `movies.id`, usuwanie zablokowane | film |
| `hall_id` | INTEGER | NOT NULL, FK → `halls.id`, usuwanie zablokowane | sala |
| `starts_at` | TEXT | NOT NULL | początek seansu, ISO 8601 w UTC (np. `2026-12-01T17:00:00Z`) |
| `base_price_grosz` | INTEGER | NOT NULL, > 0 | cena bazowa w groszach |

Indeksy: `(hall_id, starts_at)` do szukania kolizji w sali, `(starts_at)` do repertuaru, `(movie_id)` do seansów filmu.

### `reservations`: rezerwacje

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `id` | INTEGER | PK | identyfikator |
| `screening_id` | INTEGER | NOT NULL, FK → `screenings.id`, usuwanie zablokowane | seans |
| `code` | TEXT | NOT NULL, UNIQUE | kod rezerwacji podawany klientowi |
| `customer_name` | TEXT | NOT NULL, niepusty | imię klienta |
| `customer_email` | TEXT | NOT NULL | e-mail klienta (format sprawdza aplikacja) |
| `status` | TEXT | NOT NULL, `active` lub `cancelled`, domyślnie `active` | status rezerwacji |
| `created_at` | TEXT | NOT NULL | moment utworzenia, UTC |
| `cancelled_at` | TEXT | | moment anulowania, UTC (puste, gdy aktywna) |

Dodatkowe ograniczenie **UNIQUE `(id, screening_id)`** jest potrzebne tylko dla klucza złożonego w `reservation_seats`. Indeks: `(screening_id)`.

### `reservation_seats`: miejsca w rezerwacji

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `reservation_id` | INTEGER | PK (część), FK (złożony) → `reservations`, usuwanie kaskadowe | rezerwacja |
| `seat_id` | INTEGER | PK (część), FK → `seats.id`, usuwanie zablokowane | miejsce |
| `screening_id` | INTEGER | NOT NULL, FK (złożony) → `reservations` | seans (kopia z rezerwacji) |

Ograniczenia:

- **UNIQUE `(screening_id, seat_id)`**: to samo miejsce można zarezerwować tylko raz na dany seans.
- **FK `(reservation_id, screening_id)` → `reservations(id, screening_id)`**: seans zapisany przy miejscu musi być tym samym seansem co w rezerwacji, więc nie da się obejść unikalności niespójnym wpisem.

### `admins`: administratorzy

| Kolumna | Typ | Ograniczenia | Opis |
|---|---|---|---|
| `id` | INTEGER | PK | identyfikator |
| `login` | TEXT | NOT NULL, UNIQUE | login |
| `password_hash` | TEXT | NOT NULL | hash hasła (argon2), nigdy hasło jawne |
| `created_at` | TEXT | NOT NULL | moment utworzenia, UTC |

## Relacje

| Relacja | Rodzaj | Znaczenie |
|---|---|---|
| `movies` → `screenings` | 1 : wiele | film ma wiele seansów |
| `halls` → `screenings` | 1 : wiele | w sali odbywa się wiele seansów |
| `halls` → `seats` | 1 : wiele | sala ma wiele miejsc |
| `movies` ↔ `genres` | wiele : wiele | przez `movie_genres` |
| `screenings` → `reservations` | 1 : wiele | seans ma wiele rezerwacji |
| `reservations` → `reservation_seats` | 1 : wiele (min. 1) | rezerwacja obejmuje od 1 do 6 miejsc |
| `seats` → `reservation_seats` | 1 : wiele | miejsce bywa rezerwowane na różne seanse |

## Które reguły pilnuje baza, a które aplikacja

| Reguła | Kto pilnuje | Jak |
|---|---|---|
| Miejsce tylko raz na seans (BR4.3, UC4-A6) | **baza** | `UNIQUE (screening_id, seat_id)`, aplikacja zamienia `IntegrityError` na 409 |
| Unikalny kod rezerwacji (BR4.5) | **baza** | `UNIQUE (code)` |
| Czas trwania filmu i cena dodatnie (BR8.1, BR9.3) | **baza** | `CHECK (... > 0)` |
| Brak usunięcia filmu lub seansu z zależnościami (BR8.2) | **baza** i aplikacja | `ON DELETE` zablokowane, a aplikacja zwraca czytelny 409 |
| Zapis rezerwacji w całości albo wcale (BR4.6) | **aplikacja** | jedna transakcja |
| Miejsce należy do sali seansu (BR4.2) | **aplikacja** | sprawdzenie w serwisie |
| 1–6 miejsc w rezerwacji (BR4.1) | **aplikacja** | walidacja |
| Poprawny e-mail (BR4.4) | **aplikacja** | walidacja Pydantic (`EmailStr`) |
| Seans w przyszłości (BR9.2, UC4-A4) | **aplikacja** | porównanie z zegarem (`Clock`) |
| Brak nakładania się seansów w sali (BR9.1) | **aplikacja** | zapytanie po `(hall_id, starts_at)` i czasie trwania filmu |
| Anulowanie najpóźniej 30 min przed seansem (BR6.1) | **aplikacja** | porównanie z zegarem |

## Decyzje projektowe

| Decyzja | Powód |
|---|---|
| Cena w groszach (liczba całkowita) | brak błędów zaokrągleń |
| Daty jako tekst ISO 8601 w UTC | SQLite nie ma typu daty, a taki zapis da się sortować i porównywać |
| Anulowanie: usuwamy wiersze z `reservation_seats`, a w `reservations` zmieniamy status na `cancelled` | miejsca wracają do puli (BR6.2), a historia rezerwacji zostaje |
| Brak tabeli klientów | rezerwacja na imię i e-mail, zgodnie z zakresem projektu |
| Klucze obce zablokowane (`RESTRICT`) przy filmach, salach i seansach | baza nie pozwoli usunąć danych, od których zależą inne |

## Ustawienia SQLite

- Dla **każdego połączenia** włącz `PRAGMA foreign_keys = ON`, bo domyślnie klucze obce są wyłączone.
- Opcjonalnie `PRAGMA journal_mode = WAL` i `PRAGMA busy_timeout = 5000` (mniej blokad przy równoległych żądaniach).
- Tabele można tworzyć w trybie `STRICT` (SQLite 3.37+), wtedy baza pilnuje typów kolumn.



