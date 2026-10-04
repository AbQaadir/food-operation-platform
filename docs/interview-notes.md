# Technical Architecture Interview Notes

This document captures the engineering rationale, failure modes, scalability limits, and evolutionary roadmap for each core architectural decision in the **Enterprise Food Operations Platform**.

---

## 1. Database-per-Service & Microservices Domain Boundaries

### Why Chosen
- Prevents coupling at the data tier. Teams own and deploy their schemas independently without cross-domain database migrations.
- Allows polyglot persistence optimizations (e.g., GIN trigram indexes on product catalog, relational constraints on financial order records).
- Fault isolation: a high-load query or lock contention in `product_db` cannot exhaust the connection pool of `order_db` or prevent order placements.

### What Fails
- Distributed transactions (2PC) are deliberately excluded. Loss of ACID transactions across service boundaries requires eventual consistency and compensation logic.
- Complex reporting that previously relied on multi-table joins requires read-model projections or event aggregation.

### How It Scales
- Each database scales independently vertically or horizontally (e.g., read replicas on `product_db`).
- Independent connection pool sizing per service prevents database starvation.

### What Changes at 10× Traffic
- Introduce Citus / PostgreSQL horizontal sharding on `orders` keyed by `customer_id`.
- Transition the read-heavy catalog to Amazon Aurora PostgreSQL with multi-AZ read autoscaling pools.

---

## 2. Apache Kafka (KRaft Mode) as Event Backbone

### Why Chosen
- High-throughput, persistent, partitioned log capable of absorbing traffic spikes without dropping events.
- KRaft mode removes ZooKeeper operational overhead and eliminates metadata split-brain risks.
- Consumer groups allow independent services (`notification-service`, `analytics-service`, `inventory-service`) to consume at their own pace without competing for messages.

### What Fails
- Poison pill events (malformed JSON, schema mismatch). Handled via Dead Letter Queue (`.dlq`) routing and exponential backoff retry.
- Rebalance storms during consumer pod crashes. Mitigated by setting `session.timeout.ms=45000` and `heartbeat.interval.ms=15000`.

### How It Scales
- Partition count (default: 3 partitions per topic). Aggregate IDs (e.g., `orderId`) serve as partition keys, preserving strict sequential ordering per entity while distributing load across broker cores.

### What Changes at 10× Traffic
- Migrate from containerized Kafka to **Amazon MSK** (Managed Streaming for Apache Kafka) with 3 broker nodes across 3 Availability Zones.
- Increase topic partition count from 3 to 12.
- Implement Schema Registry (Confluent or AWS Glue) for contract enforcement and binary Avro/Protobuf compression.

---

## 3. Transactional Outbox Pattern & Saga Choreography

### Why Chosen
- Eliminates dual-write race conditions. Persisting the order aggregate and the outbox event row in a single atomic PostgreSQL transaction guarantees that if the order is saved, the event will eventually be emitted.
- Decouples user HTTP checkout latency from Kafka network availability.

### What Fails
- Polling overhead: a scheduled background poller querying `SELECT * FROM outbox_events WHERE published_at IS NULL` creates database lock contention under high load.
- Duplicate event publication if the publisher crashes between Kafka ack and database mark-as-published. Consumers must be strictly idempotent.

### How It Scales
- Bounded batch polling with `FOR UPDATE SKIP LOCKED` prevents concurrent workers from colliding.
- Partitioning outbox table by `created_at` or archiving processed events.

### What Changes at 10× Traffic
- Transition from poller-based outbox to **Change Data Capture (CDC)** using **Debezium** reading PostgreSQL write-ahead logs (WAL), achieving sub-millisecond event streaming with zero database query overhead.

---

## 4. Inventory Concurrency Control (Atomic Conditional Updates + Optimistic Locking)

