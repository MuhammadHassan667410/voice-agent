# Part 5 - Vapi Setup Guide (Server URL + Credentials)

This guide answers two critical questions:
1. What URL should I put in each Vapi tool?
2. Where do credentials live (Vapi vs backend)?

## 1) Credential Model (Important)

Use this separation:

- Vapi stores:
  - Vapi assistant/tool config
  - Tool server URLs
  - Optional Vapi webhook credentials (`credentialId`)
- Backend stores (never in Vapi):
  - Supabase credentials (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`)
  - Azure/OpenAI keys
  - Shopify secrets

Why: Vapi should call only your backend endpoints. Your backend is the secure gateway to Supabase and all private services.

## 2) What Server URL To Put In Vapi Tools

Set a public backend base URL (ngrok, cloud domain, etc.).

Example base URL:
- `https://your-public-backend.ngrok-free.app`

Then tool URLs become:
- `https://your-public-backend.ngrok-free.app/vapi/tool/search_products`
- `https://your-public-backend.ngrok-free.app/vapi/tool/open_product`
- `https://your-public-backend.ngrok-free.app/vapi/tool/add_to_cart_intent`
- `https://your-public-backend.ngrok-free.app/vapi/tool/update_cart_intent`
- `https://your-public-backend.ngrok-free.app/vapi/tool/show_cart_intent`
- `https://your-public-backend.ngrok-free.app/vapi/tool/navigate_intent`

## 3) Where To Configure In Vapi Dashboard

For custom tools:
1. Open `Tools` in Vapi dashboard.
2. Create or edit tool.
3. Tool type: `Function`.
4. Set function name + input schema.
5. Set `Server URL` to the matching backend endpoint above.
6. Add tool messages (request start/failed/delayed) for better voice UX.

Then attach tools to assistant:
1. Open your Assistant.
2. Go to Tools tab.
3. Add the tool(s).
4. Save and publish.

## 4) Server URL Priority (Official Behavior)

Vapi server URL priority is:
1. Function tool level
2. Assistant level
3. Phone number level
4. Account-wide level

For tool calls, function-level server URL is recommended because it is the most explicit and avoids routing confusion.

## 5) Local Development and ngrok

- Run backend locally.
- Start ngrok tunnel to backend port.
- Use the current ngrok HTTPS URL as tool server URL.
- If ngrok URL changes, update tool URLs in Vapi dashboard.

Tip: use static ngrok domain (paid ngrok feature) to avoid repeated URL edits.

## 6) Production Recommendation

Move from ngrok to a stable HTTPS backend domain and keep tool URLs fixed.

## 7) Vapi Response/Tool Call Format Note

For custom tool webhooks, Vapi sends tool call payload to your server URL. Your server should return tool results in Vapi-compatible response format. In this project, we return a structured action envelope from backend endpoints for the widget execution pipeline.

## 8) Quick Checklist

- [ ] Backend public URL is reachable from internet
- [ ] Each Vapi tool server URL points to correct `/vapi/tool/*` endpoint
- [ ] No Supabase credentials inside Vapi config
- [ ] Assistant has all required tools attached
- [ ] Calls tested for search/open/add/update/show/navigate
