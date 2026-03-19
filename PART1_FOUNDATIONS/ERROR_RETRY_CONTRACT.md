# Part 1 - Error Model and Retry Semantics

## Standard Error Shape
```json
{
  "trace_id": "tr_01...",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "variant_id is required",
    "details": {
      "field": "variant_id"
    },
    "retryable": false
  }
}
```

## Error Codes
- `VALIDATION_ERROR` -> 400
- `UNAUTHORIZED` -> 401
- `FORBIDDEN` -> 403
- `NOT_FOUND` -> 404
- `CONFLICT` -> 409
- `RATE_LIMITED` -> 429
- `UPSTREAM_TIMEOUT` -> 504
- `UPSTREAM_ERROR` -> 502
- `INTERNAL_ERROR` -> 500
- `IDEMPOTENT_REPLAY_SKIPPED` -> 200 (special success state)

## Retry Policy by Component

### Client/Widget -> Backend
- Retry only on: 429, 502, 503, 504
- Backoff: exponential (500ms, 1s, 2s) + jitter
- Max retries: 3

### n8n -> Backend Sync
- Retry on network timeout and 5xx
- Max retries: 5
- Backoff: exponential (1s, 2s, 4s, 8s, 16s)
- On final failure: write to DLQ (`sync_failures`) and alert

### Backend -> Azure OpenAI
- Retry on timeout/429/5xx
- Max retries: 3
- Respect upstream retry-after when provided

### Backend -> Supabase
- Retry on transient connection failures only
- Do not retry validation or constraint errors blindly

## Idempotency Rules
- Each sync event must have deterministic idempotency key:
  - `shop_domain + topic + product_id + occurred_at`
- If already processed, return success with `IDEMPOTENT_REPLAY_SKIPPED` semantics.

## Conflict Handling
- If out-of-order update arrives older than stored `updated_at`, ignore update and log as stale event.

## Safety Rules
- Never retry non-idempotent operation without idempotency guard.
- Never treat partial failures as full success.
