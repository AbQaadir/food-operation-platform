# GitHub Copilot Instructions — Food Operations Platform

## Context & Workspace Scope
You are working on an enterprise event-driven microservices food operations platform. The repository is a monorepo containing:
- **5 Spring Boot 3 / Java 21 microservices** (`services/api-gateway`, `services/identity-service`, `services/product-service`, `services/inventory-service`, `services/order-service`)
- **2 Node.js 22 TypeScript microservices** (`services/notification-service`, `services/analytics-service`)
- **1 Python 3.12 FastAPI microservice** (`services/ai-service`)
- **1 React 18 / Vite frontend** (`frontend`)
- **Infrastructure**: Apache Kafka KRaft, PostgreSQL 16 (5 isolated databases), Redis 7, Prometheus, Grafana, OpenTelemetry Collector.

Refer to [`AGENTS.md`](../AGENTS.md) for full architectural invariants, commands, and boundaries.

---

## Code Generation Guidelines

### 1. Java 21 / Spring Boot 3
- Use modern Java 21 idioms (records, pattern matching, switch expressions, text blocks).
- Always wrap database mutation flows with `@Transactional(isolation = Isolation.READ_COMMITTED)`.
- Use Spring 6 / Boot 3 `ProblemDetail` (RFC 7807) for error responses. Include `title`, `status`, `detail`, `instance`, and `timestamp`.
- Do not cross database boundaries. Use Kafka events or Feign/WebClient via API Gateway.
- Flyway migrations must be incremental (`V{N}__*.sql`) in `src/main/resources/db/migration/`.

### 2. Node.js 22 / TypeScript
- Enforce strict typing. Do not use `any`. Use discriminated unions for Kafka event payloads.
- Use KafkaJS with robust retry and error handling.
- When publishing Server-Sent Events (SSE), maintain headers:
  `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`.

### 3. Python 3.12 / FastAPI
- Use Pydantic v2 models for request/response validation.
- All endpoints must be typed and annotated with FastAPI response models.
- Support mock LLM fallbacks (`LLM_PROVIDER=mock`) so tests run offline without external API keys.

### 4. React 18 / Frontend
- Use Redux Toolkit (`createSlice`, `createAsyncThunk`) with typed hooks (`useAppDispatch`, `useAppSelector`).
- Style components with Tailwind CSS utility classes.
- Co-locate component tests using Vitest and React Testing Library.

---

## Safety Guardrails
- **Never hardcode secrets**: Use environment variables with sensible local defaults.
- **Never remove atomic stock logic**: Stock reservation in `inventory-service` must use conditional SQL to guarantee 0 overselling.
- **Always verify**: After modifying code, run `python3 scripts/run_production_tests.py` to ensure all 28 platform tests pass.
