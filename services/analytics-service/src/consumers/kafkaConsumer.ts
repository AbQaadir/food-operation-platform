import { Kafka, Consumer } from 'kafkajs';
import { logger } from '../config/logger.js';
import { analyticsService } from '../services/analyticsService.js';
import { v4 as uuidv4 } from 'uuid';

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

export async function startKafkaConsumer() {
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

          const payload = JSON.parse(valueStr);
          const eventId = (message.headers?.['correlation-id']?.toString() || payload.id || uuidv4()) as string;

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
  } catch (err: any) {
    logger.error({ err }, 'Failed to start Kafka consumer for analytics-service');
  }
}
