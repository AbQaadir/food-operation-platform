import { Kafka } from 'kafkajs';
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
