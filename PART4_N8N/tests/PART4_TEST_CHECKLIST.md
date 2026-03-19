# Part 4 Test Checklist (n8n)

Use this checklist after importing all workflows from `PART4_N8N/workflows`.

## Pre-checks
- [ ] Backend API running and reachable at `BACKEND_BASE_URL`
- [ ] n8n env vars set: `BACKEND_BASE_URL`, `SHOPIFY_STORE_DOMAIN`, `SHOPIFY_WEBHOOK_SECRET`, `REINDEX_ADMIN_TOKEN`
- [ ] Shopify webhooks point to n8n webhook URLs:
  - `products/create` -> `/webhook/shopify/product-created`
  - `products/update` -> `/webhook/shopify/product-updated`
  - `products/delete` -> `/webhook/shopify/product-deleted`

## Test 1 - Product Create
- [ ] Create a product in Shopify admin
- [ ] n8n created workflow receives request and verifies signature
- [ ] Backend returns `status=processed`
- [ ] Product row exists in Supabase
- [ ] Embedding row exists in Supabase (`embedding_action=created`)

## Test 2 - Price-only update
- [ ] Update only price/inventory/images/variants
- [ ] Updated workflow runs and passes idempotency check
- [ ] Backend returns `embedding_action=skipped` (or structured-only behavior)

## Test 3 - Text update
- [ ] Update title and/or short description and/or tags
- [ ] Updated workflow marks text change path
- [ ] Backend returns `embedding_action=updated`

## Test 4 - Product delete
- [ ] Delete product in Shopify
- [ ] Deleted workflow triggers backend delete endpoint
- [ ] Product row removed
- [ ] Embedding row removed (`embedding_action=deleted`)

## Test 5 - Manual reindex
- [ ] Trigger `/webhook/owner/manual-reindex` with `{ "scope": "all" }`
- [ ] Backend accepts with `accepted=true` and returns `job_id`

## Test 6 - DLQ replay
- [ ] Put one or more failed events in `DLQ_REPLAY_EVENTS_JSON`
- [ ] Run `5_failed_event_replay_dlq` manually
- [ ] Events replay to proper backend endpoint by topic

## Test 7 - Idempotency protection
- [ ] Re-send same webhook payload with same event id
- [ ] Workflow marks duplicate and does not mutate state twice

## Exit Criteria for Part 4
- [ ] All five workflows execute without node errors
- [ ] Signature verification passes on valid events and fails on tampered events
- [ ] Idempotency check blocks duplicates
- [ ] Re-embed happens only for text-field changes
