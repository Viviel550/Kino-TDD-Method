// tests/unit/Hello.test.tsx
import { it, expect } from 'vitest';
import { render, screen } from '@testing-library/preact';
import { Hello } from '../../src/components/islands/Hello';

it('renderuje komponent', () => {
  render(<Hello name="Wyspa 3.0" />);
  expect(screen.getByText('Test wyspy Preact, Wyspa 3.0')).toBeInTheDocument();
});
