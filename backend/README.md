# Backend (Part 3)

## Run locally
1. Create virtual environment and install requirements:
   - `pip install -r requirements.txt`
2. Ensure root `.env` contains required variables (Supabase + Azure OpenAI + Shopify).
3. Start API from `backend` directory:
   - `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

## Run on Render
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"`

Render injects `PORT` automatically and terminates TLS at the edge. The proxy-forwarding flags ensure request scheme/client info are forwarded correctly.

## Implemented in Part 3
- FastAPI scaffold
- Config and env loading
- Core endpoints: `/search-products`, `/product/{id}`, `/filter-products`
- Sync endpoints: product create/update/delete
- Owner-protected reindex endpoint
- Standardized error handling
- Trace-id and request timing middleware
- Structured request logging
