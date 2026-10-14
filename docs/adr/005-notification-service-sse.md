# ADR-005: Notification Service with Node.js, Express, and Server-Sent Events (SSE)

## Status
Accepted

## Context
Downstream consumers and frontend clients require real-time updates when orders are confirmed, cancelled, or when inventory reaches low-stock thresholds. The platform specification mandates that the notification service be built with Node.js 22 LTS, Express, and TypeScript, interfacing with Apache Kafka (KafkaJS), PostgreSQL (`notification_db`), and Redis.

For real-time delivery to the browser, we evaluated WebSockets vs Server-Sent Events (SSE):
- Notifications in our platform are unidirectional (server-to-client).
- SSE operates over standard HTTP/1.1 or HTTP/2, requires no custom protocol upgrades through the Spring Cloud Gateway, natively handles browser reconnection with automatic retry, and easily traverses enterprise firewalls.

## Decision
We implemented `notification-service` using Node.js 22 LTS with:
1. **KafkaJS Consumer:** Subscribes to `order.confirmed`, `order.cancelled`, and `inventory.low-stock`.
2. **PostgreSQL Persistence:** Stores notification records in `notification_db` with user-scoped pagination and indexes.
3. **Redis Unread Count:** Maintains fast atomic counters (`unread:user:{userId}`) using Redis `INCR` on arrival and `DECR` on acknowledgment.
4. **Server-Sent Events (SSE):** `GET /api/v1/notifications/stream` streams events using standard `text/event-stream` encoding with periodic heartbeats every 15s to maintain persistent HTTP connections across gateways and proxies.

## Consequences
- **Positive:**
  - Lightweight and highly concurrent I/O suited for massive SSE connections.
  - Zero custom gateway WebSocket configuration needed; works seamlessly over standard HTTP routes.
  - Automatic reconnection handled natively by browser EventSource.
- **Negative:**
  - Unidirectional only (client acknowledgments are sent via standard REST PATCH requests, which is standard and RESTful).
