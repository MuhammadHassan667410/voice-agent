-- Optional seed data for local validation
-- Embedding vectors are dummy placeholders and should be replaced by real model outputs.

insert into public.products (
  id, shop_domain, handle, title, description, short_description, price, currency,
  images, variants, tags, inventory, status, vendor, product_type, source_created_at, source_updated_at
)
values
(
  'gid://shopify/Product/1001',
  'pmcvp2-tv.myshopify.com',
  'joma-top-flex-turf-shoes',
  'Joma Top Flex Turf Shoes',
  'Comfort turf shoes for daily training.',
  'Comfort turf shoes',
  79.00,
  'USD',
  '["https://example.com/joma-top-flex.jpg"]'::jsonb,
  '[{"variant_id":"gid://shopify/ProductVariant/2001","title":"US 9","price":79,"available":true}]'::jsonb,
  '{turf,shoes,football,joma}',
  40,
  'active',
  'Joma',
  'Footwear',
  now(),
  now()
),
(
  'gid://shopify/Product/1002',
  'pmcvp2-tv.myshopify.com',
  'adidas-tiro-23-track-jacket',
  'Adidas Tiro 23 Track Jacket',
  'Training jacket for football sessions.',
  'Training football jacket',
  95.00,
  'USD',
  '["https://example.com/tiro23.jpg"]'::jsonb,
  '[{"variant_id":"gid://shopify/ProductVariant/2002","title":"Large","price":95,"available":true}]'::jsonb,
  '{jacket,training,football,adidas}',
  110,
  'active',
  'Adidas',
  'Apparel',
  now(),
  now()
)
on conflict (id) do update
set
  title = excluded.title,
  short_description = excluded.short_description,
  price = excluded.price,
  images = excluded.images,
  variants = excluded.variants,
  tags = excluded.tags,
  inventory = excluded.inventory,
  updated_at = now();

-- Dummy vectors for schema verification only.
-- Replace these with model-generated 3072-d vectors in real runs.
insert into public.product_embeddings (product_id, embedding, embedding_input, metadata)
values
(
  'gid://shopify/Product/1001',
  ('[' || array_to_string(array_fill(0.001::float8, array[3072]), ',') || ']')::vector,
  'Joma Top Flex Turf Shoes Comfort turf shoes football turf',
  '{"source":"seed"}'::jsonb
),
(
  'gid://shopify/Product/1002',
  ('[' || array_to_string(array_fill(0.002::float8, array[3072]), ',') || ']')::vector,
  'Adidas Tiro 23 Track Jacket Training football jacket adidas',
  '{"source":"seed"}'::jsonb
)
on conflict (product_id) do update
set
  embedding = excluded.embedding,
  embedding_input = excluded.embedding_input,
  metadata = excluded.metadata,
  updated_at = now();
