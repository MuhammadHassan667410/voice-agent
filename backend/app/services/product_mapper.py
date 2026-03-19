from __future__ import annotations

import re
from typing import Any


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]*>", "", text).strip()


def _to_gid(product_id: Any) -> str:
    if isinstance(product_id, str) and product_id.startswith("gid://"):
        return product_id
    return f"gid://shopify/Product/{product_id}"


def _normalize_shop_domain(shop_domain: str | None) -> str:
    value = (shop_domain or "").strip()
    value = re.sub(r"^https?://", "", value, flags=re.IGNORECASE)
    value = value.split("/")[0]
    return value.lower()


def _extract_currency(payload: dict[str, Any]) -> str | None:
    currency_candidates: list[str | None] = [
        payload.get("currency"),
        payload.get("presentment_currency"),
        payload.get("shop_currency"),
        payload.get("currency_code"),
        payload.get("price_currency"),
    ]

    variants = payload.get("variants") or []
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        currency_candidates.extend(
            [
                variant.get("currency"),
                variant.get("presentment_currency"),
                variant.get("currency_code"),
            ]
        )

        presentment_prices = variant.get("presentment_prices") or []
        if isinstance(presentment_prices, list):
            for presentment in presentment_prices:
                if not isinstance(presentment, dict):
                    continue
                price_obj = presentment.get("price") or {}
                if isinstance(price_obj, dict):
                    currency_candidates.append(price_obj.get("currency_code"))

    for candidate in currency_candidates:
        if not candidate or not isinstance(candidate, str):
            continue
        cleaned = candidate.strip().upper()
        if re.fullmatch(r"[A-Z]{3}", cleaned):
            return cleaned

    return None


def map_shopify_product(payload: dict[str, Any], shop_domain: str, fallback_currency: str = "USD") -> dict[str, Any]:
    variants = payload.get("variants") or []
    images_payload = payload.get("images") or []

    image_urls = [img.get("src") for img in images_payload if isinstance(img, dict) and img.get("src")]
    if payload.get("image") and isinstance(payload.get("image"), dict):
        hero = payload["image"].get("src")
        if hero and hero not in image_urls:
            image_urls.insert(0, hero)

    tags = payload.get("tags") or ""
    tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if isinstance(tags, str) else []

    inventory = 0
    normalized_variants = []
    for variant in variants:
        qty = int(variant.get("inventory_quantity") or 0)
        inventory += max(qty, 0)
        normalized_variants.append(
            {
                "variant_id": f"gid://shopify/ProductVariant/{variant.get('id')}",
                "title": variant.get("title") or "Default",
                "price": float(variant.get("price") or 0),
                "available": bool(variant.get("available", qty > 0)),
            }
        )

    body_text = _strip_html(payload.get("body_html"))
    short_description = body_text[:240] if body_text else None

    base_price = float(normalized_variants[0]["price"]) if normalized_variants else float(payload.get("price") or 0)

    resolved_currency = _extract_currency(payload) or (fallback_currency or "USD").strip().upper() or "USD"

    return {
        "id": _to_gid(payload.get("id")),
        "shop_domain": _normalize_shop_domain(shop_domain),
        "handle": payload.get("handle"),
        "title": payload.get("title") or "",
        "description": body_text,
        "short_description": short_description,
        "price": base_price,
        "currency": resolved_currency,
        "images": image_urls,
        "variants": normalized_variants,
        "tags": tags_list,
        "inventory": inventory,
        "status": payload.get("status"),
        "vendor": payload.get("vendor"),
        "product_type": payload.get("product_type"),
        "source_created_at": payload.get("created_at"),
        "source_updated_at": payload.get("updated_at"),
        "metadata": {
            "source": "shopify",
        },
    }


def build_embedding_input(product_record: dict[str, Any]) -> str:
    title = product_record.get("title") or ""
    short_description = product_record.get("short_description") or ""
    tags = " ".join(product_record.get("tags") or [])
    return f"{title}\n{short_description}\n{tags}".strip()
