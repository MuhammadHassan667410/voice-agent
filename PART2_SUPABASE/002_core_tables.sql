-- Part 2 / Step 2
-- Core tables for product projection, embeddings, idempotency, and DLQ

create table if not exists public.products (
  id text primary key,
  shop_domain text not null,
  handle text,
  title text not null,
  description text,
  short_description text,
  price numeric(12,2) not null default 0,
  currency text not null default 'USD',
  images jsonb not null default '[]'::jsonb,
  variants jsonb not null default '[]'::jsonb,
  tags text[] not null default '{}',
  inventory integer not null default 0,
  status text,
  vendor text,
  product_type text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  source_created_at timestamptz,
  source_updated_at timestamptz,
  metadata jsonb not null default '{}'::jsonb
);

create table if not exists public.product_embeddings (
  id uuid primary key default gen_random_uuid(),
  product_id text not null references public.products(id) on delete cascade,
  embedding vector(3072) not null,
  embedding_input text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (product_id)
);

create table if not exists public.sync_events (
  id uuid primary key default gen_random_uuid(),
  idempotency_key text not null unique,
  event_topic text not null,
  event_id text,
  shop_domain text not null,
  product_id text,
  event_occurred_at timestamptz,
  received_at timestamptz not null default now(),
  processed_at timestamptz,
  status text not null,
  embedding_action text,
  payload jsonb not null,
  error_message text,
  trace_id text
);

create table if not exists public.sync_failures (
  id uuid primary key default gen_random_uuid(),
  idempotency_key text not null,
  event_topic text not null,
  event_id text,
  shop_domain text not null,
  product_id text,
  failed_at timestamptz not null default now(),
  retry_count integer not null default 0,
  next_retry_at timestamptz,
  payload jsonb not null,
  error_message text not null,
  status text not null default 'pending',
  trace_id text
);
