# Part 2 - Supabase Schema and Vector Retrieval

This folder contains ordered SQL scripts for Part 2.

## Execution Order
1. `001_enable_extensions.sql`
2. `002_core_tables.sql`
3. `003_indexes_and_constraints.sql`
4. `004_vector_search_function.sql`
5. `005_metadata_filter_function.sql`
6. Optional sample data: `seed_sample_products.sql`
7. Validation checks: `VALIDATION_QUERIES.sql`

## Notes
- Embeddings use `vector(3072)` for `text-embedding-3-large`.
- Similarity metric is cosine distance.
- On some Supabase pgvector setups, ANN indexes (`ivfflat`/`hnsw`) don't support vectors above 2000 dimensions. In that case, vector retrieval runs as exact cosine scan (no ANN index) until dimensions are reduced.
- `products` remains the transactional product projection; `product_embeddings` is retrieval support only.
- `sync_events` enforces idempotency.
- `sync_failures` stores DLQ payloads for replay.
