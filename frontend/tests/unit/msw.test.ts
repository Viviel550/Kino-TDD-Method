import { it, expect } from 'vitest';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';

it('MSW przechwytuje żądania', async () => {
  server.use(
    http.get('http://localhost:8000/health', () =>
      HttpResponse.json({ status: 'ok' })),
  );

  const res = await fetch('http://localhost:8000/health');
  expect(await res.json()).toEqual({ status: 'ok' });
});

it('MSW zgłasza błąd dla niezamockowanego żądania', async () => {
  await expect(fetch('http://localhost:8000/nieznany')).rejects.toThrow();
});
