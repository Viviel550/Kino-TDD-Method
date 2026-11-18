// frontend/vitest.config.ts
import { getViteConfig } from 'astro/config';

export default getViteConfig({
  test: {
    // symuluje przeglądarkę (DOM) dla testów wysp
    environment: 'jsdom',

    // uruchamiane przed każdym plikiem testowym (MSW, jest-dom)
    setupFiles: ['./tests/setup.ts'],

    // tylko testy jednostkowe, E2E obsługuje Playwright
    include: ['tests/unit/**/*.test.{ts,tsx}'],
    exclude: ['tests/e2e/**', 'node_modules/**'],

    // describe/it/expect bez importowania (opcjonalne)
    globals: true,

    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      include: ['src/**/*.{ts,tsx}'],
      // typy generowane z backendu nie wymagają testów
      exclude: ['src/lib/api/api-types.ts'],
    },
  },
});
