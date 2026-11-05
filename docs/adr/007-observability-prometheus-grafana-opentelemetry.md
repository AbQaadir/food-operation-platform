# ADR 007: Observability Strategy (Prometheus, Grafana, OpenTelemetry)

## Status
Accepted

## Context
In an event-driven microservices architecture spanning 7+ polyglot services (Spring Boot 3, Node.js 22 LTS, Python 3.12 FastAPI) communicating synchronously via REST and asynchronously via Apache Kafka KRaft, system visibility cannot rely on ad-hoc logging. Operators require:
1. Standardized RED metrics (Rate, Errors, Duration) across all services.
2. Real-time distributed tracing propagating correlation identifiers (`X-Correlation-Id`, W3C `traceparent`) across service boundaries and Kafka event headers.
3. Automated provisioning of monitoring infrastructure (Prometheus scrape configs, Grafana dashboards) so clean clones boot with instant telemetry.
4. Visibility into event broker health, consumer lag, and database connection pools.

## Decision
1. **Prometheus Scraping:**
   - Spring Boot Actuator exposes Micrometer Prometheus metrics at `/actuator/prometheus`.
   - Node.js and Python services expose standard Prometheus text-format metrics at `/metrics`.
   - Prometheus is configured with scrape targets across all services with 15s sampling interval.

2. **Distributed Tracing & Context Propagation:**
   - OpenTelemetry Collector Contrib receives OTLP traces on gRPC (4317) and HTTP (4318).
   - Spring Cloud API Gateway generates or propagates `X-Correlation-Id` on all incoming requests.
   - Transactional outbox publisher injects correlation IDs into Kafka message headers.
   - Event consumers log the correlation ID on message receipt.

3. **Grafana Dashboards as Code:**
   - Configured declarative provisioning:
     - Datasource: Prometheus (`http://prometheus:9090`).
     - Dashboards: `food-operations-overview.json` mounted into `/etc/grafana/provisioning/dashboards/json`.
   - Displays real-time RPS, 5xx error ratios, p95 latency histograms, JVM heap utilization, active SSE client streams, and AI assistant invocations.

## Consequences
- **Positive:**
  - Zero-touch monitoring: running `docker compose up` brings up the complete observability stack ready for evaluation.
  - Standardized SLO tracking against p95 latency and error rate thresholds.
- **Negative:**
  - Requires maintaining metric export endpoints across polyglot runtimes.
