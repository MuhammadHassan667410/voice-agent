# AI Shopify Assistant - Execution Tasks

Use this as the build checklist. Complete one part at a time, then stop for review/testing.

## Part 1 - Foundations and Contracts
Objective: Freeze contracts before coding integrations.

Tasks:
- [x] Confirm architecture decisions and constraints from AGENTS.md
- [x] Define API request/response schemas for all backend endpoints
- [x] Define Vapi tool input/output schemas
- [x] Define global error model and retry semantics
- [x] Define environment variables list
- [x] Define logging and trace-id convention

Done when:
- [x] All schema docs approved
- [x] No unresolved contract ambiguity remains

Test and review:
- [x] Manual payload walkthrough with sample requests

---

## Part 2 - Supabase Schema and Vector Retrieval
Objective: Build reliable persistence and search primitives.

Tasks:
- [x] Create products table
- [x] Create product_embeddings table
- [x] Create sync_events table for idempotency
- [x] Create sync_failures table for failed payloads
- [x] Enable pgvector and create cosine index
- [x] Implement top-k vector search SQL function
- [x] Implement metadata filtering strategy

Done when:
- [x] Migrations apply cleanly
- [x] Seed data searchable with expected ranking

Test and review:
- [x] Validate create/update/delete row behavior
- [x] Validate vector query output relevance

---

## Part 3 - FastAPI Backend Core
Objective: Expose secure, validated API layer.

Tasks:
- [x] Scaffold FastAPI app structure
- [x] Add config and env loading
- [x] Add search-products endpoint
- [x] Add product detail endpoint
- [x] Add filter-products endpoint
- [x] Add sync webhook endpoints (create/update/delete)
- [x] Add owner-protected reindex endpoint
- [x] Add standardized error handling middleware
- [x] Add logging + trace-id middleware

Done when:
- [x] All core endpoints return validated responses
- [x] Error surfaces are actionable and consistent

Test and review:
- [x] Endpoint smoke tests pass
- [x] Invalid payload tests return correct errors

---

## Part 4 - n8n Workflows
Objective: Make Shopify lifecycle drive vector store updates.

Tasks:
- [x] Workflow 1: Product Created
- [x] Workflow 2: Product Updated
- [x] Workflow 3: Product Deleted
- [x] Workflow 4: Owner Manual Reindex
- [x] Workflow 5: Failed Event Replay (DLQ)
- [x] Add webhook signature verification step
- [x] Add idempotency check step
- [x] Add conditional re-embed logic

Done when:
- [x] All workflows run with test payloads
- [x] Re-embed only on text-field changes

Test and review:
- [x] Create product -> embedding created
- [x] Update price only -> no re-embed
- [x] Update title/tags/short description -> re-embed
- [x] Delete product -> both rows removed

---

## Part 5 - Vapi Agent Setup
Objective: Voice agent reliably maps intent to safe tools.

Tasks:
- [x] Define Vapi assistant instructions
- [x] Register tool schemas
- [x] Implement backend tool handlers
- [x] Add clarification flow for variant/quantity
- [x] Add fallback behavior for unavailable products
- [x] Add response format validation

Done when:
- [x] Vapi responses always map to valid structured actions

Test and review:
- [x] Search voice test
- [x] Open product voice test
- [ ] Add/update/show cart voice tests
- [ ] Navigate voice test

---

## Part 6 - Shopify Widget and App Embed
Objective: Execute actions in storefront without full reload.

Tasks:
- [ ] Build floating football-themed launcher (all pages)
- [ ] Build widget panel state manager
- [ ] Build centralized action handler
- [ ] Integrate with backend APIs
- [ ] Integrate with Shopify cart/add.js, cart/change.js, cart.js
- [ ] Implement no-reload navigation using fetch + history API
- [ ] Ensure script isolation and no global collisions

Done when:
- [ ] Widget available across pages
- [ ] All actions update UI dynamically

Test and review:
- [ ] Home page flow
- [ ] Collection page flow
- [ ] Product page flow
- [ ] Cart page flow
- [ ] Browser refresh is never required for core interactions

---

## Part 7 - Security and Reliability
Objective: Production-safe behavior and easy recovery.

Tasks:
- [ ] Harden CORS and origin allowlist
- [ ] Add per-route rate limits
- [ ] Ensure secrets never leak to frontend
- [ ] Add retry/backoff policies
- [ ] Add DLQ replay controls
- [ ] Add audit logs for sync mutations

Done when:
- [ ] Security checklist passes
- [ ] Failure recovery path verified

Test and review:
- [ ] Simulate webhook failures and replay successfully
- [ ] Verify secret exposure checks

---

## Part 8 - Final QA and Launch
Objective: Confirm all business requirements from AGENTS.md.

Tasks:
- [ ] Run end-to-end test script
- [ ] Validate multi-user session isolation
- [ ] Validate no full page reload behavior
- [ ] Validate search relevance and cart correctness
- [ ] Prepare staging-to-production rollout checklist
- [ ] Prepare rollback checklist

Done when:
- [ ] All acceptance criteria pass
- [ ] Owner signoff complete

---

## Hard Rules During Build
- Do not skip parts.
- Stop after each part for testing and review.
- Keep architecture aligned with AGENTS.md.
- Never allow Vapi direct DB or DOM access.
- Never use vector DB as primary transactional DB.
