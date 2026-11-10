# CLAUDE.md — Claude Code Guidelines

## Overview
Enterprise Event-Driven Microservices Food Operations Platform.
Tech Stack: Java 21 (Spring Boot 3), Node.js 22 LTS (Express/TypeScript), Python 3.12 (FastAPI), React 18 (Vite/Tailwind), Apache Kafka KRaft, PostgreSQL 16, Redis 7, Docker Compose.

See [AGENTS.md](./AGENTS.md) for the complete multi-agent standard, architectural invariants, and boundary rules.

---

## Essential Commands

```bash
# Full Platform Boot & Teardown
make up                                  # Start all 13 containers via Docker Compose
make down                                # Stop all containers and remove volumes
make seed                                # Seed 5,200 products & multi-warehouse inventory

# Golden Verification (Run before finishing any task!)
python3 scripts/run_production_tests.py  # 28-test end-to-end functional & concurrency suite
cd tests/e2e && npx playwright test      # Playwright browser journeys
k6 run tests/load/catalog-search-load.js  # k6 catalog search benchmark
k6 run tests/load/order-checkout-load.js  # k6 order checkout concurrency benchmark

# Frontend
cd frontend && npm run test              # Vitest component & store unit tests
cd frontend && npm run lint              # Type check (tsc --noEmit)
cd frontend && npm run build             # Production Vite build
```

---

## Architectural Rules
1. **Database Isolation**: No service accesses another service's database directly. Use Kafka events or Gateway REST.
2. **Transactional Outbox**: Orders publish to Kafka via transactional outbox table in the same DB transaction.
3. **Atomic Concurrency**: Inventory updates MUST use conditional SQL (`WHERE on_hand - reserved >= :qty`) to prevent overselling.
4. **Idempotency**: `POST /api/v1/orders` requires `Idempotency-Key` header; missing header returns 400 RFC 7807 problem details.
5. **No `any`**: Strict TypeScript in frontend and Node services. Pydantic v2 in FastAPI.

---

## Key URLs (Local Runtime)
- Frontend: `http://localhost:5173` (Demo login: `admin@foodplatform.com` / `Admin123!`)
- API Gateway: `http://localhost:8080`
- Kafka UI: `http://localhost:8089`
- Grafana: `http://localhost:3000` (`admin` / `admin`)
- Prometheus: `http://localhost:9090`
