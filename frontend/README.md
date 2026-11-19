# Frontend: Kino (Astro)

Strona kina w Astro: repertuar, szczegóły filmu, mapa sali i rezerwacja miejsc oraz panel administratora. Dane pochodzą z [backendu](../backend/README.md) (REST API). Projekt rozwijamy metodą **TDD**, scenariusze są w [`../docs/use-cases.md`](../docs/use-cases.md).

> **Stan na dziś:** skonfigurowane środowisko (Astro SSR, Preact, Vitest, MSW) z przykładowymi testami. Strony i komponenty to jeszcze szablon Astro (`index.astro`, `Welcome.astro`) oraz przykładowa wyspa `Hello.tsx`.

## Technologie

| Obszar | Wybór |
|---|---|
| Framework | Astro 7, renderowanie na serwerze (`output: 'server'`, adapter Node `standalone`) |
| Styl | CSS Modules |
| Interaktywność | wyspy w Preact |
| Testy jednostkowe i komponentów | Vitest + Testing Library |
| Mockowanie API | MSW |
| Testy E2E | Playwright (jeszcze nieskonfigurowany) |
| Typy kontraktu API | `openapi-typescript` + `openapi-fetch` |
| Język | TypeScript (tryb `strict`) |

## Wymagania

- **Node.js 22.23.4 lub nowszy** (pole `engines` w `package.json`). Sprawdź: `node --version`.
- npm (instaluje się razem z Node).
- Uruchomiony backend na `http://localhost:8000`, gdy chcesz oglądać prawdziwe dane. Do testów jednostkowych backend nie jest potrzebny.

## Szybki start

```bash
cd frontend
npm ci              # instaluje dokładnie wersje z package-lock.json
npm run dev         # http://localhost:4321
```

## Komendy

Wszystkie wykonujemy z katalogu `frontend/`.

