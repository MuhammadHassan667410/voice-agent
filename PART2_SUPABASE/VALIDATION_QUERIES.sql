-- Validation script for Part 2

-- 1) Table existence sanity
select table_name
from information_schema.tables
where table_schema = 'public'
  and table_name in ('products', 'product_embeddings', 'sync_events', 'sync_failures')
order by table_name;

-- 2) Index sanity
select indexname, tablename
from pg_indexes
where schemaname = 'public'
  and tablename in ('products', 'product_embeddings', 'sync_events', 'sync_failures')
order by tablename, indexname;

-- 3) Constraints sanity
select conname, conrelid::regclass as table_name
from pg_constraint
where conrelid::regclass::text in (
  'products', 'product_embeddings', 'sync_events', 'sync_failures'
)
order by table_name, conname;

-- 4) Seed count sanity
select
  (select count(*) from public.products) as product_count,
  (select count(*) from public.product_embeddings) as embedding_count;

-- 5) Filter function sanity
select *
from public.filter_products(
  page_limit => 10,
  page_offset => 0,
  min_price => 50,
  max_price => 120,
  required_tags => array['football']::text[],
  in_stock_only => true,
  sort_field => 'price',
  sort_order => 'asc',
  shop_domain_filter => 'pmcvp2-tv.myshopify.com'
);

-- 6) Vector function sanity with synthetic query vector
select *
from public.match_products(
  query_embedding => ('[' || array_to_string(array_fill(0.0015::float8, array[3072]), ',') || ']')::vector,
  match_count => 12,
  min_price => 0,
  max_price => 200,
  required_tags => array['football']::text[],
  in_stock_only => true,
  variant_option_contains => null,
  shop_domain_filter => 'pmcvp2-tv.myshopify.com'
);

-- 7) Idempotency uniqueness sanity
insert into public.sync_events (
  idempotency_key, event_topic, event_id, shop_domain, product_id,
  event_occurred_at, status, payload, trace_id
)
values
(
  'pmcvp2-tv.myshopify.com:products/update:gid://shopify/Product/1001:2026-03-17T10:00:00Z',
  'products/update',
  'evt-demo-1',
  'pmcvp2-tv.myshopify.com',
  'gid://shopify/Product/1001',
  '2026-03-17T10:00:00Z',
  'processed',
  '{"demo":true}'::jsonb,
  'tr_demo_1'
)
on conflict (idempotency_key) do nothing;
