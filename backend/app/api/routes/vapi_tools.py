from __future__ import annotations

import re
import time
import threading
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError

from app.api.deps import get_azure_openai, get_supabase
from app.core.config import Settings, get_settings
from app.models.schemas import (
    VapiAction,
    VapiAddToCartInput,
    VapiNavigateInput,
    VapiOpenProductInput,
    VapiSearchInput,
    VapiShowCartInput,
    VapiToolResponse,
    VapiUpdateCartInput,
)
from app.services.azure_openai_service import AzureOpenAIService
from app.services.supabase_service import SupabaseService

router = APIRouter()

_LAST_SEARCH_CACHE_TTL_SECONDS = 600
_LAST_SEARCH_CACHE_LOCK = threading.Lock()
_LAST_SEARCH_CANDIDATES: dict[str, dict[str, Any]] = {}


# -------------------------------------------------------------------------------------
# Vapi Helpers
# -------------------------------------------------------------------------------------

def _vapi_clarification(trace_id: str, speech: str, question: str) -> VapiToolResponse:
    return VapiToolResponse(
        trace_id=trace_id,
        action=None,
        speech=speech,
        needs_clarification=True,
        clarification_question=question,
    )


def _vapi_action(trace_id: str, action_type: str, payload: dict[str, Any], speech: str) -> VapiToolResponse:
    return VapiToolResponse(
        trace_id=trace_id,
        action=VapiAction(type=action_type, payload=payload),
        speech=speech,
        needs_clarification=False,
        clarification_question=None,
    )


def _normalize_vapi_arguments(arguments: Any) -> dict[str, Any]:
    if not isinstance(arguments, dict):
        return {}

    properties = arguments.get("properties")
    if isinstance(properties, dict):
        normalized: dict[str, Any] = {}
        for key, value in properties.items():
            if isinstance(value, dict) and "value" in value:
                normalized[key] = value.get("value")
            else:
                normalized[key] = value
        return normalized

    return arguments


def _extract_vapi_tool_call(body: dict[str, Any]) -> tuple[str | None, dict[str, Any], str | None]:
    message = body.get("message") or {}
    candidates: list[dict[str, Any]] = []

    for key in ("toolCallList", "toolCalls"):
        value = message.get(key)
        if isinstance(value, list):
            candidates.extend([item for item in value if isinstance(item, dict)])

    tool_with_call = message.get("toolWithToolCallList")
    if isinstance(tool_with_call, list):
        for item in tool_with_call:
            if isinstance(item, dict):
                embedded = item.get("toolCall")
                if isinstance(embedded, dict):
                    candidates.append(embedded)

    if not candidates:
        return None, {}, None

    tool_call = candidates[0]
    function_obj = tool_call.get("function") or {}

    tool_name = tool_call.get("name") or function_obj.get("name")
    tool_call_id = tool_call.get("id") or tool_call.get("toolCallId")

    arguments = tool_call.get("arguments")
    if arguments is None:
        arguments = function_obj.get("arguments") or function_obj.get("parameters")

    return tool_name, _normalize_vapi_arguments(arguments), tool_call_id


def _to_vapi_result(tool_call_id: str | None, result: VapiToolResponse) -> dict[str, Any]:
    return {
        "results": [
            {
                "toolCallId": tool_call_id or "tool_call_unknown",
                "result": result.model_dump(),
            }
        ]
    }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", (value or "").lower())).strip()


def _query_tokens(query_text: str) -> list[str]:
    tokens = [token for token in re.split(r"[^a-z0-9]+", query_text.lower()) if len(token) >= 3]
    return tokens


_AFFIRMATIVE_PHRASES = {
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "alright",
    "absolutely", "definitely", "please", "go ahead", "do it",
    "open it", "show it", "that one", "this one", "the one",
    "yes please", "sure thing", "of course", "why not",
    "open that", "show me", "show that", "lets go", "let s go",
    "sounds good", "perfect", "great", "cool", "fine",
    "i want that", "i ll take that", "i want it", "i want this",
    "go for it", "that s it", "that is it", "correct", "right",
    "thats the one", "that s the one", "yes open it",
}


