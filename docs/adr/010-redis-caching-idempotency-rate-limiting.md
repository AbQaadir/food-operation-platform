# ADR 010: Redis Strategy for Caching, Distributed Idempotency, and Rate Limiting

## Status
Accepted

## Context
In a distributed food operations platform, high-volume transactions and search queries place intense load on relational databases and edge routing infrastructure. Three distinct cross-cutting concerns require distributed, in-memory state:
1. **Catalog Read Performance:** High-frequency product queries (`GET /api/v1/products/{id}`) must achieve sub-5ms response times.
2. **Order Idempotency:** Duplicate checkout submissions resulting from network timeouts or aggressive user clicks must be deduplicated across distributed order service instances within milliseconds.
3. **Edge Rate Limiting:** The API Gateway must protect downstream microservices from denial-of-service and brute force without adding latency.

## Decision
We adopted **Redis 7** as the unified distributed in-memory data store across three distinct architectural tiers:

### 1. Read-Through Product Caching (`product-service`)
- `GET /api/v1/products/{id}` caches serialized product DTOs in Redis using a 10-minute TTL (`product:cache:{id}`).
- Cache eviction is triggered on update (`PUT`) or deletion (`DELETE`) via Spring Cache annotations (`@CacheEvict`).
- Eliminates repeated relational queries on steady-state catalog reads.

### 2. Distributed Idempotency Key Validation (`order-service`)
- Clients submit an `Idempotency-Key` header with `POST /api/v1/orders`.
- The order service checks Redis with an atomic `SETNX` operation (`idempotency:order:{key}`) with a 24-hour TTL.
- If the key exists, the cached order ID and status are returned immediately (HTTP 200/201).
- If the key is new, the order is created, and the key is committed.
- A PostgreSQL fallback table (`idempotency_records`) with a unique database constraint ensures absolute durability if Redis restarts.

### 3. Token-Bucket Rate Limiter (`api-gateway`)
- Spring Cloud Gateway utilizes Redis Reactive Rate Limiter using a token-bucket algorithm.
- Evaluated per client IP address and authenticated user principal (`X-User-Id`).
- Prevents cascade failures and throttles malicious bursts with HTTP 429 Too Many Requests (RFC 7807 problem detail).

### 4. Real-time Unread Notification Counter (`notification-service`)
- Redis atomic increments (`INCR unread:user:{userId}`) maintain live notification badge counts for instant retrieval without querying PostgreSQL.

## Consequences
- **Positive:**
  - Gateway request processing P95 latency is sub-15ms.
  - Complete protection against duplicate order placement.
  - Low relational database CPU consumption on catalog reads.
- **Negative:**
  - Introduces Redis as a high-availability dependency in cloud deployments (mitigated via AWS ElastiCache Redis multi-AZ replication).
