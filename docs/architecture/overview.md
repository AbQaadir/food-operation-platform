# Enterprise Food Operations Platform — Architecture Overview

## 1. System Context & Overview

The **Enterprise Food Operations Platform** is an enterprise-grade, event-driven microservices platform designed for modern food-service operations. It coordinates products, multi-warehouse inventory, customer orders, real-time notifications, analytical KPI aggregation, and an intelligent AI operations assistant.

The architecture strictly follows the **database-per-service** pattern to ensure loose coupling, independent scalability, and domain isolation. Asynchronous domain events are coordinated through **Apache Kafka** using the **Transactional Outbox Pattern**, while synchronous edge traffic and inter-service queries flow through an **API Gateway** with Resilience4j circuit breakers, rate limiting, and distributed tracing.

```mermaid
flowchart TD
    subgraph Clients["Clients & Edge"]
        UserBrowser["Web Browser (React SPA :5173)"]
        ExternalAPI["External API Clients / Consumers"]
    end

    subgraph EdgeTier["Edge Gateway"]
        Gateway["API Gateway (Spring Cloud Gateway :8080)\n- Route Handling\n- JWT Validation & RBAC\n- Redis Rate Limiter\n- Correlation ID Injection"]
    end

    subgraph CoreServices["Domain Microservices"]
        IdentitySvc["identity-service (:8081)\nJava 21 / Spring Boot 3\nAuth, Users, JWT Issuance"]
        ProductSvc["product-service (:8082)\nJava 21 / Spring Boot 3\nProducts, Categories, Prices, Redis Cache"]
        InventorySvc["inventory-service (:8083)\nJava 21 / Spring Boot 3\nWarehouses, Stock Levels, Reservations"]
        OrderSvc["order-service (:8084)\nJava 21 / Spring Boot 3\nOrders, Outbox Publisher, Idempotency"]
        NotificationSvc["notification-service (:8085)\nNode 22 / Express / TS\nKafka Consumer, Notifications, SSE"]
        AnalyticsSvc["analytics-service (:8086)\nNode 22 / Express / TS\nAggregated Sales & Stock KPIs"]
        AISvc["ai-service (:8087)\nPython 3.12 / FastAPI\nRead-only Assistant with Tool Calling"]
    end

    subgraph DataTier["Data & Cache Tier (Isolated per Service)"]
        IdentityDB[(identity_db\nPostgreSQL)]
        ProductDB[(product_db\nPostgreSQL)]
        InventoryDB[(inventory_db\nPostgreSQL)]
        OrderDB[(order_db\nPostgreSQL)]
        NotificationDB[(notification_db\nPostgreSQL)]
        AnalyticsDB[(analytics_db\nPostgreSQL)]
        SharedRedis[(Redis 7\nCache, Idempotency, Rate Limits)]
    end

    subgraph EventStream["Messaging & Event Backbone"]
        KafkaBrokers["Apache Kafka (KRaft Mode :9092)\nTopics: order.*, inventory.*, product.updated, *.dlq"]
        KafkaUI["Kafka UI (:8089)"]
    end

    subgraph ObservabilityTier["Observability & Monitoring"]
        OTel["OpenTelemetry Collector (:4317)"]
        Prometheus["Prometheus (:9090)"]
        Grafana["Grafana (:3000)"]
    end

    UserBrowser -->|HTTP / REST| Gateway
    ExternalAPI -->|HTTP / REST| Gateway

    Gateway -->|/api/v1/auth/**, /users/**| IdentitySvc
    Gateway -->|/api/v1/products/**, /categories/**| ProductSvc
    Gateway -->|/api/v1/inventory/**, /warehouses/**| InventorySvc
    Gateway -->|/api/v1/orders/**| OrderSvc
    Gateway -->|/api/v1/notifications/**| NotificationSvc
    Gateway -->|/api/v1/analytics/**| AnalyticsSvc
    Gateway -->|/api/v1/assistant/**| AISvc

    %% Service to DB connections
    IdentitySvc --> IdentityDB
    ProductSvc --> ProductDB
    InventorySvc --> InventoryDB
    OrderSvc --> OrderDB
    NotificationSvc --> NotificationDB
    AnalyticsSvc --> AnalyticsDB

    %% Redis connections
    ProductSvc -.->|Cache products (10m TTL)| SharedRedis
    OrderSvc -.->|Idempotency Keys (24h TTL)| SharedRedis
    NotificationSvc -.->|Unread counts cache| SharedRedis
    Gateway -.->|Token Bucket Rate Limiting| SharedRedis

    %% Resilience4j REST
    OrderSvc -.->|REST validate prices\n(Resilience4j)| ProductSvc
    AISvc -.->|REST query tools via Gateway| Gateway

    %% Kafka Events
    OrderSvc == Publish order.created, order.confirmed, order.cancelled ==> KafkaBrokers
    InventorySvc == Publish inventory.reserved, inventory.rejected, inventory.released, inventory.low-stock ==> KafkaBrokers
    ProductSvc == Publish product.updated ==> KafkaBrokers

    KafkaBrokers == Consume order.created, order.cancelled ==> InventorySvc
    KafkaBrokers == Consume inventory.reserved, inventory.rejected ==> OrderSvc
    KafkaBrokers == Consume order.*, inventory.low-stock ==> NotificationSvc
    KafkaBrokers == Consume order.*, inventory.* ==> AnalyticsSvc

    %% Observability
    Gateway -.->|Metrics/Traces| OTel
    IdentitySvc -.->|Metrics/Traces| OTel
    ProductSvc -.->|Metrics/Traces| OTel
    InventorySvc -.->|Metrics/Traces| OTel
    OrderSvc -.->|Metrics/Traces| OTel
    NotificationSvc -.->|Metrics/Traces| OTel
    AnalyticsSvc -.->|Metrics/Traces| OTel
    AISvc -.->|Metrics/Traces| OTel

    OTel --> Prometheus
    Prometheus --> Grafana
    KafkaBrokers -.-> KafkaUI
```