def _is_affirmative(text: str | None) -> bool:
    """Detect if the user utterance is a simple affirmation/confirmation."""
    if not text:
        return False
    normalized = _normalize_text(text)
    if not normalized:
        return False
    if normalized in _AFFIRMATIVE_PHRASES:
        return True
    # Also match short utterances that start with affirmative words
    first_word = normalized.split()[0] if normalized.split() else ""
    if first_word in {"yes", "yeah", "yep", "yup", "sure", "ok", "okay"} and len(normalized) < 30:
        return True
    return False


_NON_MEANINGFUL_WORDS = {
    "yes", "yeah", "yep", "yup", "no", "nah", "nope",
    "sure", "ok", "okay", "alright", "please", "thanks",
    "hi", "hello", "hey", "bye", "cool", "fine", "great",
    "open", "show", "that", "this", "one", "the", "it",
    "go", "do", "let", "me", "want", "get", "see",
}


def _is_meaningful_query(text: str | None) -> bool:
    """Check if a text has enough substance to be used as a vector search query.
    Prevents meaningless words like 'yes', 'ok', 'open it' from being sent to embeddings."""
    if not text or not text.strip():
        return False
    tokens = [t for t in re.split(r"[^a-z0-9]+", text.strip().lower()) if t]
    meaningful_tokens = [t for t in tokens if t not in _NON_MEANINGFUL_WORDS and len(t) >= 2]
    return len(meaningful_tokens) >= 1


def _matches_query_tokens(row: dict[str, Any], tokens: list[str]) -> bool:
    if not tokens:
        return True

    title = str(row.get("title") or "").lower()
    short_description = str(row.get("short_description") or "").lower()
    tags = " ".join([str(tag).lower() for tag in (row.get("tags") or [])])
    searchable = f"{title} {short_description} {tags}"

    return all(token in searchable for token in tokens)


def _candidate_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_id": row.get("product_id") or row.get("id") or "",
        "title": row.get("title") or "",
        "price": float(row.get("price") or 0),
        "currency": row.get("currency") or "USD",
        "in_stock": int(row.get("inventory") or 0) > 0,
    }


def _extract_vapi_session_key(wrapper_body: dict[str, Any], request: Request) -> str | None:
    message = wrapper_body.get("message") if isinstance(wrapper_body, dict) else None
    if not isinstance(message, dict):
        message = {}

    call_obj = message.get("call") if isinstance(message.get("call"), dict) else {}

    candidate_keys = [
        request.headers.get("x-vapi-call-id"),
        request.headers.get("x-vapi-conversation-id"),
        message.get("callId"),
        message.get("conversationId"),
        call_obj.get("id"),
        call_obj.get("callId"),
        call_obj.get("conversationId"),
    ]

    for key in candidate_keys:
        if isinstance(key, str) and key.strip():
            return key.strip()

    return None


def _cleanup_last_search_cache(now_ts: float) -> None:
    expired_keys = []
    for cache_key, value in _LAST_SEARCH_CANDIDATES.items():
        cached_at = float(value.get("cached_at") or 0)
        if now_ts - cached_at > _LAST_SEARCH_CACHE_TTL_SECONDS:
            expired_keys.append(cache_key)

    for cache_key in expired_keys:
        _LAST_SEARCH_CANDIDATES.pop(cache_key, None)


def _cache_last_search_candidates(session_key: str, query_text: str, candidates: list[dict[str, Any]]) -> None:
    now_ts = time.time()
    with _LAST_SEARCH_CACHE_LOCK:
        _cleanup_last_search_cache(now_ts)
        _LAST_SEARCH_CANDIDATES[session_key] = {
            "cached_at": now_ts,
            "query": query_text,
            "candidates": candidates,
        }


def _get_last_search_candidates(session_key: str) -> list[dict[str, Any]]:
    now_ts = time.time()
    with _LAST_SEARCH_CACHE_LOCK:
        _cleanup_last_search_cache(now_ts)
        value = _LAST_SEARCH_CANDIDATES.get(session_key)
        if not isinstance(value, dict):
            return []

        candidates = value.get("candidates")
        if isinstance(candidates, list):
            return [candidate for candidate in candidates if isinstance(candidate, dict)]
        return []


