"""Centralized application configuration loaded from environment variables."""

import json
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

MIN_JWT_SECRET_LENGTH = 32  # HS256 keys shorter than this are rejected (RFC 7518 §3.2)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./lexlens.db"
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 20
    rate_limit_per_minute: int = 20
    document_retention_hours: int = 24

    # Authentication
    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    supabase_jwks_url: str | None = None
    auth_dev_login_enabled: bool = False
    auth_dev_jwt_secret: str | None = None

    # Google Cloud
    gcp_project_id: str | None = None
    gcs_bucket: str | None = None
    local_storage_dir: str = "./.local_storage"
    document_ai_location: str = "us"
    document_ai_processor_id: str | None = None

    # Built Vite assets. Empty keeps the API-only local workflow.
    frontend_dist_dir: str = ""

    # Gemini
    gemini_api_key: str | None = None
    gemini_analysis_model: str = "gemini-3-flash"
    gemini_chat_model: str = "gemini-3-flash"
    # Tried in order after the primary model is unavailable. Comma-separated model ids.
    gemini_fallback_models: str = "gemini-3.1-pro"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _normalize_origins(cls, value: object) -> str:
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        return str(value) if value is not None else "http://localhost:5173"

    def gemini_fallback_model_list(self) -> list[str]:
        return [model.strip() for model in self.gemini_fallback_models.split(",") if model.strip()]

    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw.startswith("["):
            parsed = json.loads(raw)
            return [str(item).strip() for item in parsed if str(item).strip()]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def dev_login_allowed(self) -> bool:
        """Dev login is only ever permitted outside production and with a sufficiently long secret."""
        secret_ok = bool(self.auth_dev_jwt_secret) and len(self.auth_dev_jwt_secret) >= MIN_JWT_SECRET_LENGTH
        return self.auth_dev_login_enabled and not self.is_production and secret_ok

    @property
    def uses_gcs(self) -> bool:
        return bool(self.gcs_bucket)

    @property
    def uses_document_ai(self) -> bool:
        return bool(self.gcp_project_id and self.document_ai_processor_id)

    @property
    def uses_gemini(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
