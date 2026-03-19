from __future__ import annotations

from openai import AzureOpenAI

from app.core.config import Settings
from app.core.errors import AppError


class AzureOpenAIService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _client(self) -> AzureOpenAI:
        if not self.settings.azure_openai_endpoint or not self.settings.azure_openai_api_key:
            raise AppError(
                code="CONFIG_ERROR",
                message="Azure OpenAI configuration is missing",
                status_code=500,
            )
        return AzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.openai_api_version,
        )

    def embed_text(self, text: str) -> list[float]:
        if not self.settings.azure_openai_embedding_deployment_name:
            raise AppError(
                code="CONFIG_ERROR",
                message="AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME is missing",
                status_code=500,
            )

        response = self._client().embeddings.create(
            model=self.settings.azure_openai_embedding_deployment_name,
            input=text,
            encoding_format="float",
        )
        return response.data[0].embedding
