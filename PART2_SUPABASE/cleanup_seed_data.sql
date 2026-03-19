-- Cleanup script for Part 2 seed/demo data
-- Run this after seed/validation if you want a clean database.

begin;

-- Remove seed embeddings first (FK-safe order)
delete from public.product_embeddings
where metadata ->> 'source' = 'seed'
   or product_id in (
     'gid://shopify/Product/1001',
     'gid://shopify/Product/1002'
   );

-- Remove seed products
delete from public.products
where id in (
  'gid://shopify/Product/1001',
  'gid://shopify/Product/1002'
);

-- Remove demo idempotency row inserted by validation query
delete from public.sync_events
where event_id = 'evt-demo-1'
   or idempotency_key = 'pmcvp2-tv.myshopify.com:products/update:gid://shopify/Product/1001:2026-03-17T10:00:00Z';

commit;

-- Optional quick checks
-- select count(*) as product_count from public.products;
-- select count(*) as embedding_count from public.product_embeddings;
