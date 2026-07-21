"""Application settings loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = Field(default="postgresql+asyncpg://de_ai_kb:de_ai_kb@localhost:5432/de_ai_kb")
    database_url_sync: str = Field(default="postgresql+psycopg://de_ai_kb:de_ai_kb@localhost:5432/de_ai_kb")
    test_database_url: str = Field(
        default="postgresql+asyncpg://de_ai_kb:de_ai_kb@localhost:5432/de_ai_kb_test"
    )
    test_database_url_sync: str = Field(
        default="postgresql+psycopg://de_ai_kb:de_ai_kb@localhost:5432/de_ai_kb_test"
    )
    dev_api_key: str = Field(default="change-me-dev-key")
    object_storage_local_root: str = Field(default="./.data/object-storage")
    log_level: str = Field(default="INFO")
    cors_allowed_origins: str = Field(
        default="",
        description=(
            "Comma-separated list of allowed browser origins (e.g. the local "
            "Next.js dev server). Empty disables CORS entirely — restrictive "
            "by default, since this backend has no browser frontend attached "
            "unless explicitly configured."
        ),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
