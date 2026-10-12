import { Kafka, Producer } from 'kafkajs';
import { createHash } from 'node:crypto';
import { NotificationService } from '../services/notificationService.js';
import { logger } from '../config/logger.js';
import { pool } from '../config/database.js';

export const kafka = new Kafka({
  clientId: 'notification-service',
  brokers: (process.env.KAFKA_BOOTSTRAP_SERVERS || 'localhost:9092').split(','),
  retry: {
    initialRetryTime: 300,
    retries: 10
  }
});

const consumer = kafka.consumer({ groupId: 'notification-service-group' });

const TOPICS = ['order.confirmed', 'order.rejected', 'order.cancelled', 'inventory.low-stock'];

// Seed demo user ids (identity-service DataInitializer uses fixed UUIDs in dev)
const DEFAULT_LOW_STOCK_RECIPIENTS = [
  '00000000-0000-0000-0000-000000000002', // manager@foodplatform.com
  '00000000-0000-0000-0000-000000000003'  // operator@foodplatform.com
];

let producer: Producer | null = null;

async function getProducer(): Promise<Producer> {
  if (!producer) {
    producer = kafka.producer();
    await producer.connect();
  }
  return producer;
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function lowStockRecipients(): string[] {
  const configured = process.env.LOW_STOCK_ALERT_USER_IDS;
  if (configured && configured.trim().length > 0) {
    return configured.split(',').map((s) => s.trim()).filter(Boolean);
  }
  return DEFAULT_LOW_STOCK_RECIPIENTS;
}

/** Decode a Kafka record value: plain object, JSON string, or double-encoded JSON string. */
export function decodePayload(raw: string): any {
  let parsed: any = JSON.parse(raw);
  if (typeof parsed === 'string') {
    parsed = JSON.parse(parsed);
  }
  return parsed;
}

/** Stable event identity: header -> payload.eventId -> sha256 of the raw value. */
function eventIdFor(raw: string, headers: Record<string, unknown> | undefined): string {
  const headerId = headers?.['eventId']?.toString();
  if (headerId) return headerId;
  try {
    const parsed = decodePayload(raw);
    if (parsed && typeof parsed.eventId === 'string') return parsed.eventId;
  } catch {
    /* fall through to hash */
  }
  return 'sha256:' + createHash('sha256').update(raw).digest('hex');
}

/** Claim-first idempotency: returns false when the event was already processed. */
async function claimEvent(eventId: string, topic: string): Promise<boolean> {
  const result = await pool.query(
    `INSERT INTO processed_events (event_id, topic) VALUES ($1, $2)
     ON CONFLICT (event_id) DO NOTHING RETURNING event_id`,
    [eventId, topic]
  );
  return (result.rowCount ?? 0) > 0;
}

async function releaseClaim(eventId: string): Promise<void> {
  await pool.query('DELETE FROM processed_events WHERE event_id = $1', [eventId]);
}

async function processEvent(topic: string, payload: any): Promise<void> {
  if (topic === 'order.confirmed') {
    if (!payload.customerId) throw new Error('order.confirmed payload is missing customerId');
    await NotificationService.createNotification(
      payload.customerId,
      'ORDER_CONFIRMED',
      'Order Confirmed!',
      `Your order #${payload.orderId} has been confirmed and inventory allocated successfully.`
    );
  } else if (topic === 'order.rejected') {
    if (!payload.customerId) throw new Error('order.rejected payload is missing customerId');
    await NotificationService.createNotification(
      payload.customerId,
      'ORDER_REJECTED',
      'Order Rejected',
      `Your order #${payload.orderId} could not be confirmed. Reason: ${payload.reason || 'Insufficient stock'}.`
    );
  } else if (topic === 'order.cancelled') {
    if (!payload.customerId) throw new Error('order.cancelled payload is missing customerId');
    await NotificationService.createNotification(
      payload.customerId,
      'ORDER_CANCELLED',
      'Order Cancelled',
      `Your order #${payload.orderId} was cancelled. Reason: ${payload.reason || 'Not specified'}.`
    );
  } else if (topic === 'inventory.low-stock') {
    // Broadcast low-stock alerts to manager + warehouse operators
    for (const recipient of lowStockRecipients()) {
      await NotificationService.createNotification(
        recipient,
        'LOW_STOCK_ALERT',
        'Low Stock Alert!',
        `Product ${payload.productId} in warehouse ${payload.warehouseId} has fallen below threshold (${payload.available} available).`
      );
    }
  }
}

/** 3 attempts with exponential backoff, then route the poison message to <topic>.dlq. */
async function handleWithRetry(topic: string, eventId: string, raw: string): Promise<void> {
  const maxAttempts = 3;
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await processEvent(topic, decodePayload(raw));
      return;
    } catch (err: any) {
      lastError = err;
      logger.warn(`Attempt ${attempt}/${maxAttempts} failed for event ${eventId} on ${topic}: ${err.message}`);
      if (attempt < maxAttempts) {
        await sleep(300 * Math.pow(2, attempt - 1));
      }
    }
  }

  const dlqTopic = `${topic}.dlq`;
  try {
    const dlqProducer = await getProducer();
    await dlqProducer.send({
      topic: dlqTopic,
      messages: [
        {
          key: eventId,
          value: raw,
          headers: {
            eventId,
            'original-topic': topic,
            'dlq-reason': lastError?.message ?? 'unknown',
            'dlq-timestamp': new Date().toISOString()
          }
        }
      ]
    });
    logger.error(`Event ${eventId} from ${topic} moved to ${dlqTopic} after ${maxAttempts} failed attempts`);
  } catch (dlqErr: any) {
    // DLQ publish failed: release the claim and rethrow so the offset is not committed
    // and the message is redelivered instead of being lost.
    await releaseClaim(eventId);
    throw dlqErr;
  }
}

export async function startKafkaConsumer(): Promise<void> {
  const maxAttempts = Number(process.env.KAFKA_CONSUMER_START_MAX_ATTEMPTS || 30);
  let delayMs = 1000;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      await consumer.connect();
      logger.info('Kafka consumer connected');

      for (const topic of TOPICS) {
        await consumer.subscribe({ topic, fromBeginning: false });
      }
      logger.info(`Subscribed to topics: ${TOPICS.join(', ')}`);

      await consumer.run({
        autoCommit: false,
        eachMessage: async ({ topic, partition, message }) => {
          if (!message.value) {
            await consumer.commitOffsets([{ topic, partition, offset: (Number(message.offset) + 1).toString() }]);
            return;
          }

          const raw = message.value.toString();
          const eventId = eventIdFor(raw, message.headers as Record<string, unknown> | undefined);

          const claimed = await claimEvent(eventId, topic);
          if (!claimed) {
            logger.info(`Duplicate event ${eventId} on ${topic} already processed - skipping`);
          } else {
            logger.info(`Processing event ${eventId} on ${topic}`);
            await handleWithRetry(topic, eventId, raw);
          }

          // Manual commit only after successful processing (or DLQ routing)
          await consumer.commitOffsets([{ topic, partition, offset: (Number(message.offset) + 1).toString() }]);
        }
      });

      logger.info('Kafka consumer group notification-service-group is running');
      return;
    } catch (err: any) {
      logger.warn(`Kafka consumer start attempt ${attempt}/${maxAttempts} failed: ${err.message}`);
      if (attempt === maxAttempts) {
        logger.error('Kafka consumer failed to start after all attempts. Restart the service once topics are available.');
        throw err;
      }
      await sleep(delayMs);
      delayMs = Math.min(delayMs * 2, 15000);
    }
  }
}
