# API Keys and Credentials Guide

This guide covers all required services, what credentials are needed, how to get them, and where each credential is used.

## 1) Required Services
- Shopify store + Shopify Admin access
- Supabase project
- Azure OpenAI resource (for chat + embeddings)
- Vapi account
- n8n instance (cloud or self-hosted)

---

## 2) Credential Inventory

## Shopify
Needed:
- SHOPIFY_STORE_DOMAIN (example: pmcvp2-tv.myshopify.com)
- SHOPIFY_ADMIN_ACCESS_TOKEN (for server-side product sync calls if needed)
- SHOPIFY_API_KEY and SHOPIFY_API_SECRET (if using custom app OAuth flows)
- SHOPIFY_WEBHOOK_SECRET (for webhook signature validation)

Used by:
- n8n webhook and admin API integration
- Backend webhook verification and optional admin requests

## Supabase
Needed:
- SUPABASE_URL
- SUPABASE_ANON_KEY (frontend-safe only when strictly needed)
- SUPABASE_SERVICE_ROLE_KEY (backend only)
- SUPABASE_DB_PASSWORD (if direct SQL/migrations use password auth)

Used by:
- Backend data read/write
- Migrations and vector index setup
- Sync workflow persistence

## Azure OpenAI
Needed:
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_KEY
- OPENAI_API_VERSION
- AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME

Used by:
- Backend chat and embedding generation

## Vapi
Needed:
- VAPI_API_KEY (server-side management)
- VAPI_ASSISTANT_ID
- VAPI_PHONE_NUMBER_ID (if phone channel is used)
- Optional public/session token setup for widget runtime (depends on chosen Vapi integration pattern)

Used by:
- Voice assistant configuration
- Tool routing to backend

## n8n
Needed:
- N8N_WEBHOOK_BASE_URL
- N8N_API_KEY (if automating workflow import/deploy)
- Internal credentials for HTTP nodes (Shopify, Backend, Supabase)

Used by:
- Product create/update/delete orchestration
- replay and reindex workflows

---

## 3) How to Get Each Credential

## Shopify Credentials
1. Open Shopify Admin.
2. Go to Apps > App and sales channel settings.
3. Create a custom app for this project.
4. Grant minimum scopes required for product read and webhook operations.
5. Install app to store.
6. Copy Admin API access token.
7. In app settings, configure webhooks for product create/update/delete and copy webhook signing secret.

Recommended webhook topics:
- products/create
- products/update
- products/delete

## Supabase Credentials
1. Create project in Supabase dashboard.
2. Open Project Settings > API.
3. Copy Project URL, anon key, service role key.
4. Open Database settings and record connection parameters if using direct migration tooling.

## Azure OpenAI Credentials
1. Open Azure portal and select your Azure OpenAI resource.
2. From Keys and Endpoint, copy endpoint and API key.
3. From Model Deployments, record deployment names for chat and embedding models.
4. Record the API version used by your SDK/integration.
5. Store all values in backend secret manager only.

## Vapi Credentials
1. Open Vapi dashboard.
2. Create assistant.
3. Configure model, instructions, and tool endpoints.
4. Copy assistant id and API key (server-side use only).
5. Copy Vapi public key for browser widget use.
5. If using telephony, configure and capture phone number id.

## n8n Credentials
1. Create or open n8n workspace.
2. Set up credential records for Shopify and backend API endpoints.
3. Capture webhook base URL for Shopify webhook registration.
4. If using n8n API automation, generate n8n API key.

---

## 4) Environment Variable Template
Use separate files per environment:
- .env.local
- .env.staging
- .env.production

Recommended variable names:
- APP_ENV
- APP_BASE_URL
- SHOPIFY_STORE_DOMAIN
- SHOPIFY_ADMIN_ACCESS_TOKEN
- SHOPIFY_WEBHOOK_SECRET
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_API_KEY
- OPENAI_API_VERSION
- AZURE_OPENAI_CHAT_DEPLOYMENT_NAME
- AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
- VAPI_API_KEY
- VAPI_ASSISTANT_ID
- VAPI_PUBLIC_KEY
- N8N_WEBHOOK_BASE_URL

---

## 5) Secret Handling Rules
- Never commit secrets to git.
- Never expose service role keys in frontend code.
- Keep all sensitive keys in server environment only.
- Rotate keys immediately if leaked.
- Maintain different keys for local, staging, production.

---

## 6) Quick Verification Checklist
- [ ] Shopify webhooks reach n8n/backend endpoint successfully
- [ ] Supabase connectivity test passes
- [ ] Azure OpenAI chat call succeeds
- [ ] Azure OpenAI embedding call succeeds
- [ ] Vapi assistant can call backend tools
- [ ] n8n workflows can authenticate and execute

If all checks pass, credential setup is complete.
