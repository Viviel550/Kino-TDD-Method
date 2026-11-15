# Use Case'y: strona kina
Szczegóły do omówienia grupowo.
## 1. Aktorzy

| Aktor | Opis |
|---|---|
| Gość | Niezalogowany użytkownik strony, może przeglądać repertuar i rezerwować miejsca |
| Administrator | Zalogowany pracownik kina, zarządza filmami, seansami i rezerwacjami |

## 2. Podział na moduły i priorytety

| Moduł | Use Case'y | Priorytet (MoSCoW) |
|---|---|---|
| Katalog | UC1, UC2 | Must |
| Rezerwacje | UC3, UC4 (Must), UC5, UC6 (Should) | Must / Should |
| Administracja | UC7, UC9 (Must), UC8, UC10 (Should) | Must / Should |

Propozycja iteracji: sprint 1 to Katalog, sprint 2 to Rezerwacje, sprint 3 to Administracja.

**Could (rozszerzenia):** konto klienta i historia rezerwacji, typy biletów (normalny/ulgowy), wygasanie nieodebranych rezerwacji (np. po 15 min), e-mail z potwierdzeniem, wyszukiwarka, oceny filmów, zarządzanie salami.

## 3. Konwencje

- Identyfikator testu ma postać `UCx-Ay` (np. `UC4-A1`), gdzie `A` oznacza przebieg alternatywny, a `M` przebieg główny.
- Każdy scenariusz i każda reguła biznesowa ma co najmniej jeden test.
- Poziomy testów: **J** (jednostkowy), **I** (integracyjny, prawdziwa baza), **API** (HTTP), **E2E** (Playwright).

---

## 4. Use Case'y: Gość

### UC1: Przeglądanie repertuaru

- **Aktor:** Gość
- **Warunki wstępne:** brak
- **Reguły biznesowe:**
  - BR1.1: wyświetlane są tylko seanse, które jeszcze się nie rozpoczęły
  - BR1.2: seanse są posortowane rosnąco po godzinie rozpoczęcia
- **Przebieg główny:** Gość otwiera stronę główną → system pokazuje filmy z seansami na wybrany dzień (domyślnie dzisiaj) → Gość zmienia datę lub filtr (gatunek, tytuł) → system odświeża listę.
- **Przebiegi alternatywne:**
  - A1: brak seansów w wybranym dniu → komunikat „Brak seansów”
  - A2: filtr nie zwraca wyników → komunikat „Nic nie znaleziono”
  - A3: niepoprawny format daty w parametrze → 400
- **Endpoint:** `GET /movies`, `GET /screenings?date=`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC1-M` | lista seansów na dzień | J, API | 200, lista posortowana po czasie |
| `UC1-A1` | dzień bez seansów | API | 200, pusta lista |
| `UC1-A2` | filtr bez wyników | API | 200, pusta lista |
| `UC1-A3` | zły format daty | API | 400 |
| `UC1-BR1.1` | seans z przeszłości nie jest zwracany | J | brak seansu na liście |

### UC2: Podgląd szczegółów filmu

- **Aktor:** Gość
- **Warunki wstępne:** film istnieje
- **Przebieg główny:** Gość wybiera film → system pokazuje opis, czas trwania, ograniczenie wiekowe, gatunki, zwiastun i listę nadchodzących seansów.
- **Przebiegi alternatywne:**
  - A1: film nie istnieje → 404
  - A2: film bez nadchodzących seansów → szczegóły i komunikat „Brak zaplanowanych seansów”
- **Endpoint:** `GET /movies/{id}`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC2-M` | szczegóły istniejącego filmu | API, E2E | 200, komplet pól |
| `UC2-A1` | nieistniejące id | API | 404 |
| `UC2-A2` | film bez seansów | API | 200, pusta lista seansów |

### UC3: Podgląd seansu i mapy sali

- **Aktor:** Gość
- **Warunki wstępne:** seans istnieje
- **Reguły biznesowe:**
  - BR3.1: mapa zawiera wszystkie miejsca sali przypisanej do seansu
  - BR3.2: miejsce jest oznaczone jako zajęte, jeśli należy do aktywnej rezerwacji na ten seans
- **Przebieg główny:** Gość wybiera seans → system zwraca układ sali ze statusem każdego miejsca (wolne/zajęte).
- **Przebiegi alternatywne:**
  - A1: seans nie istnieje → 404
  - A2: seans już się odbył → mapa w trybie tylko do odczytu (rezerwacja wyłączona)
