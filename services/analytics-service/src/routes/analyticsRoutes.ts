import { Router, Request, Response, NextFunction } from 'express';
import { analyticsService } from '../services/analyticsService.js';

export const analyticsRouter = Router();

// GET /api/v1/analytics/daily-kpis
analyticsRouter.get('/daily-kpis', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const limit = parseInt(req.query.limit as string, 10) || 30;
    const kpis = await analyticsService.getDailyKpis(limit);
    res.json({
      content: kpis,
      totalElements: kpis.length,
      limit,
    });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/analytics/realtime-summary & /api/v1/analytics/summary
const summaryHandler = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const summary = await analyticsService.getRealtimeSummary();
    res.json(summary);
  } catch (err) {
    next(err);
  }
};
analyticsRouter.get('/realtime-summary', summaryHandler);
analyticsRouter.get('/summary', summaryHandler);

// GET /api/v1/analytics/orders-by-day
analyticsRouter.get('/orders-by-day', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const limit = parseInt(req.query.limit as string, 10) || 30;
    const kpis = await analyticsService.getDailyKpis(limit);
    const ordersByDay = kpis.map(k => ({
      date: k.date,
      orders: k.totalOrders,
      revenue: k.totalRevenue,
    }));
    res.json({ content: ordersByDay, totalElements: ordersByDay.length });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/analytics/top-products
analyticsRouter.get('/top-products', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const summary = await analyticsService.getRealtimeSummary();
    res.json({ content: summary.topProducts || [] });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/analytics/openapi.json
analyticsRouter.get('/openapi.json', (req: Request, res: Response) => {
  res.json({
    openapi: '3.0.3',
    info: {
      title: 'Food Operations Platform — Analytics Service',
      version: '1.0.0',
      description: 'Real-time KPI aggregation and streaming analytics engine',
    },
    paths: {
      '/api/v1/analytics/daily-kpis': {
        get: {
          summary: 'Retrieve historical daily KPIs',
          parameters: [
            {
              name: 'limit',
              in: 'query',
              required: false,
              schema: { type: 'integer', default: 30 },
            },
          ],
          responses: {
            '200': {
              description: 'List of daily KPIs',
            },
          },
        },
      },
      '/api/v1/analytics/realtime-summary': {
        get: {
          summary: 'Get live operational summary and hourly trends',
          responses: {
            '200': {
              description: 'Real-time KPI summary',
            },
          },
        },
      },
    },
  });
});
