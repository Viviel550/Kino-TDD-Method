# Kino-TDD-Method
front i backend

## Technologie 
 - Frontend: Astro+Preact
 - Testy Frontend: Vitest, MSW
 - Backend : FastAPI
 - Testy Backend: pytest
 - Baza danych: SQLite
 
## Wymagania:
 - Brak
## Kolejność realizacji (TDD)
By spełnić tą kolejność potrzebujemy wybrac technologie 
1. Wybrać jeden UC z ```docs/use-cases.md``` i uzgodnić go w zespole.
2. Zamienić scenariusze na listę testów (Przykłady dla każdego usecase są już w use-cases.md).
3. Napisać pierwszy test i zobaczyć, że pada (Red).
4. Napisać minimum kodu, żeby przeszedł (Green).
5. Refaktoryzacja i kolejny scenariusz.
6. Po testach jednostkowych dopisać integracyjne i API, na końcu E2E (Testy całej aplikacji) dla przebiegu głównego.
