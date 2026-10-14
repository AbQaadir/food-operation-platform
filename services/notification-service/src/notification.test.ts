import { describe, it, expect, vi } from 'vitest';
import express from 'express';
import request from 'supertest';
import { router as notificationRouter } from './routes/notificationRoutes.js';
import { NotificationService } from './services/notificationService.js';
import { decodePayload } from './consumers/kafkaConsumer.js';

describe('Notification Service Tests', () => {
  const app = express();
  app.use(express.json());
  app.use('/api/v1/notifications', notificationRouter);

  it('GET /api/v1/notifications/unread-count returns unread count', async () => {
    vi.spyOn(NotificationService, 'getUnreadCount').mockResolvedValue(3);

    const res = await request(app)
      .get('/api/v1/notifications/unread-count')
      .set('x-user-id', '5fc0741f-9724-4446-8dcb-c7fac24a4c80');

    expect(res.status).toBe(200);
    expect(res.body).toEqual({
      userId: '5fc0741f-9724-4446-8dcb-c7fac24a4c80',
      unreadCount: 3
    });
  });

  it('GET /api/v1/notifications returns paginated notification list', async () => {
    vi.spyOn(NotificationService, 'getNotifications').mockResolvedValue({
      content: [
        {
          id: '11111111-1111-1111-1111-111111111111',
          userId: '5fc0741f-9724-4446-8dcb-c7fac24a4c80',
          type: 'ORDER_CONFIRMED',
          title: 'Order Confirmed!',
          body: 'Your order #123 has been confirmed.',
          read: false,
          createdAt: new Date().toISOString()
        }
      ],
      page: 0,
      size: 20,
      totalElements: 1,
      totalPages: 1
    });

    const res = await request(app)
      .get('/api/v1/notifications')
      .set('x-user-id', '5fc0741f-9724-4446-8dcb-c7fac24a4c80');

    expect(res.status).toBe(200);
    expect(res.body.content.length).toBe(1);
    expect(res.body.content[0].type).toBe('ORDER_CONFIRMED');
  });

  it('PATCH /api/v1/notifications/:id/read marks notification as read', async () => {
    vi.spyOn(NotificationService, 'markAsRead').mockResolvedValue(true);

    const res = await request(app)
      .patch('/api/v1/notifications/11111111-1111-1111-1111-111111111111/read')
      .set('x-user-id', '5fc0741f-9724-4446-8dcb-c7fac24a4c80');

    expect(res.status).toBe(200);
    expect(res.body.read).toBe(true);
  });

  it('decodePayload handles double-encoded Kafka record values (spring-kafka JsonSerializer of a JSON string)', () => {
    const payload = { eventId: 'evt-1', orderId: 'ord-1', customerId: 'cust-1', status: 'CONFIRMED' };
    const doubleEncoded = JSON.stringify(JSON.stringify(payload));
    expect(decodePayload(doubleEncoded)).toEqual(payload);
  });

  it('decodePayload handles single-encoded Kafka record values', () => {
    const payload = { eventId: 'evt-2', orderId: 'ord-2', customerId: 'cust-2', status: 'CONFIRMED' };
    expect(decodePayload(JSON.stringify(payload))).toEqual(payload);
  });
});
