import { Kafka, Consumer } from 'kafkajs';
import { createHash } from 'node:crypto';
import { logger } from '../config/logger.js';
import { analyticsService } from '../services/analyticsService.js';

/** Decode a Kafka record value: plain object, JSON string, or double-encoded JSON string. */
export function decodePayload(raw: string): any {
  let parsed: any = JSON.parse(raw);
  if (typeof parsed === 'string') {
    parsed = JSON.parse(parsed);
  }
  return parsed;
}

const kafkaBroker = process.env.KAFKA_BOOTSTRAP_SERVERS || 'kafka:9092';

export const kafka = new Kafka({
  clientId: 'analytics-service',
  brokers: [kafkaBroker],
  retry: {
    initialRetryTime: 300,
    retries: 5,
  },
});

export const consumer: Consumer = kafka.consumer({
  groupId: 'analytics-service-group',
});

export async function startKafkaConsumer(): Promise<void> {
  const maxAttempts = Number(process.env.KAFKA_CONSUMER_START_MAX_ATTEMPTS || 30);
  let delayMs = 1000;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await consumer.connect();
      logger.info(`Kafka consumer connected to ${kafkaBroker}`);

      await consumer.subscribe({
        topics: ['order.created', 'order.cancelled', 'inventory.low-stock'],
        fromBeginning: false,
      });

      await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
          try {
            const valueStr = message.value?.toString();
            if (!valueStr) return;

            const payload = decodePayload(valueStr);
            const headerEventId = message.headers?.['eventId']?.toString();
            const eventId = (headerEventId ||
              payload.eventId ||
              'sha256:' + createHash('sha256').update(valueStr).digest('hex')) as string;

            logger.info({ topic, partition, eventId }, 'Received Kafka event in analytics-service');

            if (topic === 'order.created') {
              const orderId = payload.orderId || payload.id;
              const totalAmount = parseFloat(payload.totalAmount) || 0;
              if (orderId) {
                await analyticsService.processOrderCreated(eventId, orderId, totalAmount);
              }
            } else if (topic === 'order.cancelled') {
              const orderId = payload.orderId || payload.id;
              if (orderId) {
                await analyticsService.processOrderCancelled(eventId, orderId);
              }
            } else if (topic === 'inventory.low-stock') {
              const productId = payload.productId;
              if (productId) {
                await analyticsService.processLowStockAlert(eventId, productId);
              }
            }
          } catch (err: any) {
            logger.error({ err, topic }, 'Failed processing event in analytics-service');
          }
        },
      });

      logger.info('Kafka consumer listening on order and inventory topics');
      return;
    } catch (err: any) {
      logger.warn(`Kafka consumer start attempt ${attempt}/${maxAttempts} failed for analytics-service: ${err.message}`);
      if (attempt === maxAttempts) {
        logger.error({ err }, 'Failed to start Kafka consumer for analytics-service after all attempts');
        throw err;
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      delayMs = Math.min(delayMs * 2, 15000);
    }
  }
}
