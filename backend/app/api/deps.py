from __future__ import annotations

from typing import Any

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.models.schemas import ProductItem
from app.services.azure_openai_service import AzureOpenAIService
from app.services.supabase_service import SupabaseService


def get_supabase(settings: Settings = Depends(get_settings)) -> SupabaseService:
    return SupabaseService(settings)


def get_azure_openai(settings: Settings = Depends(get_settings)) -> AzureOpenAIService:
    return AzureOpenAIService(settings)


def to_product_item(row: dict[str, Any], include_score: bool = False) -> ProductItem:
    variants = row.get("variants") or []
    normalized_variants = []
    for variant in variants:
        normalized_variants.append(
            {
                "variant_id": variant.get("variant_id", ""),
                "title": variant.get("title", "Default"),
                "price": float(variant.get("price") or 0),
                "available": bool(variant.get("available", False)),
            }
        )

    payload = {
        "id": row.get("product_id") or row.get("id") or "",
        "title": row.get("title") or "",
        "short_description": row.get("short_description"),
        "price": float(row.get("price") or 0),
        "currency": row.get("currency") or "USD",
        "images": row.get("images") or [],
        "tags": row.get("tags") or [],
        "inventory": int(row.get("inventory") or 0),
        "variants": normalized_variants,
    }
    if include_score:
        payload["score"] = float(row.get("similarity") or 0)
    return ProductItem(**payload)
