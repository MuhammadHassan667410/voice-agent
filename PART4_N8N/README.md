# Part 4 - n8n Workflows (Shopify Sync)

This folder contains the five required n8n workflows for Part 4:
1. Product Created
2. Product Updated
3. Product Deleted
4. Owner Manual Reindex
5. Failed Event Replay (DLQ)

Also included:
- `0_initial_shopify_backfill.json` for one-time import of products that already exist in Shopify.

## Required n8n Environment Variables
Set these in n8n before importing/running workflows:

- `BACKEND_BASE_URL` (example: `http://127.0.0.1:8000`)
- `SHOPIFY_STORE_DOMAIN` (example: `pmcvp2-tv.myshopify.com`)
- `SHOPIFY_WEBHOOK_SECRET`
- `REINDEX_ADMIN_TOKEN`
- `SHOPIFY_ADMIN_API_BASE_URL` (example: `https://pmcvp2-tv.myshopify.com/admin/api/2025-01`)
- `SHOPIFY_ADMIN_ACCESS_TOKEN`

Free-trial note:
- If n8n External Secrets/Variables are unavailable on your plan, use the included free-tier workflow placeholders instead.
- Replace placeholder values directly in imported nodes:
   - `__SHOPIFY_WEBHOOK_SECRET__`
   - `__SHOPIFY_STORE_DOMAIN__`
   - `__SHOPIFY_ADMIN_API_BASE_URL__`
   - `__SHOPIFY_ADMIN_ACCESS_TOKEN__`
   - `__REINDEX_ADMIN_TOKEN__`
   - `__DLQ_REPLAY_EVENTS_JSON__`
- Backend URLs are already set to:
   - `https://rollicking-overcredulously-dalila.ngrok-free.dev`

## Common Header Mapping (Shopify -> n8n)
For Shopify webhook flows, map these headers from webhook request:

- `X-Shopify-Topic`
- `X-Shopify-Shop-Domain`
- `X-Shopify-Hmac-Sha256`
- `X-Shopify-Webhook-Id`

## Shared Workflow Pattern
Use this sequence in Product Created/Updated/Deleted workflows:

1. `Webhook` node (POST)
2. `Code: VerifySignatureAndEnvelope`
   - Validates `X-Shopify-Hmac-Sha256` against `SHOPIFY_WEBHOOK_SECRET`
   - Builds backend `SyncEnvelope` payload
3. `Code: IdempotencyCheck`
   - Uses event id from `X-Shopify-Webhook-Id` (fallback derived key)
   - Skips duplicate events inside n8n execution path
4. Optional branching logic (updated flow only):
   - `Code: TextChangeDecision` for title/short_description/tags comparison
5. `HTTP Request` node to backend sync endpoint
6. `Respond to Webhook` node with status/result

## Backend Endpoints Used
- `POST /sync/shopify/product-created`
- `POST /sync/shopify/product-updated`
- `POST /sync/shopify/product-deleted`
- `POST /sync/reindex`

All sync requests should include headers:
- `Content-Type: application/json`
- `X-Webhook-Topic`
- `X-Webhook-Event-Id`

`/sync/reindex` also requires:
- `X-Admin-Token: {{REINDEX_ADMIN_TOKEN}}`

## Workflow Files
- `workflows/0_initial_shopify_backfill.json`
- `workflows/1_product_created.json`
- `workflows/2_product_updated.json`
- `workflows/3_product_deleted.json`
- `workflows/4_owner_manual_reindex.json`
- `workflows/5_failed_event_replay_dlq.json`

## How n8n Connects to Shopify
1. In Shopify admin, create/configure your custom app and grant product read scopes.
2. Copy `Admin API access token` into n8n as `SHOPIFY_ADMIN_ACCESS_TOKEN`.
3. Set `SHOPIFY_ADMIN_API_BASE_URL` to your store admin REST API base URL.
4. Configure Shopify webhooks to n8n webhook URLs:
   - `products/create` -> `/webhook/shopify/product-created`
   - `products/update` -> `/webhook/shopify/product-updated`
   - `products/delete` -> `/webhook/shopify/product-deleted`
5. Copy Shopify webhook signing secret to `SHOPIFY_WEBHOOK_SECRET` in n8n.

## Existing Products (Before Webhooks)
Shopify webhooks only send future changes. To embed products already in your store:
1. Import and run `workflows/0_initial_shopify_backfill.json` once.
2. This pulls active products from Shopify (first 250) and pushes each product through backend `product-created` sync path.
3. After backfill completes, enable created/updated/deleted webhook workflows for ongoing sync.

If your store has more than 250 products, run this workflow in multiple passes (or extend it with pagination by `since_id`).

## Notes
- Backend already applies strict idempotency and embedding decisions; n8n mirrors those controls for defense in depth.
- If your n8n instance stores webhook payload differently, adjust each `Code` node field extraction (`body`, `headers`, `rawBody`) accordingly.
- Use the checklist in `tests/PART4_TEST_CHECKLIST.md` before marking Part 4 done.
