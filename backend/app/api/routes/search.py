from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_azure_openai, get_supabase, to_product_item
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.schemas import (
    FilterRequest,
    PageMeta,
    ProductResponse,
    SearchRequest,
    SearchResponse,
)
from app.services.azure_openai_service import AzureOpenAIService
from app.services.supabase_service import SupabaseService

router = APIRouter()


@router.post("/search-products", response_model=SearchResponse)
def search_products(
    body: SearchRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    supabase: SupabaseService = Depends(get_supabase),
    azure_openai: AzureOpenAIService = Depends(get_azure_openai),
) -> SearchResponse:
    trace_id = request.state.trace_id
    query_text = body.query.strip()
    if not query_text:
        raise AppError("VALIDATION_ERROR", "query must not be empty", status_code=400)

    query_embedding = azure_openai.embed_text(query_text)
    rows = supabase.match_products(
        {
            "query_embedding": query_embedding,
            "match_count": body.pagination.limit,
            "min_price": body.filters.min_price,
            "max_price": body.filters.max_price,
            "required_tags": body.filters.tags,
            "in_stock_only": body.filters.in_stock_only,
            "variant_option_contains": body.filters.variant_option_contains,
            "shop_domain_filter": settings.normalized_shopify_store_domain,
        }
    )

    items = [to_product_item(row, include_score=True) for row in rows]
    return SearchResponse(
        trace_id=trace_id,
        items=items,
        page=PageMeta(limit=body.pagination.limit, offset=body.pagination.offset, total_estimate=len(items)),
    )


@router.get("/product/{product_id:path}", response_model=ProductResponse)
def get_product(
    product_id: str,
    request: Request,
    supabase: SupabaseService = Depends(get_supabase),
) -> ProductResponse:
    trace_id = request.state.trace_id
    row = supabase.get_product_by_id(product_id)
    if not row:
        raise AppError("NOT_FOUND", "product not found", status_code=404)

    return ProductResponse(trace_id=trace_id, item=to_product_item(row))


@router.post("/filter-products", response_model=SearchResponse)
def filter_products(
    body: FilterRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    supabase: SupabaseService = Depends(get_supabase),
) -> SearchResponse:
    trace_id = request.state.trace_id
    rows = supabase.filter_products(
        {
            "page_limit": body.pagination.limit,
            "page_offset": body.pagination.offset,
            "min_price": body.filters.min_price,
            "max_price": body.filters.max_price,
            "required_tags": body.filters.tags,
            "in_stock_only": body.filters.in_stock_only,
            "variant_option_contains": body.filters.variant_option_contains,
            "sort_field": body.sort.field,
            "sort_order": body.sort.order,
            "shop_domain_filter": settings.normalized_shopify_store_domain,
        }
    )
    items = [to_product_item(row, include_score=False) for row in rows]
    return SearchResponse(
        trace_id=trace_id,
        items=items,
        page=PageMeta(limit=body.pagination.limit, offset=body.pagination.offset, total_estimate=len(items)),
    )
