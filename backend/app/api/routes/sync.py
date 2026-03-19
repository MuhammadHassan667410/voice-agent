from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Header, Request

from app.api.deps import get_azure_openai, get_supabase
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.schemas import (
    ReindexRequest,
    ReindexResponse,
    SyncEnvelope,
    SyncResponse,
)
from app.services.azure_openai_service import AzureOpenAIService
from app.services.supabase_service import SupabaseService
from app.services.sync_service import SyncService

router = APIRouter()


@router.post("/sync/shopify/product-created", response_model=SyncResponse)
def sync_product_created(
    body: SyncEnvelope,
    request: Request,
    x_webhook_topic: str = Header(default="products/create", alias="X-Webhook-Topic"),
    _x_webhook_event_id: str | None = Header(default=None, alias="X-Webhook-Event-Id"),
    settings: Settings = Depends(get_settings),
    supabase: SupabaseService = Depends(get_supabase),
    azure_openai: AzureOpenAIService = Depends(get_azure_openai),
) -> SyncResponse:
    trace_id = request.state.trace_id
    envelope = body.model_dump()
    if not envelope.get("store_currency"):
        envelope["store_currency"] = settings.shopify_store_currency
    status, embedding_action = SyncService(supabase, azure_openai).process_created(envelope, trace_id, x_webhook_topic)
    return SyncResponse(trace_id=trace_id, status=status, event_id=body.event_id, embedding_action=embedding_action)


@router.post("/sync/shopify/product-updated", response_model=SyncResponse)
def sync_product_updated(
    body: SyncEnvelope,
    request: Request,
    x_webhook_topic: str = Header(default="products/update", alias="X-Webhook-Topic"),
    _x_webhook_event_id: str | None = Header(default=None, alias="X-Webhook-Event-Id"),
    settings: Settings = Depends(get_settings),
    supabase: SupabaseService = Depends(get_supabase),
    azure_openai: AzureOpenAIService = Depends(get_azure_openai),
) -> SyncResponse:
    trace_id = request.state.trace_id
    envelope = body.model_dump()
    if not envelope.get("store_currency"):
        envelope["store_currency"] = settings.shopify_store_currency
    status, embedding_action = SyncService(supabase, azure_openai).process_updated(envelope, trace_id, x_webhook_topic)
    return SyncResponse(trace_id=trace_id, status=status, event_id=body.event_id, embedding_action=embedding_action)


@router.post("/sync/shopify/product-deleted", response_model=SyncResponse)
def sync_product_deleted(
    body: SyncEnvelope,
    request: Request,
    x_webhook_topic: str = Header(default="products/delete", alias="X-Webhook-Topic"),
    _x_webhook_event_id: str | None = Header(default=None, alias="X-Webhook-Event-Id"),
    settings: Settings = Depends(get_settings),
    supabase: SupabaseService = Depends(get_supabase),
    azure_openai: AzureOpenAIService = Depends(get_azure_openai),
) -> SyncResponse:
    trace_id = request.state.trace_id
    envelope = body.model_dump()
    if not envelope.get("store_currency"):
        envelope["store_currency"] = settings.shopify_store_currency
    status, embedding_action = SyncService(supabase, azure_openai).process_deleted(envelope, trace_id, x_webhook_topic)
    return SyncResponse(trace_id=trace_id, status=status, event_id=body.event_id, embedding_action=embedding_action)


@router.post("/sync/reindex", response_model=ReindexResponse)
def sync_reindex(
    body: ReindexRequest,
    request: Request,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    settings: Settings = Depends(get_settings),
) -> ReindexResponse:
    trace_id = request.state.trace_id

    if not settings.reindex_admin_token:
        raise AppError("CONFIG_ERROR", "REINDEX_ADMIN_TOKEN is not configured", status_code=500)
    if x_admin_token != settings.reindex_admin_token:
        raise AppError("FORBIDDEN", "invalid admin token", status_code=403)

    if body.scope == "ids" and not body.product_ids:
        raise AppError("VALIDATION_ERROR", "product_ids required when scope=ids", status_code=400)

    job_id = f"reindex_{uuid.uuid4().hex}"
    return ReindexResponse(trace_id=trace_id, job_id=job_id, accepted=True)
