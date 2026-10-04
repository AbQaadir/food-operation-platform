#!/usr/bin/env python3
import os

BASE = "/Users/qaadir/Desktop/dev/foodOperationPlatform/services/notification-service"

FILES = {
    # package.json
    f"{BASE}/package.json": """{
  "name": "notification-service",
  "version": "1.0.0",
  "description": "Notification microservice for Enterprise Food Operations Platform",
  "main": "dist/index.js",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "vitest run"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.4.5",
    "express": "^4.21.0",
    "helmet": "^7.1.0",
    "ioredis": "^5.4.1",
    "kafkajs": "^2.2.4",
    "pg": "^8.13.0",
    "pino": "^9.4.0",
    "uuid": "^10.0.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/cors": "^2.8.17",
    "@types/express": "^4.17.21",
    "@types/node": "^22.5.5",
    "@types/pg": "^8.11.10",
    "@types/supertest": "^6.0.2",
    "@types/uuid": "^10.0.0",
    "pino-pretty": "^11.2.2",
    "supertest": "^7.0.0",
    "tsx": "^4.19.1",
    "typescript": "^5.6.2",
    "vitest": "^2.1.1"
  }
}
""",

    # tsconfig.json
    f"{BASE}/tsconfig.json": """{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"]
}
""",

    # Dockerfile
    f"{BASE}/Dockerfile": """FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev
COPY --from=builder /app/dist ./dist

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
EXPOSE 8085
CMD ["node", "dist/index.js"]
""",

    # src/config/logger.ts
    f"{BASE}/src/config/logger.ts": """import pino from 'pino';

export const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label })
  },
  timestamp: pino.stdTimeFunctions.isoTime
});
""",

    # src/config/database.ts
    f"{BASE}/src/config/database.ts": """import { Pool } from 'pg';
import { logger } from './logger.js';

export const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: parseInt(process.env.POSTGRES_PORT || '5432', 10),
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'postgres',
  database: 'notification_db',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000
});

export async function initDatabase() {
  const client = await pool.connect();
  try {
    await client.query(`
      CREATE TABLE IF NOT EXISTS notifications (
        id UUID PRIMARY KEY,
        user_id UUID NOT NULL,
        type VARCHAR(100) NOT NULL,
        title VARCHAR(255) NOT NULL,
        body TEXT NOT NULL,
        read BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
      CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
      CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, read);
    `);
    logger.info('Notification database schema initialized successfully');
  } finally {
    client.release();
  }
}
""",

    # src/config/redis.ts
    f"{BASE}/src/config/redis.ts": """import { Redis } from 'ioredis';
import { logger } from './logger.js';

export const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379', 10),
  retryStrategy: (times) => Math.min(times * 100, 3000),
  maxRetriesPerRequest: 3,
  lazyConnect: true
});

redis.on('connect', () => logger.info('Connected to Redis'));
redis.on('error', (err) => logger.warn(`Redis connection warning: ${err.message}`));
""",

    # src/services/sseManager.ts
    f"{BASE}/src/services/sseManager.ts": """import { Response } from 'express';
import { logger } from '../config/logger.js';

interface Client {
  userId: string;
  res: Response;
}

class SseManager {
  private clients: Map<string, Set<Response>> = new Map();

  addClient(userId: string, res: Response) {
    if (!this.clients.has(userId)) {
      this.clients.set(userId, new Set());
    }
    this.clients.get(userId)!.add(res);
    logger.info(`SSE client connected for user ${userId}. Total: ${this.clients.get(userId)!.size}`);

    res.on('close', () => {
      const userClients = this.clients.get(userId);
      if (userClients) {
        userClients.delete(res);
        if (userClients.size === 0) {
          this.clients.delete(userId);
        }
      }
      logger.info(`SSE client disconnected for user ${userId}`);
    });
  }

  sendToUser(userId: string, event: string, data: any) {
    const userClients = this.clients.get(userId);
    if (!userClients || userClients.size === 0) return;

    const payload = `event: ${event}\\ndata: ${JSON.stringify(data)}\\n\\n`;
    userClients.forEach((res) => {
      try {
        res.write(payload);
      } catch (err: any) {
        logger.warn(`Failed to write SSE to client: ${err.message}`);
      }
    });
  }

  broadcast(event: string, data: any) {
    const payload = `event: ${event}\\ndata: ${JSON.stringify(data)}\\n\\n`;
    this.clients.forEach((userClients) => {
      userClients.forEach((res) => {
        try {
          res.write(payload);
        } catch (err: any) {
          logger.warn(`Failed to broadcast SSE: ${err.message}`);
        }
      });
    });
  }
}

export const sseManager = new SseManager();
""",

    # src/services/notificationService.ts
    f"{BASE}/src/services/notificationService.ts": """import { v4 as uuidv4 } from 'uuid';
import { pool } from '../config/database.js';
import { redis } from '../config/redis.js';
import { sseManager } from './sseManager.js';
import { logger } from '../config/logger.js';

export interface Notification {
  id: string;
  userId: string;
  type: string;
  title: string;
  body: string;
  read: boolean;
  createdAt: string;
}

export class NotificationService {
  private static UNREAD_KEY_PREFIX = 'unread:user:';

  static async createNotification(userId: string, type: string, title: string, body: string): Promise<Notification> {
    const id = uuidv4();
    const result = await pool.query(
      `INSERT INTO notifications (id, user_id, type, title, body, read, created_at)
       VALUES ($1, $2, $3, $4, $5, FALSE, NOW())
       RETURNING id, user_id as "userId", type, title, body, read, created_at as "createdAt"`,
      [id, userId, type, title, body]
    );

    const notification: Notification = result.rows[0];

    // Maintain unread count in Redis
    try {
      await redis.incr(`${this.UNREAD_KEY_PREFIX}${userId}`);
    } catch (err: any) {
      logger.warn(`Redis incr error: ${err.message}`);
    }

    // Push real-time SSE event
    sseManager.sendToUser(userId, 'notification', notification);
    logger.info(`Created notification ${id} for user ${userId}: ${title}`);

    return notification;
  }

  static async getNotifications(userId: string, page = 0, size = 20): Promise<{ content: Notification[]; page: number; size: number; totalElements: number; totalPages: number }> {
    const offset = page * size;
    const countResult = await pool.query('SELECT COUNT(*) FROM notifications WHERE user_id = $1', [userId]);
    const totalElements = parseInt(countResult.rows[0].count, 10);
    const totalPages = Math.ceil(totalElements / size);

    const rowsResult = await pool.query(
      `SELECT id, user_id as "userId", type, title, body, read, created_at as "createdAt"
       FROM notifications
       WHERE user_id = $1
       ORDER BY created_at DESC
       LIMIT $2 OFFSET $3`,
      [userId, size, offset]
    );

    return {
      content: rowsResult.rows,
      page,
      size,
      totalElements,
      totalPages
    };
  }

  static async markAsRead(id: string, userId?: string): Promise<boolean> {
    const query = userId
      ? 'UPDATE notifications SET read = TRUE WHERE id = $1 AND user_id = $2 AND read = FALSE RETURNING user_id as "userId"'
      : 'UPDATE notifications SET read = TRUE WHERE id = $1 AND read = FALSE RETURNING user_id as "userId"';
    const params = userId ? [id, userId] : [id];

    const result = await pool.query(query, params);
    if (result.rowCount && result.rowCount > 0) {
      const uId = result.rows[0].userId;
      try {
        const count = await redis.decr(`${this.UNREAD_KEY_PREFIX}${uId}`);
        if (count < 0) {
          await redis.set(`${this.UNREAD_KEY_PREFIX}${uId}`, 0);
        }
      } catch (err: any) {
        logger.warn(`Redis decr error: ${err.message}`);
      }
      return true;
    }
    return false;
  }

  static async getUnreadCount(userId: string): Promise<number> {
    try {
      const cached = await redis.get(`${this.UNREAD_KEY_PREFIX}${userId}`);
      if (cached !== null) {
        return parseInt(cached, 10);
      }
    } catch (err: any) {
      logger.warn(`Redis get error: ${err.message}`);
    }

    const result = await pool.query('SELECT COUNT(*) FROM notifications WHERE user_id = $1 AND read = FALSE', [userId]);
    const count = parseInt(result.rows[0].count, 10);

    try {
      await redis.set(`${this.UNREAD_KEY_PREFIX}${userId}`, count, 'EX', 3600);
    } catch (err: any) {
      logger.warn(`Redis set error: ${err.message}`);
    }

    return count;
  }
}
""",

    # src/consumers/kafkaConsumer.ts
    f"{BASE}/src/consumers/kafkaConsumer.ts": """import { Kafka } from 'kafkajs';
import { NotificationService } from '../services/notificationService.js';
import { sseManager } from '../services/sseManager.js';
import { logger } from '../config/logger.js';

export const kafka = new Kafka({
  clientId: 'notification-service',
  brokers: (process.env.KAFKA_BOOTSTRAP_SERVERS || 'localhost:9092').split(','),
  retry: {
    initialRetryTime: 300,
    retries: 5
  }
});

const consumer = kafka.consumer({ groupId: 'notification-service-group' });

export async function startKafkaConsumer() {
  try {
    await consumer.connect();
    logger.info('Kafka consumer connected');

    await consumer.subscribe({ topic: 'order.confirmed', fromBeginning: false });
    await consumer.subscribe({ topic: 'order.cancelled', fromBeginning: false });
    await consumer.subscribe({ topic: 'inventory.low-stock', fromBeginning: false });
    logger.info('Subscribed to topics: order.confirmed, order.cancelled, inventory.low-stock');

    await consumer.run({
      eachMessage: async ({ topic, partition, message }) => {
        if (!message.value) return;

        try {
          const rawString = message.value.toString();
          const payload = JSON.parse(rawString);
          logger.info(`Received event on topic ${topic}: ${rawString}`);

          if (topic === 'order.confirmed') {
            const customerId = payload.customerId || '5fc0741f-9724-4446-8dcb-c7fac24a4c80';
            await NotificationService.createNotification(
              customerId,
              'ORDER_CONFIRMED',
              'Order Confirmed!',
              `Your order #${payload.orderId} has been confirmed and inventory allocated successfully.`
            );
          } else if (topic === 'order.cancelled') {
            const customerId = payload.customerId || '5fc0741f-9724-4446-8dcb-c7fac24a4c80';
            await NotificationService.createNotification(
              customerId,
              'ORDER_CANCELLED',
              'Order Cancelled',
              `Your order #${payload.orderId} was cancelled. Reason: ${payload.reason || 'Not specified'}.`
            );
          } else if (topic === 'inventory.low-stock') {
            // Broadcast low stock alerts to manager/warehouse operators
            const adminId = '5fc0741f-9724-4446-8dcb-c7fac24a4c80';
            await NotificationService.createNotification(
              adminId,
              'LOW_STOCK_ALERT',
              'Low Stock Alert!',
              `Product ${payload.productId} in warehouse ${payload.warehouseId} has fallen below threshold (${payload.available} available).`
            );
          }
        } catch (err: any) {
          logger.error(`Error processing message on topic ${topic}: ${err.message}`);
        }
      }
    });
  } catch (err: any) {
    logger.warn(`Kafka consumer failed to start: ${err.message}`);
  }
}
""",

    # src/routes/notificationRoutes.ts
    f"{BASE}/src/routes/notificationRoutes.ts": """import { Router, Request, Response, NextFunction } from 'express';
import { NotificationService } from '../services/notificationService.js';
import { sseManager } from '../services/sseManager.js';
import { z } from 'zod';

export const router = Router();

const DEFAULT_USER_ID = '5fc0741f-9724-4446-8dcb-c7fac24a4c80'; // fallback admin/customer

function getUserId(req: Request): string {
  const headerId = req.headers['x-user-id'] as string;
  return headerId || DEFAULT_USER_ID;
}

// GET /api/v1/notifications
router.get('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const userId = getUserId(req);
    const page = parseInt(req.query.page as string || '0', 10);
    const size = parseInt(req.query.size as string || '20', 10);
    const result = await NotificationService.getNotifications(userId, page, size);
    res.json(result);
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/notifications/unread-count
router.get('/unread-count', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const userId = getUserId(req);
    const count = await NotificationService.getUnreadCount(userId);
    res.json({ userId, unreadCount: count });
  } catch (err) {
    next(err);
  }
});

// PATCH /api/v1/notifications/:id/read
router.patch('/:id/read', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const { id } = req.params;
    const userId = getUserId(req);
    const updated = await NotificationService.markAsRead(id, userId);
    if (!updated) {
      return res.status(404).json({
        type: 'https://foodplatform.com/errors/not-found',
        title: 'Notification Not Found',
        status: 404,
        detail: `Notification not found or already read: ${id}`
      });
    }
    res.json({ id, read: true, message: 'Notification marked as read' });
  } catch (err) {
    next(err);
  }
});

// GET /api/v1/notifications/stream (Server-Sent Events)
router.get('/stream', (req: Request, res: Response) => {
  const userId = getUserId(req);

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders();

  // Send initial connected event
  res.write(`event: connected\\ndata: ${JSON.stringify({ status: 'connected', userId })}\\n\\n`);

  // Heartbeat ping every 15s to keep proxy connections alive
  const heartbeat = setInterval(() => {
    res.write(': heartbeat\\n\\n');
  }, 15000);

  res.on('close', () => {
    clearInterval(heartbeat);
  });

  sseManager.addClient(userId, res);
});
""",

    # src/index.ts
    f"{BASE}/src/index.ts": """import express, { Request, Response, NextFunction } from 'express';
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
    await startKafkaConsumer();

    app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Notification Service listening on port ${PORT}`);
    });
  } catch (err: any) {
    logger.error({ err }, 'Failed to start Notification Service');
    process.exit(1);
  }
}

main();
"""
}

for path, content in FILES.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

print("All notification-service source files written successfully.")
