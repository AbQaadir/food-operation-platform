# ADR-004: Transactional Outbox Pattern and Saga Choreography

## Status
Accepted

## Context
In a distributed microservices environment with independent databases per service, dual-writing (writing to a database and publishing an event to Apache Kafka in the same HTTP request) is prone to partial failures:
- If the database write succeeds but Kafka broker is down or unreachable, the event is permanently lost, causing inconsistent downstream state (e.g. inventory never reserved for a created order).
- If the Kafka event is sent first but the database transaction subsequently fails or rolls back, downstream services process phantom events.

Distributed 2-phase commit (XA transactions) is notoriously brittle, slow, and not supported natively by Apache Kafka.

## Decision
We adopted the **Transactional Outbox Pattern** paired with **Event Choreography**:

1. **Transactional Outbox:**
   - Both the business aggregate (`orders`) and the event record (`outbox_events`) are persisted within the exact same ACID database transaction in PostgreSQL.
   - An asynchronous scheduled background publisher (`OutboxPublisher`) periodically queries unprocessed events (`processed_at IS NULL`) in FIFO order, publishes them to Kafka with the aggregate ID as the partition key, and atomically marks them processed.
   - On transient broker errors, the publisher increments `retry_count` and retries on subsequent polls, guaranteeing **at-least-once delivery**.

2. **Event Choreography (Saga):**
   - **Happy Path:**
     1. Order Service creates order (`PENDING`) -> writes `order.created` to outbox.
     2. Inventory Service consumes `order.created` -> atomically reserves stock -> publishes `inventory.reserved`.
     3. Order Service consumes `inventory.reserved` -> transitions order to `CONFIRMED`.
   - **Compensating Path (Insufficient Stock):**
     1. Inventory Service fails reservation -> publishes `inventory.rejected`.
     2. Order Service consumes `inventory.rejected` -> transitions order to `CANCELLED` (with reason `INSUFFICIENT_STOCK`).
   - **Compensating Path (User Cancellation):**
     1. User cancels order -> Order Service marks `CANCELLED` -> writes `order.cancelled` to outbox.
     2. Inventory Service consumes `order.cancelled` -> executes `releaseStockConditional` -> restores available capacity.

3. **Idempotency:**
   - `Idempotency-Key` HTTP header cached in Redis (TTL 24h) with database fallback (`idempotency_records`).
   - Identical incoming requests short-circuit and immediately return the original HTTP status code and response payload.

4. **Schema Contracts:**
   - Every Kafka event adheres to a strict JSON Schema stored under `contracts/events/` validated in integration test suites.

## Consequences
- **Positive:**
  - Zero risk of lost events or inconsistent distributed state.
  - High availability: order service accepts orders even if Kafka broker is temporarily restarting.
  - Full audit trail of all published domain events.
- **Negative:**
  - Slight latency delay (~500ms) between database commit and Kafka emission due to outbox polling interval.
