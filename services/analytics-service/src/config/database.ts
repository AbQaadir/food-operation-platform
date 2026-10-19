import { Pool } from 'pg';
import { logger } from './logger.js';

export const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432', 10),
  database: process.env.POSTGRES_DB || 'analytics_db',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres',
  max: 10,
  idleTimeoutMillis: 30000,
});

export async function initDatabase() {
  const client = await pool.connect();
  try {
    logger.info('Initializing analytics_db schema...');

    await client.query(`
      CREATE TABLE IF NOT EXISTS daily_kpis (
        kpi_date DATE PRIMARY KEY,
        total_orders INT NOT NULL DEFAULT 0,
        total_revenue NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
        confirmed_orders INT NOT NULL DEFAULT 0,
        cancelled_orders INT NOT NULL DEFAULT 0,
        low_stock_alerts INT NOT NULL DEFAULT 0,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS hourly_order_stats (
        hour_timestamp TIMESTAMP PRIMARY KEY,
        order_count INT NOT NULL DEFAULT 0,
        revenue NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      );

      CREATE TABLE IF NOT EXISTS processed_events (
        event_id VARCHAR(128) PRIMARY KEY,
        event_type VARCHAR(64) NOT NULL,
        processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_daily_kpis_date ON daily_kpis(kpi_date DESC);
      CREATE INDEX IF NOT EXISTS idx_hourly_stats_timestamp ON hourly_order_stats(hour_timestamp DESC);
    `);

    const today = new Date().toISOString().split('T')[0];
    await client.query(`
      INSERT INTO daily_kpis (kpi_date, total_orders, total_revenue, confirmed_orders, cancelled_orders, low_stock_alerts)
      VALUES ($1, 142, 6845.50, 138, 4, 3)
      ON CONFLICT (kpi_date) DO NOTHING;
    `, [today]);

    logger.info('analytics_db schema initialized successfully');
  } catch (err: any) {
    logger.error({ err }, 'Failed to initialize analytics_db');
    throw err;
  } finally {
    client.release();
  }
}
