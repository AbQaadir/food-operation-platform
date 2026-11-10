# AGENTS.md — Food Operations Platform Guide for AI Coding Agents

> **Audience**: AI Coding Agents (Antigravity, Claude Code, Cursor, GitHub Copilot, OpenAI Codex, Windsurf, Aider, Devin).  
> **Mission**: Guide automated agents through setup, development, architectural invariants, code style, and verification without context bloat or regressions.

---

## 1. Quick Reference & Golden Commands

Always run commands from the repository root:

```bash
# Platform Orchestration
make up                 # Start entire platform (13 containers) via Docker Compose
make down               # Stop all containers and remove volumes
make seed               # Seed 5,200 products, 10 categories, 4 warehouses, and stock allocations

# Golden Verification & Testing (Run before marking any task complete!)
python3 scripts/run_production_tests.py   # Automated 28-test functional & concurrency harness
cd tests/e2e && npx playwright test       # Playwright browser end-to-end user journeys
k6 run tests/load/catalog-search-load.js   # Catalog search load benchmark (p95 < 50ms)
k6 run tests/load/order-checkout-load.js   # Order checkout concurrency benchmark (p95 < 300ms)

# Service-Specific Unit / Integration Tests
make test                                 # Run tests across all services
cd frontend && npm run test               # Vitest component & store tests
cd frontend && npm run lint               # TypeScript type checking
```

---

## 2. Platform Architecture & Service Matrix

The platform is an **event-driven polyglot microservices system**. No two services share a database.

| Service | Directory | Tech Stack | Port | DB / Storage | Primary Role |
|---|---|---|---|---|---|
| **API Gateway** | `services/api-gateway` | Spring Cloud Gateway, Java 21 | `8080` | Redis (Route/RateLimit) | Unified ingress, JWT auth filter, correlation ID injection |
| **Identity Service** | `services/identity-service` | Spring Boot 3, Java 21 | `8081` | `identity_db` (Postgres) | User authentication, BCrypt hashing, JWT issuance |
| **Product Service** | `services/product-service` | Spring Boot 3, Java 21 | `8082` | `product_db` (Postgres) + Redis | 5,000+ catalog, pg_trgm fuzzy search, cache-aside |
| **Inventory Service** | `services/inventory-service` | Spring Boot 3, Java 21 | `8083` | `inventory_db` (Postgres) | Multi-warehouse stock, atomic conditional updates |
| **Order Service** | `services/order-service` | Spring Boot 3, Java 21 | `8084` | `order_db` (Postgres) + Redis | Transactional Outbox, Saga Choreography, Idempotency |
| **Notification Service** | `services/notification-service` | Node.js 22 LTS, TypeScript | `8085` | Redis (unread counts) | KafkaJS consumer, Server-Sent Events (SSE) streaming |
| **Analytics Service** | `services/analytics-service` | Node.js 22 LTS, TypeScript | `8086` | `analytics_db` (Postgres) | Real-time stream aggregation of sales & throughput KPIs |
| **AI Assistant** | `services/ai-service` | Python 3.12, FastAPI | `8087` | Mock LLM / LangChain | Tool-calling agent (inventory, catalog queries) + SSE |
| **Frontend** | `frontend` | React 18, Vite, Tailwind CSS | `5173` | Nginx (Docker) | Operations Control Center UI & real-time SSE listener |
| **Kafka KRaft** | `infrastructure/docker/kafka` | Apache Kafka 3.7.0 KRaft | `9092` | KRaft metadata | Event backbone (3 partitions per topic + DLQs) |
| **PostgreSQL** | `infrastructure/docker/postgres` | PostgreSQL 16 Alpine | `5432` | Volume mount | 5 isolated logical databases |
| **Redis** | In compose | Redis 7 Alpine | `6379` | Volume mount | Caching, idempotency store, notification badges |
| **Observability** | `infrastructure/docker/` | Prometheus, Grafana, OTel | `9090`, `3000`, `8089` | Scrapers & Dashboards | RED metrics, traces, Kafka UI cluster manager |

---

## 3. Critical Architectural Invariants (Must Respect)

### A. Database Isolation (Never Cross-Query)
* Each microservice owns its own database schema (`identity_db`, `product_db`, `inventory_db`, `order_db`, `analytics_db`).
* **NEVER** write cross-database SQL joins or queries from one service into another service's database. Cross-service data is exchanged solely via **Apache Kafka events** or **API Gateway REST endpoints**.

### B. Concurrency Control & Overselling Prevention
* Inventory reservation uses **atomic conditional SQL updates** to prevent overselling:
  ```sql
  UPDATE stock_levels 
  SET reserved = reserved + :qty, version = version + 1, updated_at = NOW()
  WHERE warehouse_id = :warehouseId 
    AND product_id = :productId 
    AND (on_hand - reserved) >= :qty;
  ```
* **NEVER** read stock into application memory, calculate in Java/Python, and write back without conditional SQL or optimistic locking. If modifying inventory logic, always run `InventoryConcurrencyTest.java` (50 threads).

### C. Transactional Outbox & Saga Choreography
* When an order is created, the order row and an `outbox_events` record are saved in the **same database transaction**.
* The scheduled `OutboxPublisher` polls unpublished outbox records and publishes to Kafka topic `order.created`.
* **Kafka Choreography Flow**:
  1. `order-service` writes `order.created` via Outbox.
  2. `inventory-service` consumes `order.created`, attempts stock reservation.
  3. If stock succeeds: publishes `inventory.reserved` $\rightarrow$ `order-service` transitions order to `CONFIRMED`.
  4. If stock fails: publishes `inventory.rejected` $\rightarrow$ `order-service` transitions order to `REJECTED`.
  5. `notification-service` consumes all events and pushes real-time SSE alerts to the browser.
  6. `analytics-service` consumes all events and updates hourly revenue aggregates.

### D. Distributed Idempotency (RFC 7807 Problem Details)
* `POST /api/v1/orders` **strictly requires** an `Idempotency-Key` HTTP header. Missing header must return HTTP 400 with RFC 7807 `application/problem+json`.
* Replaying the exact same request with the same `Idempotency-Key` must return the previously cached order without double-charging or double-reserving.

---

## 4. Boundaries & Guardrails (What NOT To Do)

- **NEVER** commit `.env` or hardcode secrets, passwords, or tokens in source code.
- **NEVER** change database schemas without adding a corresponding SQL migration file (`src/main/resources/db/migration/V{N}__*.sql`).
- **NEVER** use `any` type in TypeScript (`services/notification-service`, `services/analytics-service`, `frontend`). Strict type-checking is enforced.
- **NEVER** bypass API Gateway authentication or remove `X-Correlation-Id` header propagation.
- **NEVER** push unverified code to `main` without running `python3 scripts/run_production_tests.py`.

---

## 5. Development & Agent Workflow

1. **Understand First**: Check `docs/adr/` (Architecture Decision Records) and `contracts/events/` (JSON schemas) before designing changes.
2. **Make Minimal, Targeted Edits**: Match existing naming conventions, formatting, and file structures.
3. **Run Golden Tests**: Execute `python3 scripts/run_production_tests.py` to verify health, auth, catalog, inventory concurrency, order saga, SSE, analytics, and AI endpoints.
4. **Format Commits**: Use Conventional Commits (`feat(...)`, `fix(...)`, `test(...)`, `perf(...)`, `docs(...)`).
