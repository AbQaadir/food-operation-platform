import { describe, it, expect, vi } from 'vitest';
import request from 'supertest';

// Mock DB pool
vi.mock('./config/database.js', () => {
  const mPool = {
    connect: vi.fn().mockResolvedValue({
      query: vi.fn().mockResolvedValue({ rows: [] }),
      release: vi.fn(),
    }),
    query: vi.fn().mockImplementation((queryText: string) => {
      if (queryText.includes('daily_kpis')) {
        return Promise.resolve({
          rows: [
            {
              kpiDate: '2026-10-04',
              totalOrders: 10,
              totalRevenue: '500.00',
              confirmedOrders: 9,
              cancelledOrders: 1,
              lowStockAlerts: 0,
              updatedAt: new Date().toISOString(),
            },
          ],
        });
      }
      if (queryText.includes('hourly_order_stats')) {
        return Promise.resolve({
          rows: [
            { hour: '14:00', orders: 5, revenue: '250.00' },
          ],
        });
      }
      return Promise.resolve({ rows: [] });
    }),
  };
  return { pool: mPool, initDatabase: vi.fn().mockResolvedValue(undefined) };
});

// Mock Kafka
vi.mock('./consumers/kafkaConsumer.js', () => ({
  startKafkaConsumer: vi.fn().mockResolvedValue(undefined),
  consumer: { connect: vi.fn(), disconnect: vi.fn() },
}));

import { app } from './index.js';

describe('Analytics Service API', () => {
  it('GET /health returns 200 and UP status', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('UP');
    expect(res.body.service).toBe('analytics-service');
  });

  it('GET /ready returns 200 with dependency checks', async () => {
    const res = await request(app).get('/ready');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('UP');
    expect(res.body.checks.database).toBe('UP');
  });

  it('GET /metrics returns Prometheus metric format', async () => {
    const res = await request(app).get('/metrics');
    expect(res.status).toBe(200);
    expect(res.text).toContain('analytics_events_processed_total');
    expect(res.text).toContain('analytics_daily_revenue');
  });

  it('GET /api/v1/analytics/daily-kpis returns aggregated KPIs', async () => {
    const res = await request(app).get('/api/v1/analytics/daily-kpis');
    expect(res.status).toBe(200);
    expect(res.body.content).toBeDefined();
    expect(Array.isArray(res.body.content)).toBe(true);
    expect(res.body.content[0].kpiDate).toBe('2026-10-04');
    expect(res.body.content[0].fulfillmentRatePercent).toBe(90);
  });

  it('GET /api/v1/analytics/realtime-summary returns summary and trends', async () => {
    const res = await request(app).get('/api/v1/analytics/realtime-summary');
    expect(res.status).toBe(200);
    expect(res.body.today).toBeDefined();
    expect(res.body.hourlyTrends).toBeDefined();
    expect(res.body.sevenDayAverageRevenue).toBeDefined();
  });

  it('GET /api/v1/analytics/openapi.json returns valid OpenAPI 3.0 specification', async () => {
    const res = await request(app).get('/api/v1/analytics/openapi.json');
    expect(res.status).toBe(200);
    expect(res.body.openapi).toBe('3.0.3');
    expect(res.body.info.title).toContain('Analytics Service');
  });
});
