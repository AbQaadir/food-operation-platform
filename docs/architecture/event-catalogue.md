# Event Catalogue & Architecture Sequence Diagrams

## 1. Domain Event Catalogue

All events in the Enterprise Food Operations Platform adhere to a standardized JSON event envelope and are published with partitioned keys to preserve ordering per aggregate root.

### Event Envelope Format (`contracts/events/`)
```json
{
  "eventId": "uuid-v4",
  "eventType": "domain.event.name",
  "version": 1,
  "occurredAt": "2026-10-04T15:30:00.000Z",
  "correlationId": "uuid-v4",
  "producer": "service-name",
  "payload": {}
}
```

### Complete Event Registry

| Topic Name | Producer | Consumers | Partition Key | Payload Summary |
|---|---|---|---|---|
| `order.created` | `order-service` | `inventory-service`, `notification-service`, `analytics-service` | `orderId` | `{ orderId, customerId, totalAmount, currency, items: [{ productId, qty, unitPrice }] }` |
| `order.confirmed` | `order-service` | `notification-service`, `analytics-service` | `orderId` | `{ orderId, customerId, status: "CONFIRMED", confirmedAt }` |
| `order.rejected` | `order-service` | `notification-service`, `analytics-service` | `orderId` | `{ orderId, customerId, reason, status: "REJECTED" }` |
| `order.cancelled` | `order-service` | `inventory-service`, `notification-service`, `analytics-service` | `orderId` | `{ orderId, customerId, status: "CANCELLED", cancelledAt }` |
| `inventory.reserved` | `inventory-service` | `order-service`, `analytics-service` | `orderId` | `{ orderId, warehouseId, reservations: [{ productId, qty, stockLevelId }] }` |
| `inventory.rejected` | `inventory-service` | `order-service`, `analytics-service` | `orderId` | `{ orderId, reason: "INSUFFICIENT_STOCK", unavailableProductIds: [] }` |
| `inventory.released` | `inventory-service` | `analytics-service` | `orderId` | `{ orderId, releasedAt }` |
| `inventory.low-stock` | `inventory-service` | `notification-service`, `analytics-service` | `productId` | `{ productId, warehouseId, currentStock, threshold }` |
| `product.updated` | `product-service` | `inventory-service`, `order-service` | `productId` | `{ productId, sku, name, price, active, updatedAt }` |

---

## 2. Order Lifecycle Sequence Diagrams

### 2.1 Happy Path Flow (Order Placement to Confirmation)
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer / Browser
    participant Gateway as API Gateway
    participant OrderSvc as Order Service
    participant ProductSvc as Product Service
    participant Kafka as Apache Kafka (KRaft)
    participant InvSvc as Inventory Service
    participant NotifSvc as Notification Service
    participant Analytics as Analytics Service

    Customer->>Gateway: POST /api/v1/orders (Idempotency-Key)
    Gateway->>OrderSvc: Forward request with X-Correlation-Id
    OrderSvc->>ProductSvc: GET /api/v1/products/{id} (Validate Prices via Resilience4j)
    ProductSvc-->>OrderSvc: Return verified item prices
    OrderSvc->>OrderSvc: Persist Order (PENDING) + outbox_event in 1 DB TX
    OrderSvc-->>Gateway: HTTP 201 Created { id, status: "PENDING" }
    Gateway-->>Customer: Render Order Confirmation
    OrderSvc->>Kafka: OutboxPublisher emits order.created

    par Asynchronous Event Choreography
        Kafka->>InvSvc: Consume order.created
        InvSvc->>InvSvc: Atomic conditional UPDATE stock_levels
        InvSvc->>Kafka: Emit inventory.reserved
    and
        Kafka->>NotifSvc: Consume order.created (Queue alert)
    and
        Kafka->>Analytics: Consume order.created (Increment daily revenue)
    end

    Kafka->>OrderSvc: Consume inventory.reserved
    OrderSvc->>OrderSvc: Transition Order PENDING -> CONFIRMED
    OrderSvc->>Kafka: Emit order.confirmed
    Kafka->>NotifSvc: Push SSE notification to browser: "Order Confirmed!"
