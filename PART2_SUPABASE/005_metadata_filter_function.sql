-- Part 2 / Step 5
-- Structured filter-only function (no embedding), useful for `/filter-products`

create or replace function public.filter_products(
  page_limit integer default 24,
  page_offset integer default 0,
  min_price numeric default null,
  max_price numeric default null,
  required_tags text[] default null,
  in_stock_only boolean default true,
  variant_option_contains text default null,
  sort_field text default 'updated_at',
  sort_order text default 'desc',
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
  updated_at timestamptz
)
language sql
stable
as $$
  with base as (
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
      p.updated_at
    from public.products p
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
  )
  select *
  from base
  order by
    case
      when sort_field = 'price' and lower(sort_order) = 'asc' then price
      else null
    end asc,
    case
      when sort_field = 'price' and lower(sort_order) = 'desc' then price
      else null
    end desc,
    case
      when sort_field = 'updated_at' and lower(sort_order) = 'asc' then updated_at
      else null
    end asc,
    case
      when sort_field = 'updated_at' and lower(sort_order) = 'desc' then updated_at
      else null
    end desc,
    updated_at desc
  limit greatest(1, least(page_limit, 100))
  offset greatest(0, page_offset);
$$;
