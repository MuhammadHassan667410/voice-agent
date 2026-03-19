# Part 1 - Environment Variable Contract

Use separate env sets per environment: local, staging, production.

## Required Variables

### App
- `APP_ENV` = local|staging|production
- `APP_NAME` = ai-shopify-assistant
- `APP_BASE_URL` = backend public URL
- `LOG_LEVEL` = DEBUG|INFO|WARN|ERROR
- `CORS_ALLOWED_ORIGINS` = comma-separated storefront origins

### Shopify
- `SHOPIFY_STORE_DOMAIN`
- `SHOPIFY_WEBHOOK_SECRET`
- `SHOPIFY_ADMIN_ACCESS_TOKEN` (backend/n8n only)
- `SHOPIFY_API_VERSION` (example: 2026-01)

### Supabase
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (frontend-safe only when needed)
- `SUPABASE_SERVICE_ROLE_KEY` (backend only)
- `SUPABASE_DB_SCHEMA` (default: public)

### Azure OpenAI
- `AZURE_OPENAI_ENDPOINT` (example: https://your-resource.openai.azure.com)
- `AZURE_OPENAI_API_KEY`
- `OPENAI_API_VERSION` (set to your supported Azure OpenAI API version)
- `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` (your chat model deployment name)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` (your embedding deployment name)

### Vapi
- `VAPI_API_KEY`
- `VAPI_ASSISTANT_ID`
- `VAPI_WEBHOOK_SECRET` (if callbacks enabled)

### n8n
- `N8N_BASE_URL`
- `N8N_API_KEY` (if using workflow automation)
- `SYNC_SHARED_TOKEN` (optional shared secret between n8n and backend)

## Optional Variables
- `DEFAULT_SEARCH_TOP_K` (default 12)
- `DEFAULT_RETURN_COUNT` (default 6)
- `REQUEST_TIMEOUT_MS` (default 10000)
- `RATE_LIMIT_PER_MINUTE`

## Security Requirements
- Never expose service keys in storefront JS.
- Keep production keys isolated from local/staging.
- Use secret manager or CI secrets, never commit to source control.
