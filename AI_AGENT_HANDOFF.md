# AI Agent Handoff File

Purpose: This file gives any coding agent complete context to continue implementation without follow-up questions.

## Project Identity
- Project: AI Shopify Assistant for football gear store
- Store: pmcvp2-tv.myshopify.com
- Primary objective: Voice + semantic shopping assistant with no full-page reload interactions

## Source of Truth
- Shopify is source of truth for products and inventory.
- AGENTS.md is authoritative for business behavior and system boundaries.

## Locked Decisions
- Backend: FastAPI
- AI provider: Azure OpenAI (chat + embeddings via deployment names)
- Embeddings model family: text-embedding-3-large
- Vector similarity: cosine
- Widget placement: floating football-themed launcher on all pages
- Frontend cart endpoints: cart/add.js, cart/change.js, cart.js
- Integration strategy: Theme App Extension + App Embed Block

## Critical Constraints
- Vapi cannot access DB directly.
- Vapi cannot manipulate DOM directly.
- Backend is only gateway for secrets and data intelligence.
- No full page reload for core interactions.
- Embedding fields only: title, short description, tags.
- Never embed images, variants, or full JSON.

## Required Output Modules
1. Backend API
2. Supabase schema
3. n8n workflows
4. Vapi config
5. Frontend widget

## n8n Workflow Contract (Must Implement All)
1. Product Created
2. Product Updated
3. Product Deleted
4. Owner Manual Reindex
5. Failed Event Replay (DLQ)

Vector store mutation policy:
- Update only through owner-driven Shopify product lifecycle events and explicit owner reindex.
- No independent periodic mutating sync.

## Re-Embedding Rules
- Re-embed on create.
- Re-embed on update only if text fields changed (title, short description, tags).
- Structured-only update for non-text field changes.
- Remove embedding on delete.

## Backend Contract Summary
Core endpoints:
- POST /search-products
- GET /product/{id}
- POST /filter-products

Sync endpoints:
- POST /sync/shopify/product-created
- POST /sync/shopify/product-updated
- POST /sync/shopify/product-deleted
- POST /sync/reindex

Vapi tool endpoints:
- search_products
- open_product
- add_to_cart
- update_cart
- show_cart
- navigate

## Frontend Contract Summary
- Floating launcher across all pages
- Central action handler executes structured actions
- Uses fetch + history API + DOM replacement
- Uses locale-aware cart routes through window.Shopify.routes.root

## Acceptance Criteria
- Search returns relevant products.
- Open product shows correct detail.
- Add/update cart operations work reliably.
- Navigation works without full reload.
- Multi-user state isolation works.
- Vector store updates only from approved lifecycle events.

## Execution Order
- Follow TASKS.md in strict phase order.
- Stop after each part for human testing and approval.
- Do not start next part until review gate passes.

## Risk Controls
- Idempotency keys for webhook events
- Exponential retry + DLQ for failed sync events
- Structured logging with trace IDs
- Strict payload validation on all external boundaries

## Credentials Reference
- See API_KEYS_AND_CREDENTIALS_GUIDE.md for setup and required environment variables.

## Definition of Done
Project is done only when all modules are implemented, all review gates pass, and acceptance criteria from AGENTS.md are fully satisfied.
