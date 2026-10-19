import { pool } from '../config/database.js';
import { logger } from '../config/logger.js';

export interface DailyKpi {
  kpiDate: string;
  totalOrders: number;
  totalRevenue: number;
  confirmedOrders: number;
  cancelledOrders: number;
  lowStockAlerts: number;
  fulfillmentRatePercent: number;
  updatedAt: string;
}

export interface RealtimeSummary {
  today: DailyKpi;
  hourlyTrends: Array<{
    hour: string;
    orders: number;
    revenue: number;
  }>;
  sevenDayAverageRevenue: number;
  activeAlertsCount: number;
}

export class AnalyticsService {
  async isEventProcessed(eventId: string): Promise<boolean> {
    const res = await pool.query('SELECT 1 FROM processed_events WHERE event_id = $1', [eventId]);
    return res.rows.length > 0;
  }

  async markEventProcessed(eventId: string, eventType: string): Promise<void> {
    await pool.query(
      'INSERT INTO processed_events (event_id, event_type) VALUES ($1, $2) ON CONFLICT (event_id) DO NOTHING',
      [eventId, eventType]
    );
  }

  async processOrderCreated(eventId: string, orderId: string, totalAmount: number): Promise<void> {
    if (await this.isEventProcessed(eventId)) {
      logger.debug({ eventId }, 'Event already processed, skipping');
      return;
    }

    const today = new Date().toISOString().split('T')[0];
    const currentHour = new Date();
    currentHour.setMinutes(0, 0, 0);

    const client = await pool.connect();
    try {
      await client.query('BEGIN');

      await client.query(`
        INSERT INTO daily_kpis (kpi_date, total_orders, total_revenue, confirmed_orders, updated_at)
        VALUES ($1, 1, $2, 1, CURRENT_TIMESTAMP)
        ON CONFLICT (kpi_date) DO UPDATE
        SET total_orders = daily_kpis.total_orders + 1,
            total_revenue = daily_kpis.total_revenue + $2,
            confirmed_orders = daily_kpis.confirmed_orders + 1,
            updated_at = CURRENT_TIMESTAMP
      `, [today, totalAmount]);

      await client.query(`
        INSERT INTO hourly_order_stats (hour_timestamp, order_count, revenue, updated_at)
        VALUES ($1, 1, $2, CURRENT_TIMESTAMP)
        ON CONFLICT (hour_timestamp) DO UPDATE
        SET order_count = hourly_order_stats.order_count + 1,
            revenue = hourly_order_stats.revenue + $2,
            updated_at = CURRENT_TIMESTAMP
      `, [currentHour, totalAmount]);

      await client.query(
        'INSERT INTO processed_events (event_id, event_type) VALUES ($1, $2) ON CONFLICT (event_id) DO NOTHING',
        [eventId, 'order.created']
      );

      await client.query('COMMIT');
      logger.info({ orderId, totalAmount }, 'Processed order.created for analytics');
    } catch (err) {
      await client.query('ROLLBACK');
      throw err;
    } finally {
      client.release();
    }
  }

  async processOrderCancelled(eventId: string, orderId: string): Promise<void> {
    if (await this.isEventProcessed(eventId)) {
      return;
    }

    const today = new Date().toISOString().split('T')[0];

    await pool.query(`
      INSERT INTO daily_kpis (kpi_date, cancelled_orders, updated_at)
      VALUES ($1, 1, CURRENT_TIMESTAMP)
      ON CONFLICT (kpi_date) DO UPDATE
      SET cancelled_orders = daily_kpis.cancelled_orders + 1,
          updated_at = CURRENT_TIMESTAMP
    `, [today]);

    await this.markEventProcessed(eventId, 'order.cancelled');
    logger.info({ orderId }, 'Processed order.cancelled for analytics');
  }

  async processLowStockAlert(eventId: string, productId: string): Promise<void> {
    if (await this.isEventProcessed(eventId)) {
      return;
    }

    const today = new Date().toISOString().split('T')[0];

    await pool.query(`
      INSERT INTO daily_kpis (kpi_date, low_stock_alerts, updated_at)
      VALUES ($1, 1, CURRENT_TIMESTAMP)
      ON CONFLICT (kpi_date) DO UPDATE
      SET low_stock_alerts = daily_kpis.low_stock_alerts + 1,
          updated_at = CURRENT_TIMESTAMP
    `, [today]);

    await this.markEventProcessed(eventId, 'inventory.low-stock');
    logger.info({ productId }, 'Processed inventory.low-stock for analytics');
  }

  async getDailyKpis(limit: number = 30): Promise<DailyKpi[]> {
    const res = await pool.query(`
      SELECT 
        kpi_date as "kpiDate",
        total_orders as "totalOrders",
        total_revenue::numeric as "totalRevenue",
        confirmed_orders as "confirmedOrders",
        cancelled_orders as "cancelledOrders",
        low_stock_alerts as "lowStockAlerts",
        updated_at as "updatedAt"
      FROM daily_kpis
      ORDER BY kpi_date DESC
      LIMIT $1
    `, [limit]);

    return res.rows.map(row => ({
      ...row,
      totalRevenue: parseFloat(row.totalRevenue) || 0,
      fulfillmentRatePercent: row.totalOrders > 0
        ? Math.round(((row.confirmedOrders) / (row.totalOrders)) * 1000) / 10
        : 100,
    }));
  }

  async getRealtimeSummary(): Promise<RealtimeSummary> {
    const today = new Date().toISOString().split('T')[0];
    const kpis = await this.getDailyKpis(7);
    const todayKpi = kpis.find(k => k.kpiDate === today) || {
      kpiDate: today,
      totalOrders: 0,
      totalRevenue: 0,
      confirmedOrders: 0,
      cancelledOrders: 0,
      lowStockAlerts: 0,
      fulfillmentRatePercent: 100,
      updatedAt: new Date().toISOString(),
    };

    const hourlyRes = await pool.query(`
      SELECT 
        TO_CHAR(hour_timestamp, 'HH24:00') as "hour",
        order_count as "orders",
        revenue::numeric as "revenue"
      FROM hourly_order_stats
      WHERE hour_timestamp >= NOW() - INTERVAL '12 hours'
      ORDER BY hour_timestamp ASC
    `);

    const totalRev7Days = kpis.reduce((acc, curr) => acc + curr.totalRevenue, 0);
    const sevenDayAvg = kpis.length > 0 ? Math.round((totalRev7Days / kpis.length) * 100) / 100 : 0;

    return {
      today: todayKpi,
      hourlyTrends: hourlyRes.rows.map(r => ({
        hour: r.hour,
        orders: parseInt(r.orders, 10),
        revenue: parseFloat(r.revenue) || 0,
      })),
      sevenDayAverageRevenue: sevenDayAvg,
      activeAlertsCount: todayKpi.lowStockAlerts,
    };
  }
}

export const analyticsService = new AnalyticsService();
