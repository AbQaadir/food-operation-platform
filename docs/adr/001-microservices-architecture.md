# ADR 001: Adoption of Microservices Architecture

## Status
Accepted

## Context
The Enterprise Food Operations Platform manages multiple distinct operational capabilities:
- User identity, credentials, and access control
- Product catalogs, pricing, and category hierarchies
- Warehouse inventory tracking and stock reservation concurrency
- Order placement, state machines, and transactional outbox eventing
- Event-driven notifications and real-time alerts
- AI-driven operations assistance via LLM tool-calling

A monolithic architecture would tightly couple deployment cycles, create shared database contention across high-throughput domains, and prevent polyglot service optimization.

## Decision
We adopt an event-driven **microservices architecture** with a **database-per-service** boundary:
1. **Core Business Domains (Java 21 / Spring Boot 3):** `identity-service`, `product-service`, `inventory-service`, and `order-service`.
2. **Notification & Aggregation (Node.js 22 / Express / TypeScript):** `notification-service` and `analytics-service`.
3. **AI Operations Assistant (Python 3.12 / FastAPI):** `ai-service`.
4. **Edge Gateway (Spring Cloud Gateway):** Directs incoming traffic, enforces rate limiting, authenticates JWTs, and injects correlation IDs.

## Consequences
### Positive
- Independent scalability of write-heavy and read-heavy services.
- Fault isolation: failure in notification/AI does not disrupt order processing.
- Strict schema boundaries prevent accidental cross-boundary database coupling.
### Negative & Trade-offs
- Requires distributed transaction handling (Sagas) rather than two-phase commits.
- Added infrastructure complexity managed via Docker Compose and Terraform.
