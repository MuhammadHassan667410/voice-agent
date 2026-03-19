# AI Voice Agent - Client Store Integration Guide

Use this guide after Parts 1-8 are complete to deploy the same voice agent system to any Shopify client store with predictable setup.

## 1) Operating Model (What You Reuse vs What Changes)

### Reusable across all clients
- Backend codebase (FastAPI)
- Supabase schema and SQL functions
- n8n workflow templates
- Voice widget code (theme app embed + JS)
- Vapi assistant instructions and tool contracts

### Client-specific per store
- Shopify store domain and app credentials
- Shopify webhook secret and webhook endpoints
- Store product catalog and embeddings
- Branding/theme placement for widget
- Optional client-specific prompt/system rules

---

## 2) Recommended Production Architecture

- Backend: hosted API with stable HTTPS domain (for example `https://api.yourdomain.com`)
- Workflow engine: hosted n8n with production webhook endpoints
- Database: Supabase project (single-tenant or multi-tenant)
- Vector/embeddings: Azure OpenAI + pgvector
- Voice runtime: Vapi
- Secrets: managed secret store (not hardcoded in workflow code)
- Monitoring: centralized logs + alerts + uptime checks

Do not use temporary tunnels (ngrok/localtunnel/cloudflared) in production.

---

## 3) Multi-Tenant Strategy (Critical)

For multiple clients, use one of these:

### Option A: Separate environment per client (simplest, safest)
- One backend deployment per client
- One Supabase project per client
- One n8n workspace per client
- Easiest isolation, easier compliance, higher ops cost

### Option B: Shared platform with tenant isolation (scales better)
- Single backend + shared infra
- Every request tagged by `shop_domain` (tenant id)
- DB row-level isolation by tenant key
- n8n routes and secrets resolved per tenant
- Lower cost, higher engineering rigor

If you are starting services for clients, begin with Option A first.

---

## 4) One-Time Platform Hardening Before Client Onboarding

Complete this once before onboarding any real client:

- Use production URL + SSL certificate
- Add OAuth install flow for Shopify app installation
- Add auto webhook registration on install
- Add uninstall webhook handling and token revocation
- Move secrets to secret manager
- Add rate limiting + CORS allowlist
- Add idempotency + replay protection (already in your sync flow)
- Add async queue for embedding jobs and reindex jobs
- Add health/readiness endpoints and uptime monitoring
- Add audit logs for sync mutations

---

## 5) Client Onboarding Checklist (Per New Shopify Store)

## Step 1 - Pre-onboarding
Collect:
- Store domain (`client-store.myshopify.com`)
- Client contact + technical owner
- Approved theme(s)
- Product count estimate (for backfill sizing)
- Locale/currency and business rules

## Step 2 - Shopify app install
- Install your Shopify app on client store
- Grant required scopes (product read, webhook-related scopes)
- Store shop token securely
- Capture webhook signing secret

## Step 3 - Configure backend tenant
Set per-client config values:
- `SHOPIFY_STORE_DOMAIN`
- `SHOPIFY_ADMIN_ACCESS_TOKEN`
- `SHOPIFY_WEBHOOK_SECRET`
- `SUPABASE_*` keys (or tenant binding)
- `AZURE_OPENAI_*` values
- `VAPI_*` values
- `REINDEX_ADMIN_TOKEN`

## Step 4 - Configure n8n for client
- Import workflow templates (0 through 5)
- Bind credentials/secrets for this client
- Set webhook URLs to production URLs
- Activate workflows 1,2,3,4,5
- Keep workflow 0 for initial backfill run only

## Step 5 - Register Shopify webhooks
Create these webhooks in Shopify (JSON format, stable API version):
- Product creation -> `/webhook/shopify/product-created`
- Product update -> `/webhook/shopify/product-updated`
- Product deletion -> `/webhook/shopify/product-deleted`

## Step 6 - Initial catalog backfill
- Run workflow `0_initial_shopify_backfill`
- Verify products inserted into `products`
- Verify embeddings inserted into `product_embeddings`
- For large stores, paginate or use bulk operations

## Step 7 - Widget deployment on client theme
- Add app embed / snippet to theme
- Enable floating widget globally (all pages)
- Confirm no full page reload flows are intact
- Verify cart operations against client theme/cart behavior

## Step 8 - Voice assistant configuration
- Duplicate/base Vapi assistant for client
- Configure tool endpoints to client backend
- Apply client-specific conversation rules
- Validate fallback and error behavior

## Step 9 - Acceptance test run
Validate on client store:
- Search relevance
- Open product details
- Add/update/show cart actions
- Page navigation without full reload
- Create/update/delete sync correctness
- Reindex endpoint security

## Step 10 - Go-live signoff
- Obtain client signoff on UAT checklist
- Freeze config snapshot
- Enable monitoring alerts
- Document rollback path

---

## 6) Credentials Matrix (Per Client)

Track this in your secure ops system (not in git):

- Shopify: store domain, admin token, webhook secret
- Backend: base URL, admin token, allowed origins
- Supabase: URL, service role key, project id
- Azure OpenAI: endpoint, key, deployments
- Vapi frontend: public key, assistant id
- Vapi backend/automation: API key (server-side only)
- n8n: webhook base URL, workflow ids, credential refs

---

## 7) Runtime Requirements in Production

- Backend must be always-on (24/7)
- n8n must be always-on (24/7)
- Shopify webhooks must hit public stable HTTPS endpoints
- Async workers should be available for embedding/reindex spikes

If backend is down, webhook processing and sync will fail. Use retries + DLQ replay.

---

## 8) Update/Rollout Strategy for Existing Clients

When you ship a new version:

- Use semantic versioning (`v1.2.0`)
- Deploy to staging first
- Run regression tests against a staging Shopify store
- Roll out client-by-client (canary)
- Monitor error/latency dashboards
- Keep rollback artifact ready

---

## 9) Common Failure Modes and Recovery

- Invalid webhook signature -> check secret mismatch
- Duplicate event processing -> confirm idempotency keys
- Missing embeddings after updates -> inspect text-change decision path
- Widget visible but actions fail -> check backend URL/CORS/origin
- Backfill incomplete -> rerun with pagination/bulk mode
- Reindex forbidden -> verify `X-Admin-Token`

---

## 10) Security and Compliance Baseline

- Never store client secrets in code or repo
- Rotate tokens on schedule and on staff/client transitions
- Restrict admin endpoints by token + IP allowlist where possible
- Keep per-client data isolation enforced in DB and logs
- Minimize PII in logs and traces

---

## 11) Suggested Internal SOP Assets

Create and maintain these docs/templates:
- Client onboarding form
- Client cutover checklist
- Incident response playbook
- Key rotation SOP
- Offboarding/deprovisioning checklist
- Monthly health report template

---

## 12) 60-Minute Fast Onboarding Flow (When Platform Is Ready)

1. Install app on client store (10 min)
2. Save credentials in secret manager (5 min)
3. Configure backend tenant settings (10 min)
4. Import + activate n8n workflows (10 min)
5. Register webhooks and send test events (10 min)
6. Run initial backfill + smoke tests (10 min)
7. Enable widget and do live demo (5 min)

---

## 13) Final Recommendation

For your first few client projects, use one isolated environment per client. After you stabilize operations, migrate to a shared multi-tenant platform with strong tenant isolation and automated onboarding.
