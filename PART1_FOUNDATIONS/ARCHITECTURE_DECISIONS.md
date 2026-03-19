# Part 1 - Architecture Decisions (Frozen)

This file freezes Part 1 decisions so implementation can proceed without ambiguity.

## Core Technology
- Backend: FastAPI (Python, async)
- Database: Supabase Postgres + pgvector
- AI models (chat + embeddings): Azure OpenAI deployments
- Sync Layer: n8n workflows
- Voice Layer: Vapi assistant with backend tool calls
- Storefront Integration: Shopify Theme App Extension + App Embed Block

## Business Constraints (from AGENTS.md)
- Shopify is source of truth for products/variants/inventory.
- Vapi must never access DB directly.
- Vapi must never control DOM directly.
- Backend is only gateway for secrets and data intelligence.
- No full page reload for core user flows.
- Vector store is not a primary transactional database.

## Vector Store Rules
- Embed only: `title`, `short_description`, `tags`
- Never embed: `images`, `variants`, full product JSON
- Re-embed only on text field changes
- Delete embeddings when product is deleted

## Widget Rules
- Floating football-themed launcher appears on all storefront pages.
- Widget actions are strictly structured and handled by centralized action dispatcher.
- Cart API usage:
  - add: `/{locale}/cart/add.js`
  - update line: `/{locale}/cart/change.js`
  - read: `/{locale}/cart.js`

## Sync Rules
- Vector store mutation allowed only when owner-driven Shopify lifecycle events occur:
  - product create
  - product update
  - product delete
- Manual reindex is owner-triggered only.
- No autonomous mutation cron.

## Required n8n Workflows
1. Product Created
2. Product Updated
3. Product Deleted
4. Owner Manual Reindex
5. Failed Event Replay (DLQ)

## Default Retrieval Behavior
- Similarity: cosine
- Retrieve: top_k=12
- Return after post-filtering/ranking: 6 results by default
