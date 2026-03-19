-- Part 2 / Step 3
-- Performance indexes and basic data constraints

create index if not exists idx_products_shop_domain on public.products(shop_domain);
create index if not exists idx_products_price on public.products(price);
create index if not exists idx_products_inventory on public.products(inventory);
create index if not exists idx_products_tags_gin on public.products using gin(tags);
create index if not exists idx_products_updated_at on public.products(updated_at desc);
create index if not exists idx_product_embeddings_product_id on public.product_embeddings(product_id);

-- ANN vector index is intentionally skipped here.
-- On this Supabase pgvector setup, ivfflat/hnsw indexes reject vectors > 2000 dimensions,
-- and text-embedding-3-large is 3072 dimensions.
-- Retrieval still works using exact cosine distance scan via `<=>` in the SQL function.
-- If ANN indexing is required later, switch embedding dimension <= 2000 and recreate index.

create index if not exists idx_sync_events_topic_received on public.sync_events(event_topic, received_at desc);
create index if not exists idx_sync_events_product_id on public.sync_events(product_id);
create index if not exists idx_sync_failures_status_next_retry on public.sync_failures(status, next_retry_at);

alter table public.products
  add constraint chk_products_inventory_non_negative
  check (inventory >= 0);

alter table public.products
  add constraint chk_products_price_non_negative
  check (price >= 0);

alter table public.sync_events
  add constraint chk_sync_events_status
  check (status in ('received', 'processed', 'skipped', 'failed'));

alter table public.sync_failures
  add constraint chk_sync_failures_status
  check (status in ('pending', 'retrying', 'resolved', 'dead'));

alter table public.sync_failures
  add constraint chk_sync_failures_retry_count_non_negative
  check (retry_count >= 0);
