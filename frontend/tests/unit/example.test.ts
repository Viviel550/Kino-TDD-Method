import { describe, it, expect } from 'vitest';

describe('konfiguracja Vitest', () => {
  it('uruchamia testy', () => {
    expect(1 + 1).toBe(2);
  });

  it('ma środowisko jsdom (document istnieje)', () => {
    document.body.innerHTML = '<button disabled>Zarezerwuj</button>';
    const btn = document.querySelector('button');
    expect(btn).not.toBeNull();
  });

  it('ma załadowane dopasowania jest-dom (setup.ts działa)', () => {
    document.body.innerHTML = '<button disabled>Zarezerwuj</button>';
    expect(document.querySelector('button')).toBeDisabled();
  });
});
