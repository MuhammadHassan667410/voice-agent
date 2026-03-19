# AI Shopify Assistant - Full Implementation Guide

## 1) Project Goal
Build a production-grade AI shopping assistant for Shopify with:
- Semantic product search (RAG)
- Voice interaction through Vapi
- Dynamic frontend updates without full page reload
- Cart operations (add/update/show)
- Real-time product sync from Shopify to Supabase vector store

This guide follows the system rules defined in AGENTS.md and the decisions finalized during planning.

---

## 2) Locked Architecture Decisions

### Core Stack
- Backend: FastAPI (Python, async)
- Database: Supabase Postgres + pgvector
- AI Models (chat + embeddings): Azure OpenAI deployments
- Sync Orchestration: n8n
- Voice Agent Layer: Vapi
- Frontend Integration: Shopify Theme App Extension (App Embed Block) + lightweight JS widget

### Non-Negotiable Rules
- Shopify is source of truth for products, variants, and inventory.
- Vapi never accesses database directly.
- Vapi never controls DOM directly.
- Backend is the only gateway to AI, database, and server-side secrets.
- No full page reload for widget-driven UX.
- Vector embeddings only include: title, short description, tags.
- Do not embed: images, variants, full product JSON.

---

## 3) System Modules and Responsibilities

## Module A - Shopify Data Sync (n8n)
Purpose: Keep Supabase in sync with Shopify product lifecycle events.

Build 5 workflows:
1. Product Created
2. Product Updated
3. Product Deleted
4. Manual Reindex (owner-triggered)
5. Failed Event Replay (DLQ)

Rules:
- Create: upsert products + create embedding row
- Update: re-embed only when text fields changed
- Delete: remove from both products and embeddings
- No autonomous cron mutation of vector store
- Only owner actions in Shopify (or owner-triggered reindex) can update vector store state

## Module B - Backend API (FastAPI)
Purpose: Secure orchestration layer for frontend widget and Vapi tools.

Required endpoints:
- POST /search-products
- GET /product/{id}
- POST /filter-products
- POST /vapi/tool/search_products
- POST /vapi/tool/open_product
- POST /vapi/tool/add_to_cart_intent
- POST /vapi/tool/update_cart_intent
- POST /vapi/tool/show_cart_intent
- POST /vapi/tool/navigate_intent
- POST /sync/shopify/product-created
- POST /sync/shopify/product-updated
- POST /sync/shopify/product-deleted
- POST /sync/reindex (owner protected)

Notes:
- Widget uses backend for search/product intelligence.
- Widget uses Shopify Ajax Cart API on storefront session for cart state mutations.
- Backend validates and normalizes all Vapi tool outputs.

## Module C - Supabase Data Layer
Purpose: Durable store for catalog data and vector retrieval.

Core tables:
- products
- product_embeddings
- sync_events (idempotency and replay safety)
- sync_failures (DLQ tracking)

Indexes and functions:
- pgvector similarity index (cosine)
- SQL function for top-k vector search
- optional materialized metadata projection for filters

## Module D - Vapi Agent
Purpose: Conversational planner that calls approved tools and returns structured actions.

Allowed tools:
- search_products(query)
- open_product(product_id)
- add_to_cart(product_id, variant_id, quantity)
- update_cart(line_id, variant_id, quantity)
- show_cart()
- navigate(page)

Behavior:
- Clarify missing size/color/quantity before cart actions
- Never fabricate unavailable variants
- Return deterministic action payloads for widget action handler

## Module E - Shopify Frontend Widget
Purpose: Storefront UI/UX execution layer.

Responsibilities:
- Floating football-themed launcher on all pages
- Capture voice/text interaction
- Execute structured actions from Vapi/backend
- Update UI and route state without full reload
- Call locale-aware Shopify Ajax endpoints:
  - cart/add.js for add
  - cart/change.js for line update/removal
  - cart.js for read

---

## 4) Build Sequence (Part-by-Part)

## Part 1 - Foundations and Contracts
Deliverables:
- Final request/response schemas for backend and Vapi tools
- Error model and status code conventions
- Environment variable contract
- Local runbook

Review Gate:
- You approve schemas and naming before implementation of persistence.

## Part 2 - Supabase Schema + Retrieval Layer
Deliverables:
- SQL migrations
- pgvector setup
- vector similarity query function
- idempotency and sync status tables

Review Gate:
- Validate search quality on seeded sample products.

## Part 3 - FastAPI Core + Search Endpoints
Deliverables:
- FastAPI project scaffold
- search, product, filter endpoints
- embedding pipeline integration
- structured logging and error handling

Review Gate:
- Postman/curl smoke tests and latency check.

## Part 4 - n8n Sync Workflows
Deliverables:
- 5 workflows defined and imported
- webhook verification
- create/update/delete + reindex + DLQ replay

Review Gate:
- Trigger test events from Shopify admin and verify DB state transitions.

## Part 5 - Vapi Agent Configuration
Deliverables:
- Vapi prompt/system instruction
- Tool schema registration
- fallback and retry dialogue behavior

Review Gate:
- Voice test runs for search/add/update/show/navigate.

## Part 6 - Shopify Widget + Theme App Embed
Deliverables:
- App embed install path
- floating launcher and panel
- action dispatcher wired to backend and cart API
- no-reload navigation behavior

Review Gate:
- Manual storefront QA across home, collection, product, cart pages.

## Part 7 - Reliability, Security, and Observability
Deliverables:
- request tracing IDs
- sync failure replay controls
- rate limiting and abuse protection
- secrets hardening and CORS policy

Review Gate:
- Fault-injection tests and recovery validation.

## Part 8 - End-to-End Validation + Launch Readiness
Deliverables:
- test evidence for all AGENTS.md requirements
- deployment checklist and rollback plan
- handoff docs updated

Review Gate:
- Final signoff for production rollout.

---

## 5) Data and Sync Rules (Exact)

### Re-Embedding Decision Matrix
- Product create: embed yes
- Product update with title/short description/tags changed: embed yes
- Product update with only price/inventory/images/variants changed: embed no
- Product delete: remove embedding

### Idempotency Strategy
- Use unique event key from Shopify webhook topic + product id + updated_at/event timestamp
- Skip already-processed events
- Persist processing result and timestamp in sync_events

### Failure Strategy
- On transient failure: retry with exponential backoff
- On persistent failure: move payload to sync_failures
- Replay manually via owner-approved workflow

---

## 6) Acceptance Criteria (Project Success)
Project is successful only when all are true:
- Search returns relevant football products from embeddings.
- Product open action resolves full product detail correctly.
- Add to cart works from agent flows.
- Update cart works for specific line items.
- Navigation occurs without full page reload.
- Multi-user sessions remain isolated.
- Vector store updates only from owner-triggered Shopify product lifecycle changes.

---

## 7) Recommended Environment Progression
1. Local development
2. Staging with real Shopify dev theme
3. Production deployment

Promotion rule:
- Do not promote a part unless its review gate is passed.

---

## 8) Handoff Mode for Other AI Agents
To onboard another AI agent quickly:
1. Read AGENTS.md
2. Read AI_AGENT_HANDOFF.md
3. Execute parts strictly in order from TASKS.md
4. Stop after each part for human review
5. Do not skip sync and security gates

This ensures any AI coding agent can continue with minimal ambiguity.