- **Endpoint:** `GET /screenings/{id}/seats`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC3-M` | mapa wolnej sali | API | 200, wszystkie miejsca wolne |
| `UC3-BR3.2` | część miejsc zarezerwowana | I, API | zajęte miejsca mają status `taken` |
| `UC3-A1` | nieistniejący seans | API | 404 |
| `UC3-A2` | seans w przeszłości | J | flaga `bookable = false` |

### UC4: Rezerwacja miejsc

- **Aktor:** Gość
- **Warunki wstępne:** seans istnieje i jest w przyszłości
- **Reguły biznesowe:**
  - BR4.1: w jednej rezerwacji od 1 do 6 miejsc
  - BR4.2: miejsca muszą należeć do sali przypisanej do seansu
  - BR4.3: to samo miejsce może być zarezerwowane tylko raz na seans (gwarantuje to `UNIQUE(screening_id, seat_id)` w bazie)
  - BR4.4: imię jest niepuste, a e-mail ma poprawny format
  - BR4.5: kod rezerwacji jest unikalny i trudny do odgadnięcia
  - BR4.6: rezerwacja jest zapisywana w jednej transakcji (wszystkie miejsca albo żadne)
- **Przebieg główny:** Gość wybiera miejsca na mapie → podaje imię i e-mail → system waliduje dane i zapisuje rezerwację → zwraca kod rezerwacji (płatność w kasie).
- **Przebiegi alternatywne:**
  - A1: miejsce już zajęte → 409
  - A2: niepoprawne dane klienta → 400
  - A3: zero miejsc lub więcej niż 6 → 400
  - A4: seans już się odbył → 422
  - A5: miejsce z innej sali → 422
  - A6: dwa równoległe żądania na to samo miejsce → jedno 201, drugie 409
- **Endpoint:** `POST /reservations`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC4-M` | rezerwacja wolnych miejsc | J, API, E2E | 201, kod rezerwacji |
| `UC4-A1` | zajęte miejsce | J, API | 409 `SEAT_TAKEN` |
| `UC4-A2` | zły e-mail lub puste imię | J, API | 400 |
| `UC4-A3` | 0 lub 7 miejsc | J, API | 400 |
| `UC4-A4` | seans w przeszłości | J | 422 |
| `UC4-A5` | miejsce z innej sali | J | 422 |
| `UC4-A6` | równoległe rezerwacje | I | dokładnie jedno 201 i jedno 409 |
| `UC4-BR4.6` | błąd przy jednym z miejsc | I | żadne miejsce nie zostaje zapisane |
| `UC4-BR4.5` | unikalność kodów | J | brak kolizji w serii generowania |

### UC5: Sprawdzenie rezerwacji po kodzie

- **Aktor:** Gość
- **Warunki wstępne:** Gość zna kod rezerwacji
- **Przebieg główny:** Gość wpisuje kod → system pokazuje film, seans, miejsca i status rezerwacji.
- **Przebiegi alternatywne:**
  - A1: nieistniejący kod → 404
  - A2: rezerwacja anulowana → pokazana ze statusem „Anulowana”
- **Endpoint:** `GET /reservations/{code}`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC5-M` | istniejąca rezerwacja | API | 200, dane rezerwacji |
| `UC5-A1` | zły kod | API | 404 |
| `UC5-A2` | rezerwacja anulowana | API | 200, `status = cancelled` |

### UC6: Anulowanie rezerwacji po kodzie

- **Aktor:** Gość
- **Warunki wstępne:** rezerwacja istnieje i jest aktywna
- **Reguły biznesowe:**
  - BR6.1: anulować można najpóźniej 30 minut przed seansem
  - BR6.2: po anulowaniu miejsca wracają do puli wolnych
- **Przebieg główny:** Gość podaje kod i potwierdza anulowanie → system zmienia status i zwalnia miejsca.
- **Przebiegi alternatywne:**
  - A1: nieistniejący kod → 404
  - A2: rezerwacja już anulowana → 409
  - A3: mniej niż 30 minut do seansu → 422
- **Endpoint:** `DELETE /reservations/{code}`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC6-M` | anulowanie aktywnej rezerwacji | J, API | 204 |
| `UC6-BR6.2` | miejsca wracają do puli | I | miejsca znów wolne w UC3 |
| `UC6-A1` | zły kod | API | 404 |
| `UC6-A2` | podwójne anulowanie | J, API | 409 |
| `UC6-A3` | za późno na anulowanie | J | 422 |

---

## 5. Use Case'y: Administrator

### UC7: Logowanie do panelu

- **Aktor:** Administrator
- **Reguły biznesowe:**
  - BR7.1: hasła są przechowywane jako hash (argon2/bcrypt)
  - BR7.2: endpointy `/admin/*` wymagają ważnej sesji
- **Przebieg główny:** Administrator podaje login i hasło → system weryfikuje → tworzy sesję → przekierowanie do panelu.
- **Przebiegi alternatywne:**
  - A1: błędne hasło lub login → 401, ten sam komunikat dla obu przypadków
  - A2: dostęp do `/admin/*` bez sesji → 401
  - A3: wygasła sesja → 401