```

---

### 2.2 Rejection Path (Insufficient Stock)
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer / Browser
    participant OrderSvc as Order Service
    participant Kafka as Apache Kafka (KRaft)
    participant InvSvc as Inventory Service
    participant NotifSvc as Notification Service

    Customer->>OrderSvc: Place Order for Item (Qty: 5)
    OrderSvc->>OrderSvc: Persist Order PENDING + outbox_event
    OrderSvc->>Kafka: OutboxPublisher emits order.created

    Kafka->>InvSvc: Consume order.created
    InvSvc->>InvSvc: Evaluate (on_hand - reserved) >= 5 -> FALSE
    InvSvc->>Kafka: Emit inventory.rejected (reason: "INSUFFICIENT_STOCK")

    Kafka->>OrderSvc: Consume inventory.rejected
    OrderSvc->>OrderSvc: Transition Order PENDING -> REJECTED
    OrderSvc->>Kafka: Emit order.rejected
    Kafka->>NotifSvc: Push SSE notification: "Order rejected due to stock shortage"
```

---

### 2.3 Cancellation & Compensation Path
```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer / Browser
    participant OrderSvc as Order Service
    participant Kafka as Apache Kafka (KRaft)
    participant InvSvc as Inventory Service
    participant NotifSvc as Notification Service

    Customer->>OrderSvc: POST /api/v1/orders/{id}/cancel
    OrderSvc->>OrderSvc: Verify state transition (CONFIRMED -> CANCELLED)
    OrderSvc->>OrderSvc: Persist CANCELLED + outbox_event
    OrderSvc->>Kafka: OutboxPublisher emits order.cancelled

    Kafka->>InvSvc: Consume order.cancelled
    InvSvc->>InvSvc: Release reserved stock (UPDATE stock_levels SET reserved = reserved - qty)
    InvSvc->>Kafka: Emit inventory.released

    Kafka->>NotifSvc: Push SSE notification: "Order #ID cancelled, inventory refunded"
```

---

## 3. C4 Architecture Diagrams

### 3.1 C4 Level 1: System Context Diagram
```mermaid
flowchart TD
    User["Store Manager / Operator / Customer\n[Person]"]
    System["Enterprise Food Operations Platform\n[Software System]"]
    Payment["External Payment / Bank API\n[External System]"]
    CloudProvider["AWS Cloud Infrastructure\n(ECS, RDS, MSK, ALB, CloudFront)\n[Cloud Platform]"]

    User -->|Views catalog, places orders, manages stock| System
    System -->|Processes transactions & notifications| User
    System -.->|Payment verification| Payment
    System -->|Runs on| CloudProvider
```

### 3.2 C4 Level 2: Container Diagram
```mermaid
flowchart TD
    subgraph ClientLayer["Edge & Client Tier"]
        Browser["React 18 SPA\n[Vite, TS, Tailwind, Redux]"]
        Gateway["API Gateway\n[Spring Cloud Gateway :8080]"]
    end

    subgraph ServiceLayer["Polyglot Microservices Tier"]
        Identity["Identity Service\n[Spring Boot 3 :8081]"]
        Product["Product Service\n[Spring Boot 3 :8082]"]
        Inventory["Inventory Service\n[Spring Boot 3 :8083]"]
        Order["Order Service\n[Spring Boot 3 :8084]"]
        Notification["Notification Service\n[Node.js 22 Express :8085]"]
        Analytics["Analytics Service\n[Node.js 22 Express :8086]"]
        AI["AI Assistant\n[FastAPI Python 3.12 :8087]"]
    end

    subgraph PersistenceLayer["Storage & Messaging Tier"]
        PG[(PostgreSQL 16\nDedicated Databases)]
        Redis[(Redis 7\nCache & Idempotency)]
        Kafka[(Apache Kafka KRaft\nEvent Log)]
    end

    Browser -->|HTTPS / REST / SSE| Gateway
    Gateway --> Identity
    Gateway --> Product
    Gateway --> Inventory
    Gateway --> Order
    Gateway --> Notification
    Gateway --> Analytics
    Gateway --> AI

    Identity --> PG
    Product --> PG
    Inventory --> PG
    Order --> PG
    Notification --> PG
    Analytics --> PG

    Product -.-> Redis
    Order -.-> Redis
    Notification -.-> Redis
    Gateway -.-> Redis

    Order ==>|Events| Kafka
    Inventory ==>|Events| Kafka
    Product ==>|Events| Kafka
    Kafka ==> Notification
    Kafka ==> Analytics
    Kafka ==> Inventory
    Kafka ==> Order
```
