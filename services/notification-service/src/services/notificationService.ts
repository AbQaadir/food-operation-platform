import { v4 as uuidv4 } from 'uuid';
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
