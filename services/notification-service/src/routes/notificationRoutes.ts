import { Router, Request, Response, NextFunction } from 'express';
import { NotificationService } from '../services/notificationService.js';
import { sseManager } from '../services/sseManager.js';
import { z } from 'zod';

export const router = Router();

const DEFAULT_USER_ID = '5fc0741f-9724-4446-8dcb-c7fac24a4c80'; // fallback admin/customer

function getUserId(req: Request): string {
  const headerId = req.headers['x-user-id'] as string;
  return headerId || DEFAULT_USER_ID;
}

// GET /api/v1/notifications (supports ?unread=true & pagination)
router.get('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const userId = getUserId(req);
    const page = parseInt(req.query.page as string || '0', 10);
    const size = parseInt(req.query.size as string || '20', 10);
    const unreadOnly = req.query.unread === 'true';
    const result = await NotificationService.getNotifications(userId, page, size, unreadOnly);
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

// Mark single notification as read: supports both POST /:id/read and PATCH /:id/read
const markReadHandler = async (req: Request, res: Response, next: NextFunction) => {
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
};

router.post('/:id/read', markReadHandler);
router.patch('/:id/read', markReadHandler);

// Mark all notifications as read: supports POST /read-all and POST /mark-read
const markAllReadHandler = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const userId = getUserId(req);
    const count = await NotificationService.markAllAsRead(userId);
    res.json({ message: 'All notifications marked as read', updatedCount: count });
  } catch (err) {
    next(err);
  }
};

router.post('/read-all', markAllReadHandler);
router.post('/mark-read', markAllReadHandler);

// GET /api/v1/notifications/stream (Server-Sent Events)
router.get('/stream', (req: Request, res: Response) => {
  const userId = getUserId(req);

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');
  res.flushHeaders();

  // Send initial connected event
  res.write(`event: connected\ndata: ${JSON.stringify({ status: 'connected', userId })}\n\n`);

  // Heartbeat ping every 15s to keep proxy connections alive
  const heartbeat = setInterval(() => {
    res.write(': heartbeat\n\n');
  }, 15000);

  res.on('close', () => {
    clearInterval(heartbeat);
  });

  sseManager.addClient(userId, res);
});
