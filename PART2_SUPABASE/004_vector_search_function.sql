-- Part 2 / Step 4
-- Top-k vector retrieval with cosine distance and metadata filters

create or replace function public.match_products(
  query_embedding vector(3072),
  match_count integer default 12,
  min_price numeric default null,
  max_price numeric default null,
  required_tags text[] default null,
  in_stock_only boolean default true,
  variant_option_contains text default null,
  shop_domain_filter text default null
)
returns table (
  product_id text,
  title text,
  short_description text,
  price numeric,
  currency text,
  tags text[],
  inventory integer,
  variants jsonb,
  images jsonb,
  similarity double precision
)
language sql
stable
as $$
  select
    p.id as product_id,
    p.title,
    p.short_description,
    p.price,
    p.currency,
    p.tags,
    p.inventory,
    p.variants,
    p.images,
    1 - (pe.embedding <=> query_embedding) as similarity
  from public.product_embeddings pe
  join public.products p on p.id = pe.product_id
  where
    (shop_domain_filter is null or p.shop_domain = shop_domain_filter)
    and (min_price is null or p.price >= min_price)
    and (max_price is null or p.price <= max_price)
    and (
      required_tags is null
      or cardinality(required_tags) = 0
      or p.tags && required_tags
    )
    and (
      in_stock_only is false
      or p.inventory > 0
    )
    and (
      variant_option_contains is null
      or variant_option_contains = ''
      or p.variants::text ilike '%' || variant_option_contains || '%'
    )
  order by pe.embedding <=> query_embedding
  limit greatest(1, least(match_count, 50));
$$;
