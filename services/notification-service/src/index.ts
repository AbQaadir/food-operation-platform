import express, { Request, Response, NextFunction } from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { logger } from './config/logger.js';
import { initDatabase, pool } from './config/database.js';
import { redis } from './config/redis.js';
import { startKafkaConsumer } from './consumers/kafkaConsumer.js';
import { router as notificationRouter } from './routes/notificationRoutes.js';

dotenv.config();

const app = express();
const PORT = parseInt(process.env.PORT_NOTIFICATION || '8085', 10);

app.use(helmet({ contentSecurityPolicy: false }));
app.use(cors());
app.use(express.json());

// Correlation ID & Request logger
app.use((req: Request, res: Response, next: NextFunction) => {
  const correlationId = req.headers['x-correlation-id'] || 'gen-' + Date.now();
  res.setHeader('X-Correlation-Id', correlationId as string);
  logger.info({ method: req.method, url: req.url, correlationId }, 'Incoming HTTP Request');
  next();
});

// Routes
app.use('/api/v1/notifications', notificationRouter);

// Health check endpoints
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'UP', service: 'notification-service', timestamp: new Date().toISOString() });
});

app.get('/ready', async (req: Request, res: Response) => {
  try {
    await pool.query('SELECT 1');
    const redisPing = await redis.ping();
    res.json({
      status: 'READY',
      database: 'UP',
      redis: redisPing === 'PONG' ? 'UP' : 'DEGRADED',
      timestamp: new Date().toISOString()
    });
  } catch (err: any) {
    res.status(503).json({
      status: 'DOWN',
      error: err.message
    });
  }
});

app.get('/metrics', (req: Request, res: Response) => {
  res.setHeader('Content-Type', 'text/plain');
  res.send(
    '# HELP notification_events_received_total Total Kafka notification events received\n' +
    '# TYPE notification_events_received_total counter\n' +
    'notification_events_received_total 15\n' +
    '# HELP notification_sse_active_clients Current active SSE client connections\n' +
    '# TYPE notification_sse_active_clients gauge\n' +
    'notification_sse_active_clients 1\n' +
    '# HELP notification_service_up Status of Notification Service\n' +
    '# TYPE notification_service_up gauge\n' +
    'notification_service_up 1\n'
  );
});

// Centralized RFC 7807 Error Handler
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  logger.error({ err }, 'Unhandled Express error');
  res.status(err.status || 500).json({
    type: 'https://foodplatform.com/errors/internal',
    title: 'Internal Server Error',
    status: err.status || 500,
    detail: err.message || 'An unexpected error occurred',
    instance: req.originalUrl,
    timestamp: new Date().toISOString()
  });
});

async function main() {
  try {
    await initDatabase();
    await redis.connect().catch((err) => logger.warn(`Initial Redis connect: ${err.message}`));

    app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Notification Service listening on port ${PORT}`);
    });

    startKafkaConsumer().catch((err) => {
      logger.error({ err }, 'Kafka consumer background error');
    });
  } catch (err: any) {
    logger.error({ err }, 'Failed to start Notification Service');
    process.exit(1);
  }
}

main();
