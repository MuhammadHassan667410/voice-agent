from __future__ import annotations

from typing import Any

from supabase import Client, create_client

from app.core.config import Settings
from app.core.errors import AppError


class SupabaseService:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise AppError("CONFIG_ERROR", "Supabase config is missing", status_code=500)
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    def get_product_by_id(self, product_id: str) -> dict[str, Any] | None:
        response = self.client.table("products").select("*").eq("id", product_id).limit(1).execute()
        if not response.data:
            return None
        return response.data[0]

    def filter_products(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        response = self.client.rpc("filter_products", params).execute()
        return response.data or []

    def match_products(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        response = self.client.rpc("match_products", params).execute()
        return response.data or []

    def upsert_product(self, payload: dict[str, Any]) -> None:
        self.client.table("products").upsert(payload, on_conflict="id").execute()

    def upsert_embedding(self, product_id: str, embedding: list[float], embedding_input: str, metadata: dict[str, Any]) -> None:
        self.client.table("product_embeddings").upsert(
            {
                "product_id": product_id,
                "embedding": embedding,
                "embedding_input": embedding_input,
                "metadata": metadata,
            },
            on_conflict="product_id",
        ).execute()

    def delete_product(self, product_id: str) -> None:
        self.client.table("products").delete().eq("id", product_id).execute()

    def write_sync_event(self, event: dict[str, Any]) -> None:
        self.client.table("sync_events").upsert(event, on_conflict="idempotency_key").execute()

    def has_sync_event(self, idempotency_key: str) -> bool:
        response = self.client.table("sync_events").select("id").eq("idempotency_key", idempotency_key).limit(1).execute()
        return bool(response.data)
