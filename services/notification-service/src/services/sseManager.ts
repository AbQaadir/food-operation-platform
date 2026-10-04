import { Response } from 'express';
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

    const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
    userClients.forEach((res) => {
      try {
        res.write(payload);
      } catch (err: any) {
        logger.warn(`Failed to write SSE to client: ${err.message}`);
      }
    });
  }

  broadcast(event: string, data: any) {
    const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
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
