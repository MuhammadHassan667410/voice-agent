# Part 1 - Logging and Trace-ID Convention

## Trace ID Rules
- Every inbound request gets `trace_id`.
- Preserve incoming `X-Trace-Id` if valid; otherwise generate new.
- Return `trace_id` in every response body and response header.
- Propagate `trace_id` on all downstream calls (Azure OpenAI, Supabase, n8n callbacks).

## Log Event Format (JSON)
Required fields:
- `timestamp`
- `level`
- `service`
- `environment`
- `trace_id`
- `event_name`
- `message`
- `context` (object)

Example:
```json
{
  "timestamp": "2026-03-17T10:00:00Z",
  "level": "INFO",
  "service": "backend-api",
  "environment": "local",
  "trace_id": "tr_01H...",
  "event_name": "search_products.completed",
  "message": "Search request served",
  "context": {
    "query": "turf shoes",
    "result_count": 6,
    "latency_ms": 143
  }
}
```

## Minimum Log Events
- `http.request.received`
- `http.request.completed`
- `http.request.failed`
- `sync.event.received`
- `sync.event.idempotent_skipped`
- `sync.event.processed`
- `sync.event.failed`
- `embedding.generated`
- `embedding.skipped_non_text_update`
- `cart.intent.validated`
- `vapi.tool.called`

## PII/Sensitive Data Policy
- Do not log API keys or secrets.
- Do not log full webhook signatures.
- Avoid raw customer-identifiable data in info logs.
- Use redaction for sensitive fields.

## SLO-oriented Metrics to capture
- Search endpoint latency p50/p95
- Sync processing latency
- Sync failure rate
- Embedding generation error rate
- Cart intent validation failure rate
