# Part 1 - Backend API Contract

All endpoints return JSON.
All responses include `trace_id` at top-level for observability.

## 1) Search Products
### `POST /search-products`

Request:
```json
{
  "query": "turf shoes under 100",
  "filters": {
    "min_price": 0,
    "max_price": 100,
    "tags": ["turf", "nike"],
    "in_stock_only": true
  },
  "pagination": {
    "limit": 6,
    "offset": 0
  }
}
```

Response:
```json
{
  "trace_id": "tr_01...",
  "items": [
    {
      "id": "gid://shopify/Product/123",
      "title": "Joma Top Flex Turf Shoes",
      "short_description": "Lightweight turf shoes",
      "price": 79.0,
      "currency": "USD",
      "images": ["https://..."],
      "tags": ["turf", "shoes"],
      "inventory": 40,
      "variants": [
        {
          "variant_id": "gid://shopify/ProductVariant/999",
          "title": "US 9",
          "price": 79.0,
          "available": true
        }
      ],
      "score": 0.89
    }
  ],
  "page": {
    "limit": 6,
    "offset": 0,
    "total_estimate": 48
  }
}
```

## 2) Get Product
### `GET /product/{id}`

Response:
```json
{
  "trace_id": "tr_01...",
  "item": {
    "id": "gid://shopify/Product/123",
    "title": "Joma Top Flex Turf Shoes",
    "description": "...",
    "price": 79.0,
    "currency": "USD",
    "images": ["https://..."],
    "tags": ["turf", "shoes"],
    "inventory": 40,
    "variants": [
      {
        "variant_id": "gid://shopify/ProductVariant/999",
        "title": "US 9",
        "price": 79.0,
        "available": true
      }
    ],
    "updated_at": "2026-03-17T08:00:00Z"
  }
}
```

## 3) Filter Products
### `POST /filter-products`

Request:
```json
{
  "filters": {
    "min_price": 20,
    "max_price": 120,
    "tags": ["jersey"],
    "variant_option_contains": "large",
    "in_stock_only": true
  },
  "sort": {
    "field": "price",
    "order": "asc"
  },
  "pagination": {
    "limit": 24,
    "offset": 0
  }
}
```

Response shape is identical to `/search-products` with `items` and `page`.

## 4) Shopify Sync Endpoints (called by n8n)
### `POST /sync/shopify/product-created`
### `POST /sync/shopify/product-updated`
### `POST /sync/shopify/product-deleted`

Headers required:
- `X-Webhook-Topic`
- `X-Webhook-Event-Id`
- `X-Shopify-Hmac-Sha256`

Common request envelope:
```json
{
  "shop_domain": "pmcvp2-tv.myshopify.com",
  "event_id": "evt_...",
  "occurred_at": "2026-03-17T08:00:00Z",
  "payload": { "...shopify product payload...": true }
}
```

Common response:
```json
{
  "trace_id": "tr_01...",
  "status": "processed",
  "event_id": "evt_...",
  "embedding_action": "created_or_updated_or_skipped_or_deleted"
}
```

## 5) Owner Manual Reindex
### `POST /sync/reindex`

Request:
```json
{
  "scope": "all|ids",
  "product_ids": ["gid://shopify/Product/123"],
  "reason": "manual repair"
}
```

Response:
```json
{
  "trace_id": "tr_01...",
  "job_id": "reindex_...",
  "accepted": true
}
```

## 6) Health
### `GET /health`

Response:
```json
{
  "trace_id": "tr_01...",
  "status": "ok",
  "version": "0.1.0"
}
```

## 7) Cart Action Sequence (Explicit)

Cart mutations are **not** performed by n8n workflows.

Runtime sequence for cart actions:
1. User speaks to voice assistant in widget.
2. Vapi emits tool intent (`add_to_cart` or `update_cart`) to backend for validation/resolution.
3. Backend validates quantity, resolves/validates product + variant references, and returns structured action.
4. Widget executes Shopify Ajax Cart API in current shopper session:
  - add: `window.Shopify.routes.root + 'cart/add.js'`
  - update line: `window.Shopify.routes.root + 'cart/change.js'`
  - read cart: `window.Shopify.routes.root + 'cart.js'`
5. Widget updates cart UI/badge/panel without full page reload.

Boundary:
- n8n is only for product lifecycle sync (create/update/delete/reindex/replay).
- Cart add/update/show is handled in storefront session via widget + Shopify Ajax API.

## Validation Rules (global)
- Reject unknown enum values.
- Enforce strict type validation.
- Trim and normalize user query text.
- Cap limits (`limit <= 50`).
- Require positive integer quantity for cart intents.