def _extract_rank_reference(text: str | None) -> int | None:
    if not text:
        return None

    normalized = _normalize_text(text)

    match = re.search(r"(?:^|\b)(?:number\s+)?([1-5])(?:st|nd|rd|th)?(?:\b|$)", normalized)
    if match:
        return int(match.group(1))

    ordinal_map = {
        "first": 1,
        "one": 1,
        "second": 2,
        "two": 2,
        "third": 3,
        "three": 3,
        "fourth": 4,
        "four": 4,
        "fifth": 5,
        "five": 5,
    }

    tokens = normalized.split()
    for token in tokens:
        rank = ordinal_map.get(token)
        if rank is not None:
            return rank

    return None


def _resolve_cached_candidate(
    candidates: list[dict[str, Any]],
    latest_user_utterance: str | None,
) -> dict[str, Any] | None:
    if not candidates or not latest_user_utterance:
        return None

    # If there's exactly 1 candidate and the user gave an affirmative response,
    # they are confirming the single result — return it immediately.
    if len(candidates) == 1 and _is_affirmative(latest_user_utterance):
        return candidates[0]

    normalized_utterance = _normalize_text(latest_user_utterance)
    utterance_tokens = set(_query_tokens(latest_user_utterance))

    exact_title_matches = []
    partial_title_matches = []
    token_matches = []

    for candidate in candidates:
        title = str(candidate.get("title") or "")
        normalized_title = _normalize_text(title)
        candidate_tokens = set(_query_tokens(title))

        if normalized_title and normalized_title == normalized_utterance:
            exact_title_matches.append(candidate)
            continue

        if normalized_title and normalized_title in normalized_utterance:
            partial_title_matches.append(candidate)
            continue

        if utterance_tokens and candidate_tokens and candidate_tokens.issubset(utterance_tokens):
            token_matches.append(candidate)

    if len(exact_title_matches) == 1:
        return exact_title_matches[0]
    if len(partial_title_matches) == 1:
        return partial_title_matches[0]
    if len(token_matches) == 1:
        return token_matches[0]

    rank = _extract_rank_reference(latest_user_utterance)
    if rank is not None:
        index = rank - 1
        if 0 <= index < len(candidates):
            return candidates[index]

    # If user gave a generic affirmation with multiple candidates,
    # default to the first (highest-ranked) candidate
    if _is_affirmative(latest_user_utterance):
        return candidates[0]

    return None


def _extract_latest_user_utterance(wrapper_body: dict[str, Any]) -> str | None:
    message = wrapper_body.get("message") or {}
    artifact = message.get("artifact") or {}

    candidates = artifact.get("messages")
    if not isinstance(candidates, list):
        candidates = message.get("messages")

    if not isinstance(candidates, list):
        return None

    for entry in reversed(candidates):
        if not isinstance(entry, dict):
            continue

        role = str(entry.get("role") or entry.get("speaker") or "").lower()
        if role not in {"user", "customer"}:
            continue

        content = entry.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for part in content:
                if isinstance(part, dict):
                    maybe_text = part.get("text") or part.get("content")
                    if isinstance(maybe_text, str) and maybe_text.strip():
                        text_parts.append(maybe_text.strip())
            if text_parts:
                return " ".join(text_parts)

        text = entry.get("text")
        if isinstance(text, str) and text.strip():
            return text.strip()

    return None


# -------------------------------------------------------------------------------------
# Tool Endpoints
# -------------------------------------------------------------------------------------

