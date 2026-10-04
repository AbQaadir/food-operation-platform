import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  it('renders platform title in header', () => {
    render(<App />);
    expect(screen.getByText('FoodOps')).toBeDefined();
    expect(screen.getByText('Enterprise Platform')).toBeDefined();
  });
});
