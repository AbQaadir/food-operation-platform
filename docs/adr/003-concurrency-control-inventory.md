# ADR-003: Concurrency Control and Conditional Updates in Inventory Service

## Status
Accepted

## Context
In a high-throughput food operations platform, flash sales and multi-user order spikes create severe contention on inventory. When multiple customers attempt to reserve the last unit of an item simultaneously, naive read-modify-write patterns (`SELECT -> update in memory -> UPDATE`) result in race conditions and inventory overselling (negative stock).

The platform requires:
1. Strict guarantee against overselling (`on_hand - reserved >= 0`).
2. High throughput under concurrent reservation attempts.
3. Resilience to database-level lock contention.

## Decision
We implemented a multi-layered concurrency control strategy combining relational database constraints, atomic conditional SQL updates, and optimistic locking with bounded backoff retry:

1. **Database CHECK Constraint:**
   ```sql
   CONSTRAINT chk_stock_non_negative CHECK (on_hand - reserved >= 0);
   ```
   Ensures that no matter what application bug or race condition occurs, PostgreSQL's storage engine physically rejects any write that would make available inventory negative.

2. **Atomic Conditional Updates:**
   ```sql
   UPDATE stock_levels 
   SET reserved = reserved + :qty, 
       version = version + 1 
   WHERE id = :id AND (on_hand - reserved) >= :qty;
   ```
   PostgreSQL executes row-level predicate evaluation while holding a row exclusive lock during the update. If another transaction consumed the remaining stock, the condition `(on_hand - reserved) >= :qty` evaluates to false and `updatedRows` returns 0 without raising a database-level abort.

3. **Optimistic Locking (`@Version`) + Bounded Retry:**
   When contention occurs on the stock level row, the application layer retries up to 3 times with progressive backoff (10ms * attempt) before raising an `InsufficientStockException` (mapped to RFC 7807 HTTP 409 Conflict).

## Consequences
- **Positive:**
  - Guaranteed zero overselling, verified by a 50-thread concurrent integration test.
  - No database table-level locks; leverages fine-grained row-level locks in PostgreSQL.
  - Clean HTTP 409 Conflict semantics for the client when stock is exhausted.
- **Negative:**
  - Heavy contention on a single product's stock row causes serialization retries, which is mitigated by warehouse multi-sourcing and bounded retries.
