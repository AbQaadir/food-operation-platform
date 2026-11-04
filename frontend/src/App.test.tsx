import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  it('renders platform title in header', () => {
    render(<App />);
    expect(screen.getByText('FoodOps')).toBeDefined();
    expect(screen.getByText('Enterprise Platform')).toBeDefined();
  });

  it('renders primary navigation links', () => {
    render(<App />);
    expect(screen.getByText('Dashboard')).toBeDefined();
    expect(screen.getByText('Products')).toBeDefined();
    expect(screen.getByText('Inventory')).toBeDefined();
    expect(screen.getByText('Orders')).toBeDefined();
    expect(screen.getByText('AI Assistant')).toBeDefined();
  });

  it('renders dashboard operations center headings', () => {
    render(<App />);
    expect(screen.getByText('Operations Control Center')).toBeDefined();
    expect(screen.getByText('Distributed Microservices Runtime Matrix')).toBeDefined();
  });
});
