# Part 1 - Manual Payload Walkthrough

Use this file for Part 1 review before coding begins.

## A) Search Flow
Request:
```json
{
  "query": "adidas track jacket",
  "filters": {
    "max_price": 150,
    "in_stock_only": true
  },
  "pagination": {
    "limit": 6,
    "offset": 0
  }
}
```
Expected checks:
- query accepted and normalized
- pagination limit validation applied
- response includes `trace_id`, `items`, `page`

## B) Product Detail Flow
Request path:
`GET /product/gid://shopify/Product/123`

Expected checks:
- 404 when ID does not exist
- full product object shape when exists

## C) Sync Update Flow (non-text fields)
Input event:
- topic: product update
- changed fields: inventory only

Expected checks:
- product row updated
- embedding row unchanged
- response `embedding_action = skipped`

## D) Sync Update Flow (text fields)
Input event:
- topic: product update
- changed fields: title/tags

Expected checks:
- product row updated
- embedding regenerated
- response `embedding_action = updated`

## E) Vapi Clarification Flow
Input:
```json
{
  "intent": "add_to_cart",
  "product_name": "phantom gx",
  "quantity": 1
}
```
Expected checks:
- if variant/size missing, response uses `needs_clarification = true`
- no cart mutation action emitted before clarification

## F) Error Contract Validation
Input:
- invalid quantity = 0 for add_to_cart

Expected checks:
- status code 400
- `error.code = VALIDATION_ERROR`
- `retryable = false`
- includes `trace_id`

## G) Idempotency Behavior
Input:
- same Shopify event replayed twice

Expected checks:
- first event processed normally
- second event returns idempotent skip success state
- both operations logged with same event key

## Signoff Checklist
- [ ] API contract accepted
- [ ] Vapi tool contract accepted
- [ ] Error/retry model accepted
- [ ] Env contract accepted
- [ ] Logging and trace contract accepted
