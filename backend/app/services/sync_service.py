from __future__ import annotations

from typing import Any

from app.core.errors import AppError
from app.services.azure_openai_service import AzureOpenAIService
from app.services.product_mapper import build_embedding_input, map_shopify_product
from app.services.supabase_service import SupabaseService


TEXT_FIELDS = ("title", "short_description", "tags")


class SyncService:
    def __init__(self, supabase: SupabaseService, azure_openai: AzureOpenAIService) -> None:
        self.supabase = supabase
        self.azure_openai = azure_openai

    def _event_key(self, shop_domain: str, topic: str, product_id: str, occurred_at: str | None) -> str:
        return f"{shop_domain}:{topic}:{product_id}:{occurred_at or 'na'}"

    def _payload_has_currency(self, payload: dict[str, Any]) -> bool:
        direct_keys = ("currency", "presentment_currency", "shop_currency", "currency_code", "price_currency")
        if any(payload.get(key) for key in direct_keys):
            return True

        variants = payload.get("variants") or []
        for variant in variants:
            if not isinstance(variant, dict):
                continue
            if any(variant.get(key) for key in ("currency", "presentment_currency", "currency_code")):
                return True
            presentment_prices = variant.get("presentment_prices") or []
            if isinstance(presentment_prices, list):
                for presentment in presentment_prices:
                    if not isinstance(presentment, dict):
                        continue
                    price_obj = presentment.get("price") or {}
                    if isinstance(price_obj, dict) and price_obj.get("currency_code"):
                        return True

        return False

    def process_created(self, envelope: dict[str, Any], trace_id: str, topic: str) -> tuple[str, str]:
        fallback_currency = envelope.get("store_currency") or "USD"
        product = map_shopify_product(envelope["payload"], envelope["shop_domain"], fallback_currency=fallback_currency)
        product_id = product["id"]
        event_key = self._event_key(envelope["shop_domain"], topic, product_id, envelope.get("occurred_at"))

        if self.supabase.has_sync_event(event_key):
            return "skipped", "skipped"

        self.supabase.upsert_product(product)
        embedding_input = build_embedding_input(product)
        embedding = self.azure_openai.embed_text(embedding_input)
        self.supabase.upsert_embedding(product_id, embedding, embedding_input, {"source": "shopify-create"})

        self.supabase.write_sync_event(
            {
                "idempotency_key": event_key,
                "event_topic": topic,
                "event_id": envelope.get("event_id"),
                "shop_domain": envelope["shop_domain"],
                "product_id": product_id,
                "event_occurred_at": envelope.get("occurred_at"),
                "status": "processed",
                "embedding_action": "created",
                "payload": envelope["payload"],
                "trace_id": trace_id,
            }
        )
        return "processed", "created"

    def process_updated(self, envelope: dict[str, Any], trace_id: str, topic: str) -> tuple[str, str]:
        fallback_currency = envelope.get("store_currency") or "USD"
        product = map_shopify_product(envelope["payload"], envelope["shop_domain"], fallback_currency=fallback_currency)
        product_id = product["id"]
        event_key = self._event_key(envelope["shop_domain"], topic, product_id, envelope.get("occurred_at"))

        if self.supabase.has_sync_event(event_key):
            return "skipped", "skipped"

        existing = self.supabase.get_product_by_id(product_id)
        if existing and not self._payload_has_currency(envelope["payload"]):
            product["currency"] = existing.get("currency") or product.get("currency")
        self.supabase.upsert_product(product)

        embedding_input = build_embedding_input(product)
        embedding = self.azure_openai.embed_text(embedding_input)
        self.supabase.upsert_embedding(product_id, embedding, embedding_input, {"source": "shopify-update"})
        embedding_action = "updated"

        self.supabase.write_sync_event(
            {
                "idempotency_key": event_key,
                "event_topic": topic,
                "event_id": envelope.get("event_id"),
                "shop_domain": envelope["shop_domain"],
                "product_id": product_id,
                "event_occurred_at": envelope.get("occurred_at"),
                "status": "processed",
                "embedding_action": embedding_action,
                "payload": envelope["payload"],
                "trace_id": trace_id,
            }
        )
        return "processed", embedding_action

    def process_deleted(self, envelope: dict[str, Any], trace_id: str, topic: str) -> tuple[str, str]:
        payload = envelope["payload"]
        product_id_raw = payload.get("id")
        if not product_id_raw:
            raise AppError("VALIDATION_ERROR", "Delete payload must include id", status_code=400)

        product_id = (
            product_id_raw
            if isinstance(product_id_raw, str) and product_id_raw.startswith("gid://")
            else f"gid://shopify/Product/{product_id_raw}"
        )

        event_key = self._event_key(envelope["shop_domain"], topic, product_id, envelope.get("occurred_at"))
        if self.supabase.has_sync_event(event_key):
            return "skipped", "skipped"

        self.supabase.delete_product(product_id)

        self.supabase.write_sync_event(
            {
                "idempotency_key": event_key,
                "event_topic": topic,
                "event_id": envelope.get("event_id"),
                "shop_domain": envelope["shop_domain"],
                "product_id": product_id,
                "event_occurred_at": envelope.get("occurred_at"),
                "status": "processed",
                "embedding_action": "deleted",
                "payload": envelope["payload"],
                "trace_id": trace_id,
            }
        )
        return "processed", "deleted"
