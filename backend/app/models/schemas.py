from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    retryable: bool = False


class ErrorResponse(BaseModel):
    trace_id: str
    error: ErrorBody


class PaginationRequest(BaseModel):
    limit: int = Field(default=6, ge=1, le=50)
    offset: int = Field(default=0, ge=0)


class SearchFilters(BaseModel):
    min_price: float | None = None
    max_price: float | None = None
    tags: list[str] | None = None
    in_stock_only: bool = True
    variant_option_contains: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    pagination: PaginationRequest = Field(default_factory=PaginationRequest)


class FilterSort(BaseModel):
    field: Literal["price", "updated_at"] = "updated_at"
    order: Literal["asc", "desc"] = "desc"


class FilterRequest(BaseModel):
    filters: SearchFilters = Field(default_factory=SearchFilters)
    sort: FilterSort = Field(default_factory=FilterSort)
    pagination: PaginationRequest = Field(default_factory=lambda: PaginationRequest(limit=24, offset=0))


class ProductVariant(BaseModel):
    variant_id: str
    title: str
    price: float
    available: bool


class ProductItem(BaseModel):
    id: str
    title: str
    short_description: str | None = None
    price: float
    currency: str
    images: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    inventory: int
    variants: list[ProductVariant] = Field(default_factory=list)
    score: float | None = None


class PageMeta(BaseModel):
    limit: int
    offset: int
    total_estimate: int


class SearchResponse(BaseModel):
    trace_id: str
    items: list[ProductItem]
    page: PageMeta


class ProductResponse(BaseModel):
    trace_id: str
    item: ProductItem


class HealthResponse(BaseModel):
    trace_id: str
    status: Literal["ok"]
    version: str


class SyncEnvelope(BaseModel):
    shop_domain: str
    store_currency: str | None = None
    event_id: str | None = None
    occurred_at: str | None = None
    payload: dict[str, Any]


class SyncResponse(BaseModel):
    trace_id: str
    status: Literal["processed", "skipped", "failed"]
    event_id: str | None = None
    embedding_action: Literal["created", "updated", "skipped", "deleted"] | None = None


class ReindexRequest(BaseModel):
    scope: Literal["all", "ids"] = "all"
    product_ids: list[str] = Field(default_factory=list)
    reason: str | None = None


class ReindexResponse(BaseModel):
    trace_id: str
    job_id: str
    accepted: bool


VapiActionType = Literal["search_products", "open_product", "add_to_cart", "update_cart", "show_cart", "navigate"]
VapiPageType = Literal["home", "collection", "product", "cart", "search"]


class VapiSearchInput(BaseModel):
    query: str = ""
    filters: SearchFilters = Field(default_factory=SearchFilters)


class VapiOpenProductInput(BaseModel):
    product_id: str = ""


class VapiAddToCartInput(BaseModel):
    product_id: str = ""
    variant_id: str = ""
    quantity: int | None = Field(default=None, ge=1)


class VapiUpdateCartInput(BaseModel):
    line_id: str = ""
    variant_id: str = ""
    quantity: int | None = Field(default=None, ge=0)


class VapiShowCartInput(BaseModel):
    pass


class VapiNavigateInput(BaseModel):
    page: VapiPageType | None = None
    url: str | None = None


class VapiAction(BaseModel):
    type: VapiActionType
    payload: dict[str, Any] = Field(default_factory=dict)


class VapiToolResponse(BaseModel):
    trace_id: str
    action: VapiAction | None = None
    speech: str
    needs_clarification: bool = False
    clarification_question: str | None = None