| Komenda | Co robi |
|---|---|
| `npm run dev` | serwer deweloperski na `localhost:4321` |
| `npm run build` | build produkcyjny do `dist/` |
| `npm run preview` | podgląd builda |
| `npm test` | jednorazowe uruchomienie testów Vitest |
| `npm run test:watch` | tryb watch: testy uruchamiają się po każdej zmianie pliku (wygodny w TDD) |
| `npm run test:e2e` | testy Playwright (patrz „Znane braki") |
| `npm run typecheck` | `astro check`: błędy typów w `.ts`, `.tsx` i `.astro` |
| `npm run gen:api` | generuje typy TypeScript z `../docs/openapi.json` do `src/lib/api/api-types.ts` |

## Testy

### Szybkie komendy

| Komenda | Co robi |
|---|---|
| `npm test` | wszystkie testy jednostkowe |
| `npm run test:watch` | testy w trybie ciągłym |
| `npx vitest run tests/unit/msw.test.ts` | tylko jeden plik |
| `npx vitest run -t "MSW przechwytuje"` | tylko testy o pasującej nazwie |
| `npx vitest run --coverage` | pokrycie kodu, raport w terminalu i w `coverage/index.html` |
| `npx vitest run --reporter=verbose` | nazwa każdego testu |

Folder `coverage/` jest generowany i ignorowany przez git (nie commitujemy go).

### Rodzaje testów

| Rodzaj | Narzędzie | Gdzie | Co sprawdza |
|---|---|---|---|
| Funkcje i serwisy API | Vitest + MSW | `tests/unit/` | logika w `src/lib/`, obsługa odpowiedzi backendu (201, 409, 400, 500) |
| Wyspy (Preact) | Vitest + Testing Library | `tests/unit/*.test.tsx` | zachowanie interfejsu: klikanie, blokady przycisków, limit 6 miejsc |
| Komponenty `.astro` | Vitest + Container API | `tests/unit/` | wyrenderowany HTML |
| Ścieżki użytkownika | Playwright | `tests/e2e/` | całość: przeglądarka → frontend → backend → baza |

Zasada piramidy: dużo testów jednostkowych, kilka E2E tylko dla przebiegów głównych (rezerwacja, logowanie admina, dodanie seansu).

### Co jest skonfigurowane

| Plik | Rola |
|---|---|
| `vitest.config.ts` | `environment: 'jsdom'` (atrapa przeglądarki), `setupFiles`, `include` tylko `tests/unit/**/*.test.{ts,tsx}`, pokrycie przez `v8` |
| `tests/setup.ts` | przed testami: ładuje dopasowania `jest-dom` (np. `toBeDisabled`) i uruchamia serwer MSW (`onUnhandledRequest: 'error'`) |
| `tests/mocks/server.ts` | pusty serwer MSW, handlery dodaje się w testach przez `server.use(...)` |
| `tests/unit/example.test.ts` | test kontrolny: czy Vitest, jsdom i `jest-dom` działają |
| `tests/unit/msw.test.ts` | test kontrolny MSW |
| `tests/unit/hello.test.tsx` | test kontrolny wyspy Preact (`src/components/islands/Hello.tsx`) |

Pliki `example`, `msw`, `hello` i komponent `Hello.tsx` to **próbki do usunięcia** po powstaniu prawdziwych testów.

### Jak działa MSW

MSW przechwytuje żądania HTTP wychodzące z kodu i odpowiada w imieniu backendu, więc testy działają bez serwera, bazy i sieci.

```ts
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

it('mapuje 409 na SEAT_TAKEN', async () => {            // UC4-A1
  server.use(
    http.post('http://localhost:8000/reservations', () =>
      HttpResponse.json({ error: 'SEAT_TAKEN' }, { status: 409 })),
  );
  // ... wywołaj funkcję z src/lib/services i sprawdź wynik
});
```

- `server.use(...)` dodaje handler tylko na czas jednego testu (po teście `resetHandlers` go czyści).
- `onUnhandledRequest: 'error'` powoduje, że test pada, gdy kod wysyła żądanie, którego nie zamockowano. To zabezpiecza przed testem, który przechodzi „przypadkiem".
- **Mock musi odpowiadać kontraktowi backendu** (`docs/openapi.json`), a nie być wymyślony z głowy. Inaczej testy są zielone, a aplikacja nie działa z prawdziwym API.
- MSW w Vitest działa tylko w procesie testu. Nie przechwyci żądań z serwera Astro uruchomionego osobno (np. w Playwright). Tam używa się `page.route` albo prawdziwego backendu.

### Przykład testu wyspy

```tsx
import { it, expect } from 'vitest';
import { render, screen } from '@testing-library/preact';
import { Hello } from '../../src/components/islands/Hello';

it('renderuje komponent', () => {
  render(<Hello name="Jan" />);
  expect(screen.getByText('Test wyspy Preact, Jan')).toBeInTheDocument();
});
```

## Pakiety

Definicje są w `package.json`, dokładne wersje w `package-lock.json`.

### Uruchomieniowe (`dependencies`)

| Pakiet | Do czego służy |
|---|---|
| `astro` | framework: strony, routing, renderowanie na serwerze |
| `@astrojs/node` | adapter Node, bez niego Astro nie uruchomi się w trybie SSR |
| `@astrojs/preact` | integracja Preact z Astro (wyspy `.tsx`) |
| `preact` | lekka biblioteka UI (alternatywa dla Reacta) do interaktywnych komponentów |
| `openapi-fetch` | mały klient HTTP z typami wygenerowanymi z OpenAPI |

### Deweloperskie (`devDependencies`)

| Pakiet | Do czego służy |
|---|---|
| `vitest` | runner testów jednostkowych |
| `@vitest/coverage-v8` | raport pokrycia kodu |
| `jsdom` | symulacja przeglądarki (DOM) w testach |
| `@testing-library/preact` | renderowanie wysp w testach i szukanie elementów jak użytkownik (rola, etykieta, tekst) |
| `@testing-library/user-event` | realistyczne klikanie i pisanie w testach |
| `@testing-library/jest-dom` | dodatkowe dopasowania: `toBeDisabled()`, `toBeInTheDocument()` |
| `msw` | udawanie backendu na poziomie sieci |
| `@playwright/test` | testy E2E w prawdziwej przeglądarce |
| `openapi-typescript` | generuje typy TypeScript z `openapi.json` backendu |
| `@astrojs/check` | silnik `astro check` (sprawdzanie typów w plikach `.astro`) |
| `typescript` | kompilator i sprawdzanie typów |

### Zarządzanie pakietami

| Zadanie | Komenda |
|---|---|
| zainstalować dokładnie to, co w locku (po `git pull`, w CI) | `npm ci` |
| dodać pakiet | `npm install nazwa` |
| dodać pakiet deweloperski | `npm install -D nazwa` |
| dodać integrację Astro | `npx astro add nazwa` |
| usunąć pakiet | `npm uninstall nazwa` |

Po każdej zmianie zależności commitujemy `package.json` razem z `package-lock.json`.

## Struktura

Poniżej układ docelowy (przynajmniej na razie). Elementy oznaczone `(brak)` jeszcze nie istnieją.

```
frontend/
├── src/
│   ├── pages/              # routing; dziś tylko index.astro (szablon)
│   │   ├── movies/[id].astro            # (brak) UC2
│   │   ├── screenings/[id].astro        # (brak) UC3, UC4
│   │   ├── reservations/                # (brak) UC5, UC6
│   │   └── admin/                       # (brak) UC7–UC10
│   ├── layouts/            # Layout.astro (do przerobienia na BaseLayout)
│   ├── components/
│   │   ├── Welcome.astro   # szablon Astro, do usunięcia
│   │   └── islands/        # interaktywne wyspy Preact (dziś tylko Hello.tsx)
│   ├── lib/                # (brak) api/ (klient + typy), services/, format.ts, errors.ts
│   └── middleware.ts       # (brak) ochrona /admin/*
├── tests/
│   ├── unit/               # testy Vitest
│   ├── mocks/server.ts     # serwer MSW
│   ├── setup.ts
│   └── e2e/                # (brak) testy Playwright
├── astro.config.mjs
├── vitest.config.ts
└── tsconfig.json           # JSX ustawiony pod Preact
```

**Co ma być interaktywne, a co nie.** Domyślnie wszystko jest zwykłym HTML-em renderowanym na serwerze (`.astro`). JavaScript dokładamy tylko tam, gdzie potrzeba: wybór miejsc, formularz rezerwacji, przycisk anulowania, formularze admina. To trzyma stronę lekką.

**Logika poza komponentami.** Wywołania API, mapowanie błędów (409 → komunikat) i formatowanie dat trzymamy w `src/lib/`, a wyspy i strony zostają cienkie. Zwykłe funkcje testuje się najłatwiej.

## Znane braki

- **Playwright nie jest skonfigurowany.** Skrypt `npm run test:e2e` istnieje, ale nie ma `playwright.config.ts` ani katalogu `tests/e2e/`. Przed pierwszym uruchomieniem: dodać konfigurację i wykonać `npx playwright install chromium` (pobiera przeglądarkę).
- **`npm run gen:api` nie zadziała**, dopóki nie powstanie `docs/openapi.json` (backend musi go wyeksportować).
- **Brak `src/lib/`**, więc nie ma jeszcze klienta API ani serwisów.
- **Pokrycie kodu** liczy tylko pliki `.ts` i `.tsx` z `src/`. Komponenty `.astro` nie wchodzą do raportu.

## Rady dla osób pracujących nad frontendem

**TDD we frontendzie**
- Zacznij od `npm run test:watch` w osobnym terminalu. Pisz test, zobacz, że pada, napisz minimum kodu, refaktoryzuj.
- Testuj to, co widzi użytkownik, a nie szczegóły implementacji. Szukaj elementów przez `getByRole`, `getByLabelText`, `getByText`, a w ostateczności przez `data-testid`.
- Elementom, które klika Playwright, dawaj `data-testid` (np. `seat-A1`). Zmiana tekstu lub wyglądu nie zepsuje wtedy testów.
- Oznaczaj testy identyfikatorem UC (`// UC4-A1`), tak jak w backendzie.
- W testach importuj `describe`, `it`, `expect`, `vi` z `vitest`. Opcja `globals: true` jest włączona w configu, ale `tsconfig.json` nie zna jej typów, więc edytor i `astro check` zgłosiłyby błędy przy importach pominiętych.

**Praca z API**
- Nie ustalaj formatu żądań i odpowiedzi „na oko". Źródłem prawdy jest backend, czyli `docs/openapi.json`. Po jego zmianie uruchom `npm run gen:api`, a potem `npm run typecheck`, który pokaże miejsca do poprawy.
- Nie edytuj ręcznie `src/lib/api/api-types.ts`, bo jest generowany i następne `gen:api` nadpisze zmiany.
- Komponenty nie budują żądań HTTP same. Robią to serwisy w `src/lib/services/`, które używają klienta z `openapi-fetch`.
- Błąd po stronie użytkownika (409, 400) pokazuj przy formularzu, a teksty komunikatów trzymaj w jednym miejscu (`lib/errors.ts`).

**Astro**
- Dane na stronach publicznych pobieraj w sekcji `---` pliku `.astro` (na serwerze) i przekazuj do wysp jako propsy.
- Dyrektywa `client:load` ładuje wyspę od razu, `client:visible` dopiero po przewinięciu do niej. Używaj najlżejszej, która wystarcza.
- Nie mieszaj frameworków wysp. W projekcie jest tylko Preact.
- Pamiętaj o dostępności: etykiety pól formularza, `aria-pressed` na przyciskach wyboru miejsca, obsługa klawiatury. Mapa sali musi działać na telefonie.

**Git i porządek**
- Pracuj na gałęzi (`feature/uc1-repertoire`), a przed pushem uruchom `npm run typecheck && npm test && npm run build`.
- Nie commituj: `node_modules/`, `dist/`, `.astro/`, `coverage/`, `.env`.
- Używaj `npm ci` (nie `npm install`) do zwykłego instalowania, żeby nie zmieniać `package-lock.json` bez potrzeby.

**Gdy coś nie działa**
- `document is not defined`: test nie leży w `tests/unit/` albo config nie jest wczytany. Sprawdź `include` i `environment: 'jsdom'` w `vitest.config.ts`.
- `toBeDisabled is not a function`: `tests/setup.ts` nie jest uruchamiany, sprawdź `setupFiles`.
- Test pada z komunikatem o niezamockowanym żądaniu: dodaj handler MSW przez `server.use(...)`. To zamierzone działanie.
- Błąd składni przy `.tsx`: sprawdź w `tsconfig.json` `"jsx": "react-jsx"` i `"jsxImportSource": "preact"` oraz integrację `preact()` w `astro.config.mjs`.
- Dziwne zachowanie po zmianie zależności: usuń `node_modules` i uruchom `npm ci`.
