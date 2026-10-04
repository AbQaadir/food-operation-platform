# Performance & Load Testing Suite (k6)

This directory contains load tests verifying platform SLOs under realistic enterprise production traffic.

## Test Scenarios

### 1. Catalog Search Load (`catalog-search-load.js`)
- **Target SLO:** P95 latency < 50ms at up to 500 requests/second.
- **Underlying Mechanics:**
  - Evaluates Redis cache hit performance on hot products.
  - Evaluates PostgreSQL `pg_trgm` GIN index on text search queries across 5,200+ catalog items.
- **Execution:**
  ```bash
  k6 run tests/load/catalog-search-load.js
  ```

### 2. Concurrent Order Checkout (`order-checkout-load.js`)
- **Target SLO:** P95 latency < 300ms under 50 orders/second concurrent checkout.
- **Underlying Mechanics:**
  - Generates client-side `Idempotency-Key` headers per transaction.
  - Writes to transactional outbox and triggers asynchronous Saga choreography.
  - Verifies zero overselling and bounded retries on inventory locks.
- **Execution:**
  ```bash
  k6 run tests/load/order-checkout-load.js
  ```

## Running with Docker (if k6 is not installed locally)
```bash
docker run --rm -i --network=foodoperationplatform_default \
  -e GATEWAY_URL=http://api-gateway:8080 \
  grafana/k6 run - < tests/load/catalog-search-load.js
```
