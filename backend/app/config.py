"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for DocuSpider AI.

    The default provider is ``local`` so the engine runs fully offline and free.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "local"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    spider_delay_seconds: float = 1.8
    max_upload_mb: int = 25

    frontend_origin: str = "http://localhost:3000"

    @property
    def effective_provider(self) -> str:
        """Resolve the provider, falling back to local when no key is present."""
        provider = self.llm_provider.strip().lower()
        if provider == "openai" and self.openai_api_key:
            return "openai"
        if provider == "gemini" and self.gemini_api_key:
            return "gemini"
        if provider == "auto":
            if self.openai_api_key:
                return "openai"
            if self.gemini_api_key:
                return "gemini"
        return "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
