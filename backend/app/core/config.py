from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="ai-shopify-assistant", alias="APP_NAME")
    app_base_url: str = Field(default="http://localhost:8000", alias="APP_BASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_allowed_origins: str = Field(default="*", alias="CORS_ALLOWED_ORIGINS")

    shopify_store_domain: str = Field(default="", alias="SHOPIFY_STORE_DOMAIN")
    shopify_store_currency: str = Field(default="USD", alias="SHOPIFY_STORE_CURRENCY")
    shopify_webhook_secret: str = Field(default="", alias="SHOPIFY_WEBHOOK_SECRET")
    shopify_api_version: str = Field(default="2026-01", alias="SHOPIFY_API_VERSION")

    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")

    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    openai_api_version: str = Field(default="", alias="OPENAI_API_VERSION")
    azure_openai_chat_deployment_name: str = Field(default="", alias="AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    azure_openai_embedding_deployment_name: str = Field(default="", alias="AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

    reindex_admin_token: str = Field(default="", alias="REINDEX_ADMIN_TOKEN")

    default_search_top_k: int = Field(default=12, alias="DEFAULT_SEARCH_TOP_K")
    default_return_count: int = Field(default=6, alias="DEFAULT_RETURN_COUNT")

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_allowed_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def normalized_shopify_store_domain(self) -> str:
        return self.shopify_store_domain.strip().lower().replace("https://", "").replace("http://", "").rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