---

## 2. Service Responsibilities & Ports

| Service | Technology | Port | Database | Primary Responsibility |
|---|---|---|---|---|
| `frontend` | React 18, TypeScript, Vite, Tailwind | 5173 | — | Single-page application dashboard for operational management |
| `api-gateway` | Spring Boot 3.x, Spring Cloud Gateway | 8080 | — | Reverse proxy, JWT authentication & RBAC, rate-limiting, CORS, correlation tracking |
| `identity-service` | Spring Boot 3.x, Spring Security, JPA | 8081 | `identity_db` | User identity, credentials, roles (`ADMIN`, `MANAGER`, `WAREHOUSE_OPERATOR`, `CUSTOMER`), JWT token issuance |
| `product-service` | Spring Boot 3.x, Spring Data JPA, Redis | 8082 | `product_db` | Product catalog, categories, pricing, unit definitions, Redis query caching |
| `inventory-service` | Spring Boot 3.x, Spring Data JPA | 8083 | `inventory_db` | Multi-warehouse stock tracking, reservations with optimistic locking + conditional updates |
| `order-service` | Spring Boot 3.x, Spring Data JPA | 8084 | `order_db` | Order orchestration, transactional outbox pattern, state machine, idempotency checking |
| `notification-service` | Node.js 22, Express, TypeScript, KafkaJS | 8085 | `notification_db` | Kafka event consumption, persistence of user notifications, unread counts, optional SSE live stream |
| `analytics-service` | Node.js 22, Express, TypeScript | 8086 | `analytics_db` | Event-driven KPI projection, daily revenue metrics, top-performing product trends |
| `ai-service` | Python 3.12, FastAPI, Pydantic | 8087 | Read-only | AI operations assistant with structured read-only tool calling via the Gateway |

---

## 3. Communication Patterns

### Synchronous REST
- **Client to Gateway:** All external requests enter through the API Gateway at `http://localhost:8080/api/v1/...`.
- **Gateway to Microservices:** Reverse proxy forwarding based on route patterns. All requests are annotated with `X-Correlation-Id`.
- **Order to Product Validation:** `order-service` calls `product-service` synchronously via REST to validate item prices at order placement. This synchronous interaction is shielded using Resilience4j (timeout 2s, retry 2x, circuit breaker with fallback).
- **AI Assistant to Platform:** `ai-service` executes read-only tool calls by invoking the Gateway REST endpoints using the caller's JWT.

### Asynchronous Event Streaming (Kafka)
- **Transactional Outbox:** Aggregate state mutations and event publication occur atomically within a single database transaction. An asynchronous worker polls or streams outbox events to Kafka.
- **Order-Inventory Saga:**
  1. `order-service` emits `order.created`.
  2. `inventory-service` attempts stock reservation:
     - On success: emits `inventory.reserved`.
     - On failure (insufficient stock): emits `inventory.rejected`.
  3. `order-service` consumes reservation result:
     - `inventory.reserved` transitions order to `CONFIRMED` and emits `order.confirmed`.
     - `inventory.rejected` transitions order to `REJECTED`.
  4. On customer cancellation, `order-service` emits `order.cancelled` which instructs `inventory-service` to release reserved stock (`inventory.released`).
- **Notification & Analytics Fans:**
  - `notification-service` consumes order and inventory events to notify users.
  - `analytics-service` consumes events to maintain rolling KPI read models.
