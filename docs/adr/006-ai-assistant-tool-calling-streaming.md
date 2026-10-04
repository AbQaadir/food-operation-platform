# ADR 006: AI Operations Assistant with Tool Calling & SSE Streaming

## Status
Accepted

## Context
The Enterprise Food Operations Platform requires an intelligent operational assistant capable of querying operational data (real-time inventory levels across warehouses, order statuses, low-stock threshold alerts, and revenue/sales performance KPIs). Operators need immediate, interactive insights via natural language conversational interfaces without manual database querying.

Key considerations:
1. **Safety and Least Privilege:** The AI assistant must only have read-only access to operational domain data. It should never perform state-mutating operations directly without human validation.
2. **Real-time UX:** Operations staff expect low latency and incremental updates rather than blocking for full model inference and tool aggregation.
3. **Extensibility:** The system must support mock/test providers, local development modes, and cloud LLM providers (e.g. Gemini, OpenAI) with zero application code changes.
4. **Resilience & Decoupling:** In the event of backend service timeouts or degradation, fallback adapters must protect user experience.

## Decision
We implemented `ai-service` using Python 3.12 and FastAPI with asynchronous streaming SSE (`text/event-stream`):

1. **Tool-Calling Architecture:**
   - Designed 4 discrete, read-only tools:
     - `get_stock_level(product_id, warehouse_id)`: queries `inventory-service` via HTTP client.
     - `get_order_status(order_id)`: queries `order-service` via HTTP client.
     - `list_low_stock_products(threshold)`: identifies products below inventory safety stock.
     - `get_daily_sales(date_str)`: calculates revenue and order fulfillment KPIs.
   - Assistant inspects user intents, dispatches tool execution events asynchronously, and synthesizes structured operational summaries.

2. **Server-Sent Events (SSE) Streaming Protocol:**
   - Emits structured events over `POST /api/v1/ai/chat` (and `/api/v1/assistant/chat`):
     - `event: tool_call`: Notifies client of tool invocation with parameters.
     - `event: tool_result`: Returns structured data payload fetched by tool.
     - `event: token`: Streams natural language explanation word-by-word.
     - `event: done`: Emits completion status payload.

3. **Gateway Integration:**
   - Routed through Spring Cloud Gateway (`api-gateway`) at `http://api-gateway:8080/api/v1/ai/**` and `/api/v1/assistant/**` with correlation ID propagation and optional JWT enrichment (`X-User-Id`, `X-User-Role`).

## Consequences
- **Positive:**
  - Clear real-time observability in UI: frontend renders tool badges, live data cards, and typewriter text streams simultaneously.
  - Zero DB coupling: relies strictly on REST APIs, respecting service boundary isolation.
  - Testable with pytest and FastAPI TestClient without external LLM API costs.
- **Negative:**
  - Streaming HTTP connections (SSE) require persistent sockets; reverse proxies must disable response buffering (`X-Accel-Buffering: no`).
