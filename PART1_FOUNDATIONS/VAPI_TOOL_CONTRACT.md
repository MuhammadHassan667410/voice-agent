# Part 1 - Vapi Tool Contract

Vapi is a planner and tool caller only.
Vapi must return structured actions for widget execution.

## Common Tool Response Envelope
```json
{
  "trace_id": "tr_01...",
  "action": {
    "type": "search_products|open_product|add_to_cart|update_cart|show_cart|navigate",
    "payload": {}
  },
  "speech": "Short user-facing response",
  "needs_clarification": false,
  "clarification_question": null
}
```

## Tool 1: `search_products(query)`
Input:
```json
{
  "query": "turf shoes",
  "filters": {
    "max_price": 100,
    "tags": ["turf"]
  }
}
```

Output action:
```json
{
  "type": "search_products",
  "payload": {
    "query": "turf shoes",
    "filters": { "max_price": 100, "tags": ["turf"] }
  }
}
```

## Tool 2: `open_product(product_id)`
Input:
```json
{
  "product_id": "gid://shopify/Product/123"
}
```

Output action:
```json
{
  "type": "open_product",
  "payload": {
    "product_id": "gid://shopify/Product/123"
  }
}
```

## Tool 3: `add_to_cart(product_id, variant_id, quantity)`
Input:
```json
{
  "product_id": "gid://shopify/Product/123",
  "variant_id": "gid://shopify/ProductVariant/999",
  "quantity": 2
}
```

Output action:
```json
{
  "type": "add_to_cart",
  "payload": {
    "product_id": "gid://shopify/Product/123",
    "variant_id": "gid://shopify/ProductVariant/999",
    "quantity": 2
  }
}
```

## Tool 4: `update_cart(line_id, variant_id, quantity)`
Input:
```json
{
  "line_id": "794864053:83503fd282...",
  "variant_id": "gid://shopify/ProductVariant/999",
  "quantity": 1
}
```

Output action:
```json
{
  "type": "update_cart",
  "payload": {
    "line_id": "794864053:83503fd282...",
    "variant_id": "gid://shopify/ProductVariant/999",
    "quantity": 1
  }
}
```

## Tool 5: `show_cart()`
Input:
```json
{}
```

Output action:
```json
{
  "type": "show_cart",
  "payload": {}
}
```

## Tool 6: `navigate(page)`
Input:
```json
{
  "page": "home|collection|product|cart|search",
  "url": "/collections/footwear"
}
```

Output action:
```json
{
  "type": "navigate",
  "payload": {
    "page": "collection",
    "url": "/collections/footwear"
  }
}
```

## Clarification Policy
Vapi must ask clarifying question if any required field is missing for action safety:
- Missing `variant_id` or size for add-to-cart
- Missing `quantity` for cart mutation
- Ambiguous product selection from multiple similar candidates

Example clarification envelope:
```json
{
  "trace_id": "tr_01...",
  "action": null,
  "speech": "I found two options. Do you want Nike Phantom GX or Joma Top Flex?",
  "needs_clarification": true,
  "clarification_question": "Which product do you want?"
}
```

## Prohibited Behavior
- No direct DOM command generation.
- No SQL or DB-level operation requests.
- No catalog mutation actions.

## Cart Execution Responsibility (Explicit)
- Vapi plans and emits structured cart actions only.
- Backend validates and normalizes cart intent payloads.
- Widget executes cart operations in the shopper session using Shopify Ajax API.
- n8n does not handle cart add/update/show actions.

Sequence for cart mutation:
1. Vapi -> backend tool intent (`add_to_cart` or `update_cart`)
2. Backend -> structured action response
3. Widget -> `cart/add.js` or `cart/change.js`
4. Widget -> `cart.js` refresh for current state rendering