### Why Chosen
- Under flash sale spikes, naive read-modify-write (`SELECT stock -> calculate in Java -> UPDATE stock`) causes catastrophic overselling.
- Pessimistic table locks (`LOCK TABLE`) throttle throughput across the entire warehouse.
- Atomic conditional update:
  ```sql
  UPDATE stock_levels 
  SET reserved = reserved + :qty, version = version + 1 
  WHERE id = :id AND (on_hand - reserved) >= :qty;
  ```
  PostgreSQL evaluates this predicate under a row-exclusive lock. If stock is depleted, `updatedRows == 0`, immediately signaling exhaustion without deadlocks.

### What Fails
- Extreme contention on a single SKU causes high retry rates for optimistic locking.
- Database constraint `CHECK (on_hand - reserved >= 0)` is the physical safety net; any attempt to bypass logic throws a database constraint violation.

### How It Scales
- Stock is segmented by warehouse ID. Reservations are distributed across regional hubs, reducing hot-spot contention on a single row.

### What Changes at 10× Traffic
- Implement Redis distributed inventory decrement using atomic Lua scripts (`EVAL`) for pre-allocation, synchronizing asynchronously back to PostgreSQL in batches.

---

## 5. Redis for Multi-Tier Caching, Idempotency, and Rate Limiting

### Why Chosen
- Sub-millisecond read latency for hot catalog items.
- Token-bucket rate limiting at API Gateway protects backend microservices from DDoS and brute force.
- Fast idempotency cache prevents duplicate order processing when clients retry timed-out requests.

### What Fails
- Cache stampede / thundering herd when popular product keys expire. Handled via staggered TTLs and mutex locks.
- Redis node crash. Backend services fall back to database constraints (e.g., `idempotency_records` table) gracefully.

### How It Scales
- Redis cluster mode with key hash slots.
- Dedicated cache instances for caching vs transient rate limiting tokens.

### What Changes at 10× Traffic
- Transition from single-node Redis to **Amazon ElastiCache Redis Cluster** with cluster sharding and read replicas in each Availability Zone.

---

## 6. AI Operations Assistant (Tool-Calling via REST)

### Why Chosen
- Operational supervisors require real-time natural language queries without writing SQL.
- Safety: AI has zero direct database credentials. It can only call read-only REST APIs through the API Gateway, inheriting the caller's JWT role permissions.
- Streaming: SSE allows instant feedback (tool call badges, data previews, and typewriter tokens) rather than waiting 5-10s for complete model response.

### What Fails
- LLM hallucination or schema violation in tool calling. Addressed via strict Pydantic parameter schemas and validation guards.
- Tool latency: if a downstream microservice is slow, assistant timeout is capped at 30 seconds.

### How It Scales
- Stateless FastAPI application scales horizontally across ECS Fargate tasks behind the ALB.
- Provider abstraction allows dynamic fallback between Gemini, OpenAI, Anthropic, or local vLLM models.

### What Changes at 10× Traffic
- Add semantic response caching in Redis using vector embeddings to answer frequent repetitive queries (e.g., "what is the price of SKU-100") in < 5ms without invoking the LLM provider.

---

## 7. Cloud Deployment: AWS ECS Fargate vs EKS Kubernetes

### Why Chosen
- **ECS Fargate:** Chosen as primary AWS deployment target for maximum operational efficiency, zero server patching, per-second billing, and native IAM/CloudWatch integration without Kubernetes control plane costs (\$72/month/cluster minimum on EKS).
- **Kubernetes Manifests (`infrastructure/k8s/`):** Maintained alongside Terraform as declarative Kustomize configs to support enterprise clients running on EKS, GKE, or hybrid clouds.

### What Fails
- Fargate task cold start time (30-60s) during rapid auto-scaling spikes compared to pre-provisioned EC2 instances.
- Mitigated by target tracking auto-scaling based on CPU utilization (70%) and ALB request count.

### What Changes at 10× Traffic
- Transition high-traffic microservices (`api-gateway`, `product-service`, `order-service`) to EC2-backed ECS or EKS with Bottlerocket OS and Karpenter node autoscaling for cost efficiency at scale.
