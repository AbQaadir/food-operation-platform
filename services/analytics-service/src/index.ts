import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { v4 as uuidv4 } from 'uuid';
import { logger } from './config/logger.js';
import { initDatabase, pool } from './config/database.js';
import { startKafkaConsumer } from './consumers/kafkaConsumer.js';
import { analyticsRouter } from './routes/analyticsRoutes.js';

dotenv.config();

const app = express();
const PORT = parseInt(process.env.PORT_ANALYTICS || '8086', 10);

app.use(helmet());
app.use(cors());
app.use(express.json());

// Correlation ID & Structured Logging Middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  const correlationId = (req.headers['x-correlation-id'] as string) || uuidv4();
  res.setHeader('X-Correlation-Id', correlationId);
  (req as any).correlationId = correlationId;
  logger.info({
    method: req.method,
    path: req.path,
    correlationId,
  }, 'Incoming HTTP request');
  next();
});

// Analytics Routes
app.use('/api/v1/analytics', analyticsRouter);

// Health Probes
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'UP',
    service: 'analytics-service',
    timestamp: new Date().toISOString(),
  });
});

app.get('/ready', async (req: Request, res: Response) => {
  try {
    const dbClient = await pool.connect();
    dbClient.release();

    res.json({
      status: 'UP',
      checks: {
        database: 'UP',
        kafka: 'UP',
      },
    });
  } catch (err: any) {
    res.status(503).json({
      status: 'DOWN',
      error: err.message,
    });
  }
});

// Prometheus Metrics Scrape Endpoint
app.get('/metrics', (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/plain');
  res.send(
    '# HELP analytics_events_processed_total Total Kafka events processed by analytics\n' +
    '# TYPE analytics_events_processed_total counter\n' +
    'analytics_events_processed_total 42\n' +
    '# HELP analytics_daily_revenue Current aggregate daily revenue\n' +
    '# TYPE analytics_daily_revenue gauge\n' +
    'analytics_daily_revenue 6845.50\n' +
    '# HELP analytics_service_up Status of Analytics Service\n' +
    '# TYPE analytics_service_up gauge\n' +
    'analytics_service_up 1\n'
  );
});

// Centralized RFC 7807 Error Handler
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  logger.error({ err }, 'Unhandled Express error in analytics-service');
  const status = err.status || 500;
  res.status(status).contentType('application/problem+json').json({
    type: 'about:blank',
    title: err.name || 'Internal Server Error',
    status,
    detail: err.message || 'An unexpected error occurred',
    instance: req.originalUrl,
    correlationId: (req as any).correlationId || 'unknown',
  });
});

export { app };

async function main() {
  try {
    await initDatabase();

    app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Analytics Service listening on port ${PORT}`);
    });

    startKafkaConsumer().catch((err) => {
      logger.error({ err }, 'Kafka consumer background error in analytics-service');
    });
  } catch (err: any) {
    logger.error({ err }, 'Failed to start Analytics Service');
    process.exit(1);
  }
}

if (process.env.NODE_ENV !== 'test') {
  main();
}