@router.post("/vapi/tool/search_products")
def vapi_tool_search_products(
    body: dict[str, Any],
    request: Request,
    settings: Settings = Depends(get_settings),
    supabase: SupabaseService = Depends(get_supabase),
    azure_openai: AzureOpenAIService = Depends(get_azure_openai),
) -> dict[str, Any] | VapiToolResponse:
    trace_id = request.state.trace_id
    incoming = body or {}
    is_vapi_wrapper = "message" in incoming
    tool_call_id: str | None = None
    if is_vapi_wrapper:
        _tool_name, incoming, tool_call_id = _extract_vapi_tool_call(incoming)

    try:
        parsed = VapiSearchInput.model_validate(incoming)
    except ValidationError:
        result = _vapi_clarification(
            trace_id,
            "Tell me what product you want me to find.",
            "What would you like to search for?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    query_text = parsed.query.strip()

    if not query_text:
        result = _vapi_clarification(
            trace_id,
            "Tell me what product you want me to find.",
            "What would you like to search for?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    query_embedding = azure_openai.embed_text(query_text)
    rows = supabase.match_products(
        {
            "query_embedding": query_embedding,
            "match_count": settings.default_return_count,
            "min_price": parsed.filters.min_price,
            "max_price": parsed.filters.max_price,
            "required_tags": parsed.filters.tags,
            "in_stock_only": parsed.filters.in_stock_only,
            "variant_option_contains": parsed.filters.variant_option_contains,
            "shop_domain_filter": settings.normalized_shopify_store_domain,
        }
    )

    if not rows:
        result = VapiToolResponse(
            trace_id=trace_id,
            action=None,
            speech="I could not find matching products. Try a different keyword, team, or price range.",
            needs_clarification=False,
            clarification_question=None,
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    tokens = _query_tokens(query_text)
    exact_rows = [row for row in rows if _matches_query_tokens(row, tokens)]
    chosen_rows = exact_rows if exact_rows else rows

    candidates = []
    for index, row in enumerate(chosen_rows[:5], start=1):
        candidate = _candidate_payload(row)
        candidate["rank"] = index
        candidates.append(candidate)

    if is_vapi_wrapper:
        session_key = _extract_vapi_session_key(wrapper_body=body, request=request)
        if session_key:
            _cache_last_search_candidates(session_key=session_key, query_text=query_text, candidates=candidates)

    if len(chosen_rows) == 1:
        single = candidates[0]
        stock_text = "in stock" if single["in_stock"] else "currently out of stock"
        speech = (
            f"I found one match: {single['title']}, {single['price']} {single['currency']}, {stock_text}. "
            "Would you like me to open this product?"
        )
        result = _vapi_action(
            trace_id,
            "search_products",
            {
                "query": query_text,
                "filters": parsed.filters.model_dump(),
                "match_count": 1,
                "candidates": candidates,
            },
            speech,
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    top_titles = ", ".join([candidate["title"] for candidate in candidates[:3]])
    if exact_rows:
        speech = (
            f"I found {len(exact_rows)} matching products. "
            f"Top options are: {top_titles}. Which one should I open?"
        )
    else:
        speech = (
            f"I found {len(rows)} related products, but not all are exact '{query_text}' matches. "
            f"Top options are: {top_titles}. Which one should I open?"
        )

    result = _vapi_action(
        trace_id,
        "search_products",
        {
            "query": query_text,
            "filters": parsed.filters.model_dump(),
            "match_count": len(chosen_rows),
            "candidates": candidates,
        },
        speech,
    )
    return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result


@router.post("/vapi/tool/open_product")
def vapi_tool_open_product(
    body: dict[str, Any],
    request: Request,
    settings: Settings = Depends(get_settings),
    supabase: SupabaseService = Depends(get_supabase),
    azure_openai: AzureOpenAIService = Depends(get_azure_openai),
) -> dict[str, Any] | VapiToolResponse:
    trace_id = request.state.trace_id
    incoming = body or {}
    wrapper_body = incoming if isinstance(incoming, dict) else {}
    is_vapi_wrapper = "message" in incoming
    tool_call_id: str | None = None
    if is_vapi_wrapper:
        _tool_name, incoming, tool_call_id = _extract_vapi_tool_call(incoming)

    try:
        parsed = VapiOpenProductInput.model_validate(incoming)
    except ValidationError:
        result = _vapi_clarification(
            trace_id,
            "I need a product selection before opening details.",
            "Which product should I open?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    product_id = parsed.product_id.strip()

    if not product_id:
        result = _vapi_clarification(
            trace_id,
            "I need a product selection before opening details.",
            "Which product should I open?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    row = supabase.get_product_by_id(product_id)
    if not row:
        fallback_query = product_id
        latest_user_utterance = _extract_latest_user_utterance(wrapper_body) if is_vapi_wrapper else None
        if is_vapi_wrapper:
            session_key = _extract_vapi_session_key(wrapper_body=wrapper_body, request=request)
            if session_key:
                cached_candidates = _get_last_search_candidates(session_key=session_key)
                cached_match = _resolve_cached_candidate(candidates=cached_candidates, latest_user_utterance=latest_user_utterance)
                if cached_match:
                    cached_product_id = str(cached_match.get("product_id") or "").strip()
                    if cached_product_id:
                        result = _vapi_action(
                            trace_id,
                            "open_product",
                            {"product_id": cached_product_id},
                            f"Opening {cached_match.get('title') or 'the product'}.",
                        )
                        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

        if latest_user_utterance:
            fallback_query = latest_user_utterance

        fallback_query = (fallback_query or "").strip()
        fallback_rows: list[dict[str, Any]] = []
        # Only attempt embedding search if the query has meaningful product-related words.
        # Prevents garbage results from queries like "yes", "ok", "open it", etc.
        if fallback_query and _is_meaningful_query(fallback_query):
            query_embedding = azure_openai.embed_text(fallback_query)
            fallback_rows = supabase.match_products(
                {
                    "query_embedding": query_embedding,
                    "match_count": 3,
                    "min_price": None,
                    "max_price": None,
                    "required_tags": None,
                    "in_stock_only": True,
                    "variant_option_contains": None,
                    "shop_domain_filter": settings.normalized_shopify_store_domain,
                }
            )

        if fallback_rows:
            normalized_query = _normalize_text(fallback_query)
            query_tokens = _query_tokens(fallback_query)

            exact_title_rows = [
                row_item
                for row_item in fallback_rows
                if _normalize_text(str(row_item.get("title") or "")) == normalized_query
            ]
            if len(exact_title_rows) == 1:
                chosen = exact_title_rows[0]
                chosen_id = chosen.get("product_id") or chosen.get("id") or ""
                result = _vapi_action(
                    trace_id,
                    "open_product",
                    {"product_id": chosen_id},
                    f"Opening {chosen.get('title') or 'the product'}.",
                )
                return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

            token_filtered_rows = [
                row_item for row_item in fallback_rows if _matches_query_tokens(row_item, query_tokens)
            ]
            if len(token_filtered_rows) == 1:
                chosen = token_filtered_rows[0]
                chosen_id = chosen.get("product_id") or chosen.get("id") or ""
                result = _vapi_action(
                    trace_id,
                    "open_product",
                    {"product_id": chosen_id},
                    f"Opening {chosen.get('title') or 'the product'}.",
                )
                return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

            if token_filtered_rows:
                fallback_rows = token_filtered_rows

        if len(fallback_rows) == 1:
            candidate = fallback_rows[0]
            result = _vapi_action(
                trace_id,
                "open_product",
                candidate,
                f"Opening {candidate.get('title') or 'the product'}.",
            )
            return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

        if len(fallback_rows) > 1:
            top_titles = ", ".join([str(row_item.get("title") or "") for row_item in fallback_rows[:3]])
            result = VapiToolResponse(
                trace_id=trace_id,
                action=None,
                speech=f"I found multiple possible matches: {top_titles}.",
                needs_clarification=True,
                clarification_question="Please tell me the exact product name from these options.",
            )
            return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

        result = VapiToolResponse(
            trace_id=trace_id,
            action=None,
            speech="I could not find that product. Please choose another product from the results.",
            needs_clarification=True,
            clarification_question="Which product should I open instead?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    result = _vapi_action(
        trace_id,
        "open_product",
        row,
        f"Opening {row.get('title') or 'the product'}.",
    )
    return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result


@router.post("/vapi/tool/add_to_cart_intent")
def vapi_tool_add_to_cart_intent(
    body: dict[str, Any],
    request: Request,
    supabase: SupabaseService = Depends(get_supabase),
) -> dict[str, Any] | VapiToolResponse:
    trace_id = request.state.trace_id
    incoming = body or {}
    is_vapi_wrapper = "message" in incoming
    tool_call_id: str | None = None
    if is_vapi_wrapper:
        _tool_name, incoming, tool_call_id = _extract_vapi_tool_call(incoming)

    try:
        parsed = VapiAddToCartInput.model_validate(incoming)
    except ValidationError:
        result = _vapi_clarification(
            trace_id,
            "I need to know which product you want to add.",
            "Which product do you want to add to cart?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    product_id = parsed.product_id.strip()
    variant_id = parsed.variant_id.strip()
    quantity = parsed.quantity

    if not product_id:
        result = _vapi_clarification(
            trace_id,
            "I need to know which product you want to add.",
            "Which product do you want to add to cart?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result
    if not variant_id:
        result = _vapi_clarification(
            trace_id,
            "I need a specific size or variant before adding to cart.",
            "Which size or variant do you want?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result
    if quantity is None:
        result = _vapi_clarification(
            trace_id,
            "I need quantity to update the cart safely.",
            "How many do you want to add?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    row = supabase.get_product_by_id(product_id)
    if not row:
        result = VapiToolResponse(
            trace_id=trace_id,
            action=None,
            speech="That product is unavailable right now.",
            needs_clarification=True,
            clarification_question="Do you want a different product?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    variants = row.get("variants") or []
    has_variant = any((variant.get("variant_id") or "") == variant_id for variant in variants)
    if not has_variant:
        result = VapiToolResponse(
            trace_id=trace_id,
            action=None,
            speech="That variant was not found for this product.",
            needs_clarification=True,
            clarification_question="Which available size or variant should I use?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    result = _vapi_action(
        trace_id,
        "add_to_cart",
        {"product_id": product_id, "variant_id": variant_id, "quantity": quantity},
        "Adding that item to your cart.",
    )
    return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result


@router.post("/vapi/tool/update_cart_intent")
def vapi_tool_update_cart_intent(
    body: dict[str, Any],
    request: Request,
) -> dict[str, Any] | VapiToolResponse:
    trace_id = request.state.trace_id
    incoming = body or {}
    is_vapi_wrapper = "message" in incoming
    tool_call_id: str | None = None
    if is_vapi_wrapper:
        _tool_name, incoming, tool_call_id = _extract_vapi_tool_call(incoming)

    try:
        parsed = VapiUpdateCartInput.model_validate(incoming)
    except ValidationError:
        result = _vapi_clarification(
            trace_id,
            "I need the cart line to update.",
            "Which cart item should I update?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    line_id = parsed.line_id.strip()
    variant_id = parsed.variant_id.strip()
    quantity = parsed.quantity

    if not line_id:
        result = _vapi_clarification(
            trace_id,
            "I need the cart line to update.",
            "Which cart item should I update?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result
    if not variant_id:
        result = _vapi_clarification(
            trace_id,
            "I need the target variant before updating.",
            "Which variant should I use?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result
    if quantity is None:
        result = _vapi_clarification(
            trace_id,
            "I need the new quantity.",
            "What quantity should I set?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    result = _vapi_action(
        trace_id,
        "update_cart",
        {"line_id": line_id, "variant_id": variant_id, "quantity": quantity},
        "Updating your cart.",
    )
    return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result


@router.post("/vapi/tool/show_cart_intent")
def vapi_tool_show_cart_intent(
    body: dict[str, Any],
    request: Request,
) -> dict[str, Any] | VapiToolResponse:
    trace_id = request.state.trace_id
    incoming = body or {}
    is_vapi_wrapper = "message" in incoming
    tool_call_id: str | None = None
    if is_vapi_wrapper:
        _tool_name, _incoming, tool_call_id = _extract_vapi_tool_call(incoming)

    result = _vapi_action(
        trace_id, 
        "show_cart", 
        {
            "status": "success", 
            "system_note": "The visual cart has successfully popped open on the user's screen. You cannot see the items. DO NOT apologize. Simply acknowledge by saying 'Opening your cart.'"
        }, 
        "Opening your cart."
    )
    return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result


@router.post("/vapi/tool/navigate_intent")
def vapi_tool_navigate_intent(
    body: dict[str, Any],
    request: Request,
) -> dict[str, Any] | VapiToolResponse:
    trace_id = request.state.trace_id
    incoming = body or {}
    is_vapi_wrapper = "message" in incoming
    tool_call_id: str | None = None
    if is_vapi_wrapper:
        _tool_name, incoming, tool_call_id = _extract_vapi_tool_call(incoming)

    try:
        parsed = VapiNavigateInput.model_validate(incoming)
    except ValidationError:
        result = _vapi_clarification(
            trace_id,
            "I need a destination before I can navigate.",
            "Where do you want to go?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    if not parsed.page and not parsed.url:
        result = _vapi_clarification(
            trace_id,
            "I need a destination before I can navigate.",
            "Where do you want to go?",
        )
        return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result

    payload: dict[str, Any] = {}
    if parsed.page:
        payload["page"] = parsed.page
    if parsed.url:
        payload["url"] = parsed.url

    payload["system_note"] = "The system has successfully navigated the user's browser. You cannot see the user's screen. DO NOT apologize or state that you cannot see the page. Simply acknowledge by saying 'Navigating now.'"

    result = _vapi_action(trace_id, "navigate", payload, "Navigating now.")
    return _to_vapi_result(tool_call_id, result) if is_vapi_wrapper else result
