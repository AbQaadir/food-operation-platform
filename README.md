# Enterprise Food Operations Platform

> **A production-grade, event-driven microservices platform for modern food service operations, multi-warehouse inventory management, transactional order processing, real-time alerts, and AI-assisted operational intelligence.**

[![CI Pipeline](https://img.shields.io/badge/CI%20Pipeline-Passing-brightgreen.svg)]()
[![Java 21](https://img.shields.io/badge/Java-21-orange.svg)](https://openjdk.org/projects/jdk/21/)
[![Spring Boot 3.3](https://img.shields.io/badge/Spring%20Boot-3.3.4-brightgreen.svg)](https://spring.io/projects/spring-boot)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-KRaft-black.svg)](https://kafka.apache.org/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Redis 7](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python%203.12-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed.svg)](https://www.docker.com/)

---

## Operations Control Center (Live UI)

![Operations Control Center](docs/architecture/dashboard-full.png)

---

## 1. System Architecture & Topology

The platform adheres to strict domain-driven boundaries and the **Database-per-Service** pattern. Synchronous traffic is handled via **Spring Cloud Gateway** with JWT authentication and Redis rate limiting. Asynchronous cross-service communication flows through **Apache Kafka (KRaft mode)** utilizing the **Transactional Outbox Pattern** to ensure data consistency without distributed 2PC locks.

```mermaid
flowchart TD
    subgraph Clients["Frontend Tier"]
        Browser["React 18 SPA (Vite / TS :5173)\nRedux Toolkit / TanStack Query"]
    end

    subgraph EdgeTier["Edge & Gateway Tier"]
        Gateway["API Gateway (:8080)\nSpring Cloud Gateway (Java 21)\nJWT Filter / Redis Token-Bucket / CORS"]
    end

    subgraph CoreServices["Domain Microservices"]
        Identity["identity-service (:8081)\nSpring Boot 3 / BCrypt / JWT / RBAC"]
        Product["product-service (:8082)\nSpring Boot 3 / Trigram GIN / Redis Cache"]
        Inventory["inventory-service (:8083)\nSpring Boot 3 / Optimistic Locking"]
        Order["order-service (:8084)\nSpring Boot 3 / Transactional Outbox / Idempotency"]
        Notification["notification-service (:8085)\nNode.js 22 LTS / Express / SSE Stream"]
        Analytics["analytics-service (:8086)\nNode.js 22 LTS / Event Projections / KPIs"]
        AI["ai-service (:8087)\nPython 3.12 / FastAPI / Tool-Calling Agent"]
    end

    subgraph DataStorage["Data & State Isolation (Zero Shared DBs)"]
        DB_ID[(identity_db\nPostgreSQL 16)]
        DB_PROD[(product_db\nPostgreSQL 16)]
        DB_INV[(inventory_db\nPostgreSQL 16)]
        DB_ORD[(order_db\nPostgreSQL 16)]
        DB_NOTIF[(notification_db\nPostgreSQL 16)]
        DB_ANALYTICS[(analytics_db\nPostgreSQL 16)]
        RedisCache[(Redis 7 Cluster\nCaching / Idempotency)]
        KafkaCluster[(Apache Kafka KRaft :9092\nEvent Backbone)]
    end

    Browser -->|HTTP REST & SSE| Gateway

    Gateway -->|/api/v1/auth/** & /users/**| Identity
    Gateway -->|/api/v1/products/**| Product
    Gateway -->|/api/v1/inventory/** & /warehouses/**| Inventory
    Gateway -->|/api/v1/orders/**| Order
    Gateway -->|/api/v1/notifications/**| Notification
    Gateway -->|/api/v1/analytics/**| Analytics
    Gateway -->|/api/v1/ai/**| AI

    Identity --> DB_ID
    Product --> DB_PROD
    Inventory --> DB_INV
    Order --> DB_ORD
    Notification --> DB_NOTIF
    Analytics --> DB_ANALYTICS

    Product -.-> RedisCache
    Order -.-> RedisCache
    Gateway -.-> RedisCache

    Order ==>|order.created| KafkaCluster
    KafkaCluster ==>|order.created| Inventory
    Inventory ==>|inventory.reserved / inventory.rejected| KafkaCluster
    KafkaCluster ==>|inventory.reserved| Order
    KafkaCluster ==>|order.confirmed / cancelled / low-stock| Notification
    KafkaCluster ==>|all events| Analytics
```

---

## 2. Event-Driven Choreography Saga

All order allocations are managed using asynchronous **Choreography Sagas**. A transactional outbox in `order-service` guarantees that order creation and event emission remain strictly atomic within PostgreSQL.

```mermaid
sequenceDiagram
    autonumber
    actor User as Customer / UI
    participant Gateway as API Gateway (:8080)
    participant OrderSvc as order-service (:8084)
    participant Outbox as Outbox Scheduler
    participant Kafka as Kafka KRaft (:9092)
    participant InvSvc as inventory-service (:8083)
    participant NotifSvc as notification-service (:8085)

    User->>Gateway: POST /api/v1/orders (Idempotency-Key)
    Gateway->>OrderSvc: Forward request + Correlation-ID
    OrderSvc->>OrderSvc: Verify Idempotency (Redis)
    OrderSvc->>OrderSvc: Insert Order (PENDING) & Outbox Record in DB
    OrderSvc-->>Gateway: 201 Created (Order PENDING)
    Gateway-->>User: Order confirmation response

    loop Every 500ms
        Outbox->>OrderSvc: Poll pending outbox entries
        OrderSvc->>Kafka: Publish "order.created"
        OrderSvc->>OrderSvc: Mark outbox entry as PROCESSED
    end

    Kafka->>InvSvc: Consume "order.created"
    alt Sufficient Warehouse Stock
        InvSvc->>InvSvc: Conditional Update (on_hand - reserved >= qty)
        InvSvc->>Kafka: Publish "inventory.reserved"
        Kafka->>OrderSvc: Consume "inventory.reserved"
        OrderSvc->>OrderSvc: Update Order status to CONFIRMED
        OrderSvc->>Kafka: Publish "order.confirmed"
        Kafka->>NotifSvc: Consume "order.confirmed"
        NotifSvc->>User: Stream SSE Notification (Order Confirmed)
    else Insufficient Available Stock
        InvSvc->>Kafka: Publish "inventory.rejected"
        Kafka->>OrderSvc: Consume "inventory.rejected"
        OrderSvc->>OrderSvc: Update Order status to CANCELLED
        OrderSvc->>Kafka: Publish "order.cancelled"
        Kafka->>NotifSvc: Consume "order.cancelled"
        NotifSvc->>User: Stream SSE Notification (Order Cancelled)
    end
```

---

## 3. Technology Stack & Design Rationale

| Layer | Technology | Version | Rationale & Architectural Purpose |
|---|---|---|---|
| **Frontend** | React, TypeScript, Vite, Tailwind | `18.3` | Ultra-fast client build with responsive UI, real-time status banners, and demo user fast-switching. |
| **State & Cache** | Redux Toolkit, TanStack Query | `2.x / 5.x` | Clean client auth storage in Redux + stale-while-revalidate caching and background polling for API data. |
| **API Gateway** | Spring Cloud Gateway, Java | `21` | Non-blocking reactive gateway with centralized JWT validation, header forwarding (`X-User-Role`, `X-Correlation-Id`), and token-bucket rate limiting. |
| **Core Services** | Spring Boot, Spring Data JPA | `3.3.4` | Enterprise service framework utilizing Java 21, Flyway migrations, and Hibernate ORM. |
| **Event Backbone** | Apache Kafka | `3.7.0` | KRaft mode (no ZooKeeper dependency). High-throughput, partitioned event topics with dead-letter queues. |
| **Databases** | PostgreSQL | `16.15` | Isolated databases per service (`identity_db`, `product_db`, `inventory_db`, `order_db`, `notification_db`, `analytics_db`). |
| **Distributed Cache** | Redis | `7-alpine` | Read-through catalog caching, Redis-backed idempotency key verification, and distributed rate limiting. |
| **Event Notification** | Node.js, Express, TypeScript | `22 LTS` | Lightweight I/O service handling KafkaJS event consumption and real-time Server-Sent Events (SSE). |
| **Analytics Service** | Node.js, Express, TypeScript | `22 LTS` | Asynchronous event projection engine calculating real-time revenue, order velocity, and fulfillment KPIs. |
| **AI Assistant** | Python, FastAPI, Pydantic | `3.12` | Operations assistant featuring autonomous tool-calling across live inventory and order endpoints with streaming responses. |
| **Testing** | JUnit 5, Playwright, Vitest, pytest, k6 | — | Multi-layer test coverage: unit tests, concurrency tests (50 parallel threads), and headless browser E2E tests. |
| **Observability** | OpenTelemetry, Prometheus, Grafana | — | End-to-end distributed telemetry, metric scraping at `/actuator/prometheus`, and pre-built Grafana operational dashboards. |

---

## 4. Microservices Directory & Port Map

| Service | Host Port | Runtime | Database | Primary Responsibility |
|---|---|---|---|---|
| **`frontend`** | `:5173` | Node 22 / Nginx | — | Responsive operations dashboard & administrative controls |
| **`api-gateway`** | `:8080` | Java 21 / Netty | — | Edge reverse proxy, JWT verification, route forwarding |
| **`identity-service`** | `:8081` | Java 21 / Tomcat | `identity_db` | User identity, BCrypt credentials, JWT token lifecycle |
| **`product-service`** | `:8082` | Java 21 / Tomcat | `product_db` | 5,200+ product catalog, categories, Redis sub-ms cache |
| **`inventory-service`** | `:8083` | Java 21 / Tomcat | `inventory_db` | Multi-warehouse stock tracking, conditional concurrency updates |
| **`order-service`** | `:8084` | Java 21 / Tomcat | `order_db` | Order lifecycle, Transactional Outbox, Idempotency-Key |
| **`notification-service`**| `:8085` | Node 22 / Express| `notification_db` | Kafka event consumption, in-app notifications, SSE stream |
| **`analytics-service`** | `:8086` | Node 22 / Express| `analytics_db` | Event projections, daily revenue aggregation, KPI trends |
| **`ai-service`** | `:8087` | Python 3.12 / Uvicorn | Read-only REST | AI Operations Assistant with tool-calling capabilities |

### Infrastructure Services
- **PostgreSQL 16**: Port `5432`
- **Redis 7**: Port `6379`
- **Apache Kafka (KRaft)**: Ports `9092` (internal) / `29092` (host)
- **Kafka UI**: Port `8089` (`http://localhost:8089`)
- **Prometheus**: Port `9090` (`http://localhost:9090`)
- **Grafana**: Port `3000` (`http://localhost:3000`, login: `admin` / `admin`)
- **OpenTelemetry Collector**: Ports `4317` (gRPC) / `4318` (HTTP)

---

## 5. Quick Start & Local Development

### Prerequisites
- **Docker Desktop** (running)
- **Java 21** (`openjdk@21`)
- **Node.js 22 LTS** & npm
- **Python 3.12**

### 1. Build & Start All Services
```bash
# Compile Java microservices, Node packages, and frontend bundle
make build

# Start all 17 containers via Docker Compose
make up
```

### 2. Populate Platform Seed Data (5,200 Products & 5 Warehouses)
```bash
make seed
```

### 3. Access the Dashboard
Open your web browser to:
👉 **[http://localhost:5173](http://localhost:5173)**

#### Pre-seeded Demo Accounts
| Role | Email | Password | Permissions |
|---|---|---|---|
| **ADMIN** | `admin@foodplatform.com` | `Admin123!` | Complete system governance, user management, metrics |
| **MANAGER** | `manager@foodplatform.com` | `Manager123!` | Order oversight, catalog updates, warehouse inventory |
| **WAREHOUSE_OPERATOR** | `operator@foodplatform.com` | `Operator123!` | Stock adjustments, replenishment, hub management |
| **CUSTOMER** | `customer@foodplatform.com` | `Customer123!` | Self-service order placement, personal order tracking |

---

## 6. Testing & Quality Assurance

### Automated Testing Matrix
```bash
# Type check and lint frontend and Node services
make lint

# Run all unit and integration test suites across all 8 microservices
make test

# Execute Playwright end-to-end browser user journeys
make e2e

# Run k6 load test against API Gateway
make load
```

### Concurrency Integrity Guarantee
The platform guarantees that simultaneous requests for stock will never oversell inventory. This is enforced via an atomic conditional SQL update:
```sql
UPDATE stock_levels 
SET reserved = reserved + :qty, version = version + 1 
WHERE id = :id AND (on_hand - reserved) >= :qty;
```
Verified through `InventoryConcurrencyTest.java` with 50 parallel threads competing for 10 units of stock.

---

## 7. Cloud Deployment & AWS Architecture

The platform includes production-ready Terraform configurations in `infrastructure/terraform/` deployable to AWS:

- **Compute**: AWS ECS Fargate running microservice containers
- **Database**: AWS Aurora / RDS PostgreSQL 16 (Multi-AZ)
- **Cache**: AWS ElastiCache for Redis
- **Messaging**: Amazon MSK (Managed Streaming for Apache Kafka) or EC2 KRaft container
- **Load Balancing & CDN**: AWS ALB (Application Load Balancer) + Amazon CloudFront + S3 for frontend SPA
- **Secrets Management**: AWS Secrets Manager
- **Observability**: AWS CloudWatch + Managed Prometheus & Grafana

```bash
# Plan cloud infrastructure
make tf-plan

# Deploy to AWS (requires configured AWS credentials)
make tf-apply
```

---

## 8. License

This project is licensed under the MIT License.