- **Endpoint:** `POST /admin/login`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC7-M` | poprawne logowanie | J, API, E2E | 200, ciasteczko sesji |
| `UC7-A1` | złe dane | API | 401 |
| `UC7-A2` | brak sesji | API | 401 |
| `UC7-BR7.1` | hash w bazie nie jest równy hasłu | J | hasło jawne nigdy nie jest zapisane |

### UC8: Zarządzanie filmami (możemy rozbić na Dodawanie/Usuwanie/Edycja filmów)

- **Aktor:** Administrator
- **Warunki wstępne:** Administrator jest zalogowany (UC7)
- **Reguły biznesowe:**
  - BR8.1: tytuł niepusty, czas trwania dodatni
  - BR8.2: nie można usunąć filmu, który ma przyszłe seanse z aktywnymi rezerwacjami
- **Przebieg główny:** Administrator dodaje, edytuje lub usuwa film → system waliduje i zapisuje zmianę.
- **Przebiegi alternatywne:**
  - A1: niepoprawne dane → 400
  - A2: edycja lub usunięcie nieistniejącego filmu → 404
  - A3: usunięcie filmu z aktywnymi rezerwacjami → 409
- **Endpointy:** `POST/PUT/DELETE /admin/movies`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC8-M` | dodanie filmu | J, API | 201 |
| `UC8-A1` | czas trwania ujemny | J, API | 400 |
| `UC8-A2` | nieistniejące id | API | 404 |
| `UC8-A3` | film z rezerwacjami | I | 409 |

### UC9: Zarządzanie seansami (Też możemy rozbić na dodawanie/usuwanie/edycje seansów)

- **Aktor:** Administrator
- **Warunki wstępne:** Administrator jest zalogowany, film i sala istnieją
- **Reguły biznesowe:**
  - BR9.1: seanse w tej samej sali nie mogą się nakładać (czas trwania filmu plus przerwa techniczna, np. 15 min)
  - BR9.2: seans nie może zaczynać się w przeszłości
  - BR9.3: cena bazowa jest dodatnia
- **Przebieg główny:** Administrator wybiera film, salę, datę, godzinę i cenę → system sprawdza kolizje → zapisuje seans.
- **Przebiegi alternatywne:**
  - A1: seans nakłada się na inny w tej sali → 409
  - A2: początek w przeszłości → 422
  - A3: nieistniejący film lub sala → 404
  - A4: cena niedodatnia → 400
- **Endpointy:** `POST/PUT/DELETE /admin/screenings`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC9-M` | dodanie seansu | J, API, E2E | 201 |
| `UC9-A1a` | pełne nałożenie | J | 409 |
| `UC9-A1b` | częściowe nałożenie (początek w trakcie innego) | J | 409 |
| `UC9-A1c` | seans zaczyna się dokładnie po przerwie technicznej | J | 201 |
| `UC9-A1d` | ta sama godzina w innej sali | J | 201 |
| `UC9-A2` | data w przeszłości | J | 422 |
| `UC9-A3` | nieistniejący film | API | 404 |

### UC10: Podgląd i anulowanie rezerwacji na seans

- **Aktor:** Administrator
- **Warunki wstępne:** Administrator jest zalogowany, seans istnieje
- **Przebieg główny:** Administrator otwiera seans → system pokazuje listę rezerwacji (imię, e-mail, miejsca, status) → Administrator może anulować wybraną rezerwację.
- **Przebiegi alternatywne:**
  - A1: seans bez rezerwacji → pusta lista
  - A2: anulowanie przez administratora nie podlega ograniczeniu BR6.1
- **Endpointy:** `GET /admin/screenings/{id}/reservations`, `DELETE /admin/reservations/{id}`

| Test | Scenariusz | Poziom | Oczekiwany wynik |
|---|---|---|---|
| `UC10-M` | lista rezerwacji seansu | API | 200 |
| `UC10-A1` | seans bez rezerwacji | API | 200, pusta lista |
| `UC10-A2` | anulowanie tuż przed seansem | J | 204 |

---

## 6. Macierz śledzenia (UC → testy)

**Do uzupełniania w trakcie projektu.**

| UC | Scenariusze i reguły | Testy jedn. | Testy integr. | Testy API | E2E | Status |
|---|---|---|---|---|---|---|
| UC1 | 5 | 1 | 0 | 4 | 0 | do zrobienia |
| UC2 | 3 | 0 | 0 | 3 | 1 | do zrobienia |
| UC3 | 4 | 1 | 1 | 3 | 0 | do zrobienia |
| UC4 | 9 | 6 | 2 | 4 | 1 | do zrobienia |
| UC5 | 3 | 0 | 0 | 3 | 0 | do zrobienia |
| UC6 | 5 | 3 | 1 | 3 | 0 | do zrobienia |
| UC7 | 4 | 2 | 0 | 3 | 1 | do zrobienia |
| UC8 | 4 | 1 | 1 | 3 | 0 | do zrobienia |
| UC9 | 7 | 6 | 0 | 2 | 1 | do zrobienia |
| UC10 | 3 | 1 | 0 | 2 | 0 | do zrobienia |

