import { Redis } from 'ioredis';
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
