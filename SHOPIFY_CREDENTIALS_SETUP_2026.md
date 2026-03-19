# Shopify Credentials Setup (2026) for This Project

This guide is tailored to this repo architecture (FastAPI backend + n8n + Shopify webhooks + storefront widget).

## 1) Credentials used in this project

## Required now
- `SHOPIFY_STORE_DOMAIN`
- `SHOPIFY_ADMIN_ACCESS_TOKEN`
- `SHOPIFY_WEBHOOK_SECRET`
- `SHOPIFY_API_VERSION`

## Optional (only if using OAuth/public app patterns)
- `SHOPIFY_API_KEY`
- `SHOPIFY_API_SECRET`

---

## 2) Where to create the app in 2026
Shopify docs indicate app development is centered in the Dev Dashboard, and creating new legacy custom apps in admin is restricted as of Jan 1, 2026.

For this project, use one of these:
1. **Dev Dashboard / Partner flow (recommended for future-proofing)**
2. Existing admin-created custom app (if already available)

Either way, you need Admin API token + webhook verification secret.

---

## 3) How to get each credential

## A) `SHOPIFY_STORE_DOMAIN`
From your store URL:
- Example: `pmcvp2-tv.myshopify.com`

No protocol, no path.

## B) `SHOPIFY_ADMIN_ACCESS_TOKEN`
Path (common flow):
1. Open Shopify Admin.
2. Go to Apps (or Dev Dashboard app settings for your app).
3. Open your app.
4. Configure Admin API scopes (minimum for this project below).
5. Install/reinstall app to store.
6. Copy **Admin API access token**.

Use in backend as `X-Shopify-Access-Token` for Admin GraphQL/REST calls.

## C) `SHOPIFY_WEBHOOK_SECRET`
For webhook HMAC verification, use the app’s signing secret/client secret from app credentials.

Path:
1. Open your app’s API credentials page.
2. Find the secret used for webhook HMAC signing.
3. Copy it and store as `SHOPIFY_WEBHOOK_SECRET`.

Important:
- Verify incoming `X-Shopify-Hmac-SHA256` using the raw request body and this secret.
- HMAC can take time to fully switch after secret rotation.

## D) `SHOPIFY_API_VERSION`
Use a fixed version in `.env` (for consistency and reproducibility).
- Current project default: `2026-01`

Admin GraphQL endpoint pattern:
- `https://{shop}.myshopify.com/admin/api/{version}/graphql.json`

## E) `SHOPIFY_API_KEY` and `SHOPIFY_API_SECRET` (optional)
Needed when implementing OAuth/public app flows or Shopify CLI app auth features.
If you are only using an installed custom/internal app token flow for backend calls, these may remain unused.

---

## 4) Minimum scopes for this project

For current phases (catalog sync + read/search):
- `read_products`
- `read_inventory`

If you later write catalog data (not planned currently):
- `write_products`

Only request least privilege.

---

## 5) Webhooks you need (Part 4)
Create subscriptions for:
- `products/create`
- `products/update`
- `products/delete`

Delivery target:
- your n8n webhook endpoint OR backend sync endpoint

Webhook handling requirements:
- return 2xx quickly
- validate HMAC signature
- queue/process asynchronously for resilience

---

## 6) Add to `.env`
Use these keys in `.env`:

```env
SHOPIFY_STORE_DOMAIN=pmcvp2-tv.myshopify.com
SHOPIFY_ADMIN_ACCESS_TOKEN=
SHOPIFY_WEBHOOK_SECRET=
SHOPIFY_API_VERSION=2026-01
SHOPIFY_API_KEY=
SHOPIFY_API_SECRET=
```

Never expose these in storefront JS.

---

## 7) Quick verification

## Verify Admin token
Run a simple products query against Admin GraphQL endpoint using `X-Shopify-Access-Token`.
If token/scopes are valid, you get product data.

## Verify webhook secret
Send a test webhook from app/webhook UI and ensure HMAC verification passes in backend/n8n.

## Verify API version
Ensure requests use the exact version in env (e.g. `2026-01`) and return expected schema.

---

## 8) Rotation notes
- If credentials/tokens are regenerated, update `.env` immediately.
- Reinstall app if scope changes require token regeneration.
- Keep secrets only in backend or secrets manager.
