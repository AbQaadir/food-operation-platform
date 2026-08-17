# ADR 002: Apache Kafka as Asynchronous Event Backbone

## Status
Accepted

## Context
The platform requires asynchronous coordination across services for order fulfillment choreography, customer notifications, analytical KPI projection, and auditing. Synchronous REST calls introduce high latency, tight coupling, and cascading failures.

## Decision
We adopt **Apache Kafka** (running in KRaft mode) as the platform's asynchronous messaging backbone.
1. **Partitioning Key:** Aggregate root IDs (e.g. `orderId`) guarantee strict causal ordering.
2. **Transactional Outbox:** Producers write events atomically into a local `outbox_events` table before dispatching to Kafka.
3. **Consumer Idempotency:** Consumers persist processed `eventId` keys.
4. **Dead Letter Queues (DLQ):** Failed messages retry with backoff then route to `<topic>.dlq`.
5. **Schema Contracts:** All events conform strictly to JSON Schema definitions in `contracts/events/`.

## Consequences
### Positive
- High-throughput append-only log durability.
- Decoupled event publication allowing new consumers without producer modification.
- Zero ZooKeeper overhead via modern KRaft metadata consensus.
### Negative & Trade-offs
- Eventual consistency requires UI to support pending states.
- Consumer group offsets and lag must be continuously monitored via Prometheus/Grafana.
