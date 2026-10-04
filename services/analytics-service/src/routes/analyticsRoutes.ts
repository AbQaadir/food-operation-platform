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

// GET /api/v1/analytics/realtime-summary
analyticsRouter.get('/realtime-summary', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const summary = await analyticsService.getRealtimeSummary();
    res.json(summary);
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
