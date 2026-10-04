# Enterprise Food Operations Platform — Operations Runbook

This runbook provides complete operational guidance for building, running, testing, monitoring, and deploying the Enterprise Food Operations Platform.

---

## 1. System Topology & Port Matrix

| Component | Language / Framework | Port | Persistence / Role | Health / Readiness |
|---|---|---|---|---|
| **API Gateway** | Java 21 / Spring Cloud Gateway | `8080` | Routing, JWT validation, Correlation ID | `/actuator/health` |
| **Identity Service** | Java 21 / Spring Boot 3 | `8081` | `identity_db` (PostgreSQL), BCrypt, JWT | `/actuator/health` |
| **Product Service** | Java 21 / Spring Boot 3 | `8082` | `product_db` (PostgreSQL), Redis Cache | `/actuator/health` |
| **Inventory Service** | Java 21 / Spring Boot 3 | `8083` | `inventory_db` (PostgreSQL), Optimistic lock | `/actuator/health` |
| **Order Service** | Java 21 / Spring Boot 3 | `8084` | `order_db` (PostgreSQL), Outbox, Idempotency | `/actuator/health` |
| **Notification Service** | Node.js 22 LTS / Express / TS | `8085` | `notification_db`, Redis counter, SSE | `/health`, `/ready` |
| **AI Operations Assistant** | Python 3.12 / FastAPI | `8087` | Read-only tool calling, SSE streaming | `/health` |
| **Operations Frontend** | React 18 / Vite / TypeScript | `5173` | Executive dashboard & operations UI | `/` |
| **PostgreSQL 16** | Database-per-service | `5432` | 6 isolated domain databases | `pg_isready` |
| **Redis 7** | In-memory cache & idempotency | `6379` | Sub-millisecond cache & lock store | `redis-cli ping` |
| **Apache Kafka (KRaft)** | Event streaming backbone | `9092` / `29092` | 9 event topics + DLQ, no ZooKeeper | broker-api-versions |
| **Kafka UI** | Web management console | `8089` | Topic, partition, and message browser | Web UI |
| **Prometheus** | Metrics aggregation | `9090` | Scrapes all microservices (15s interval) | `/api/v1/targets` |
| **Grafana** | Dashboards & alerting | `3000` | Pre-provisioned executive dashboard | `http://localhost:3000` |
| **OTel Collector** | OpenTelemetry Contrib | `4317` / `4318` | Distributed tracing (gRPC/HTTP) | Health check |

---

## 2. Quick Start (From a Clean Clone)

### Prerequisites
- Docker Engine & Docker Compose v2+
- Make (optional, all commands wrapped in `Makefile`)
- Java 21 (Temurin recommended) & Maven 3.9+
- Node.js 22 LTS & npm 10+
- Python 3.12

### Starting the Platform
```bash
# Start all 15 infrastructure and microservice containers
make up

# Seed 5,200+ products across 10 categories for scale testing
make seed
```

### Accessing Interfaces
- **Operations Dashboard:** [http://localhost:5173](http://localhost:5173)
- **API Gateway:** [http://localhost:8080](http://localhost:8080)
- **Grafana (admin / admin):** [http://localhost:3000](http://localhost:3000)
- **Prometheus:** [http://localhost:9090](http://localhost:9090)
- **Kafka UI:** [http://localhost:8089](http://localhost:8089)

---

## 3. Test Suites & Verification

### Running All Unit & Integration Tests
```bash
make test
```
Executes:
- Spring Boot Testcontainers & Mockito across `api-gateway`, `identity-service`, `product-service`, `inventory-service`, `order-service`.
- Vitest integration tests for `notification-service`.
- Vitest React Testing Library tests for `frontend`.
- Pytest TestClient tests for `ai-service`.

### End-to-End Playwright Tests
```bash
make e2e
```
Validates:
- Complete user journey in Chromium (Dashboard, Product Search, Inventory Inspection, Order Checkout with Idempotency-Key, AI Assistant).
- API Gateway routing, header propagation, idempotency deduplication, and SSE streaming.

### Performance & SLO Load Tests (k6)
```bash
make load
```
Verifies:
- **Product Catalog Search SLO:** P95 latency < 50ms at up to 500 req/s.
- **Concurrent Order Checkout SLO:** P95 latency < 300ms with client-side Idempotency-Key.

---

## 4. Operational Runbook & Troubleshooting

### Scenario A: Order Reservation Fails or Rejection Occurs
1. **Inspect Order Status:**
   ```bash
   curl -s -H "Authorization: Bearer <token>" http://localhost:8080/api/v1/orders/<orderId>
   ```
2. **Check Outbox Table:**
   ```bash
   docker exec -it food-platform-postgres psql -U postgres -d order_db -c "SELECT id, event_type, status, created_at FROM outbox_events ORDER BY created_at DESC LIMIT 10;"
   ```
3. **Inspect Kafka Dead Letter Queue (DLQ):**
   Navigate to Kafka UI at [http://localhost:8089](http://localhost:8089) and inspect topic `order.events.DLQ`.

### Scenario B: Clearing Redis Product Cache
When diagnosing cache invalidation:
```bash
# Connect to Redis
docker exec -it food-platform-redis redis-cli

# Inspect product cache keys
KEYS product:*

# Invalidate specific product or flush DB
DEL "product:a68d0d41-c837-4da4-8c66-e64f5ea6e761"
```

### Scenario C: High Database Concurrency & Lock Retries
1. View Grafana Dashboard: [http://localhost:3000/d/food-ops-overview](http://localhost:3000/d/food-ops-overview)
2. Inspect `inventory_db` stock levels and versions:
   ```bash
   docker exec -it food-platform-postgres psql -U postgres -d inventory_db -c "SELECT warehouse_id, product_id, on_hand, reserved, (on_hand - reserved) as available, version FROM stock_levels;"
   ```

---

## 5. AWS Cloud Deployment (Terraform)

### Planning Infrastructure (Dev / Prod)
```bash
# Dry-run plan for Dev environment
make tf-plan

# Apply to AWS (requires active AWS CLI credentials)
cd infrastructure/terraform/environments/dev
terraform init
terraform apply
```

### Production Topology Differences
- Multi-AZ RDS PostgreSQL with automatic failover.
- Amazon MSK cluster with 3 partitions and `min.insync.replicas=2`.
- ElastiCache Redis multi-node replication group with auto-failover.
- Multi-AZ Application Load Balancer with HTTPS termination.
