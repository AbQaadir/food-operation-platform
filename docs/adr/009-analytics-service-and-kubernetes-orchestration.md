# ADR 009: Real-time Analytics Event Aggregation & Kubernetes Orchestration

## Status
Accepted

## Context
As the Enterprise Food Operations Platform scales across multiple fulfillment centers and customer regions, operational stakeholders require:
1. Low-latency, high-level business metrics (daily order count, gross merchandise value / revenue, order cancellation rates, low-stock triggers) without running expensive, read-heavy analytical queries against the operational transaction databases (`order_db`, `inventory_db`).
2. Declarative, cloud-agnostic Kubernetes manifests (`infrastructure/k8s/`) to support hybrid cloud, on-premises, and managed Kubernetes environments (EKS, GKE) alongside our AWS ECS Fargate deployment topology.
3. Strict isolation of analytical compute and storage from OLTP workloads.

## Decision
1. **Dedicated Analytics Microservice (`analytics-service`):**
   - Built on Node.js 22 LTS, Express, TypeScript, KafkaJS, and PostgreSQL 16 (`analytics_db`).
   - Listens on port 8086 and routes through API Gateway at `/api/v1/analytics/**`.
   - Idempotently consumes Apache Kafka KRaft events:
     - `order.created`: Increments total orders, adds gross order revenue to daily KPIs and hourly buckets.
     - `order.cancelled`: Increments cancelled order counter in real-time.
     - `inventory.low-stock`: Increments low stock alert counter.
   - Enforces event deduplication via dedicated `processed_events` table indexed by event ID / correlation ID.

2. **Database-per-Service Isolation (`analytics_db`):**
   - The service maintains its own relational schema (`daily_kpis`, `hourly_order_stats`, `processed_events`).
   - Zero synchronous cross-database queries or foreign keys to `order_db` or `inventory_db`.

3. **Kubernetes Deployment Architecture (`infrastructure/k8s/`):**
   - Fully declarative Kustomize configuration (`kustomization.yaml`).
   - Multi-pod deployments with resource requests/limits, Horizontal Pod Autoscalers (HPA), HTTP readiness/liveness probes (`/health`, `/ready`), and shared ConfigMaps/Secrets.
   - AWS Application Load Balancer (ALB) Ingress controller annotations with SSL redirection and path-based routing.

## Consequences
- **Positive:**
  - OLTP order and inventory databases are completely shielded from analytical aggregation load.
  - Zero latency impact on customer checkout flows.
  - Kubernetes manifests provide instant portability for multi-cloud and enterprise Kubernetes environments.
- **Negative:**
  - Eventual consistency: analytical KPIs lag the exact moment of order placement by the Kafka consumer roundtrip (~5-20ms).
