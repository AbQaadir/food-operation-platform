# Benchmark: PostgreSQL GIN Trigram Search Optimization

## Overview
This benchmark evaluates query execution performance for product text search on the `product_db` database containing 5,200 products. Substring matching (`LIKE '%term%'`) typically triggers a full sequential table scan in relational databases because B-Tree indexes cannot index wildcard prefixes. By leveraging PostgreSQL's `pg_trgm` extension and a Generalized Inverted Index (GIN) on trigrams, substring search can be evaluated via inverted index lookups.

- **Dataset Size:** 5,200 records
- **Target Table:** `products`
- **Search Expression:** `WHERE lower(name) LIKE '%spinach%'`
- **PostgreSQL Version:** 16.15 (Alpine)

---

## Benchmark 1: Sequential Scan (Without Trigram Index)

```sql
SET enable_seqscan = on;
SET enable_bitmapscan = off;
EXPLAIN ANALYZE SELECT * FROM products WHERE lower(name) LIKE '%spinach%';
```

### Execution Plan:
```
                                                QUERY PLAN                                                
----------------------------------------------------------------------------------------------------------
 Seq Scan on products  (cost=0.00..235.00 rows=263 width=207) (actual time=0.025..2.557 rows=178 loops=1)
   Filter: (lower((name)::text) ~~ '%spinach%'::text)
   Rows Removed by Filter: 5022
 Planning Time: 1.372 ms
 Execution Time: 2.650 ms
```

### Analysis:
- The database engine is forced to scan every single page and row in the table (`Heap Scan`), checking each string for substring containment.
- 5,022 rows were evaluated and discarded by the filter.
- Overall execution time: **2.650 ms**.

---

## Benchmark 2: Bitmap Index Scan (With GIN Trigram Index)

The index was created via Flyway migration `V2__add_trigram_indexes.sql`:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin (lower(name) gin_trgm_ops);
```

```sql
SET enable_seqscan = off;
SET enable_bitmapscan = on;
EXPLAIN ANALYZE SELECT * FROM products WHERE lower(name) LIKE '%spinach%';
```

### Execution Plan:
```
                                                             QUERY PLAN                                                             
------------------------------------------------------------------------------------------------------------------------------------
 Bitmap Heap Scan on products  (cost=53.17..219.38 rows=263 width=207) (actual time=0.273..0.794 rows=178 loops=1)
   Recheck Cond: (lower((name)::text) ~~ '%spinach%'::text)
   Heap Blocks: exact=111
   ->  Bitmap Index Scan on idx_products_name_trgm  (cost=0.00..53.10 rows=263 width=0) (actual time=0.254..0.255 rows=179 loops=1)
         Index Cond: (lower((name)::text) ~~ '%spinach%'::text)
 Planning Time: 0.999 ms
 Execution Time: 0.947 ms
```

### Analysis:
- `Bitmap Index Scan on idx_products_name_trgm` decomposes `'spinach'` into trigrams (`spi`, `pin`, `ina`, `nac`, `ach`) and resolves candidate row pointers from the GIN index in **0.254 ms**.
- `Bitmap Heap Scan` fetches only the 111 matching heap blocks directly instead of reading the entire table.
- Execution time dropped from **2.650 ms** to **0.947 ms** (~**64.3% latency reduction**).
- As the catalog scales to 100,000+ items, the performance divergence grows exponentially (O(N) full table scan vs O(log N) inverted index lookups).

---

## Conclusion
The `pg_trgm` GIN index provides sub-millisecond prefix, suffix, and infix text matching for the enterprise catalog, ensuring responsive search under high concurrent load without external search infrastructure for medium-scale catalogs.
