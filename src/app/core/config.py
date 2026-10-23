import os
from functools import lru_cache
from typing import List, Set
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration and environment variable validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Enterprise AI Document & Analytics Platform"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = Field(default="development", description="development, test, production")
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/rag_db",
        description="Database connection URL (PostgreSQL or SQLite fallback for tests)",
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_TIMEOUT_SECONDS: int = 5
    AUTO_APPLY_MIGRATIONS: bool = False

    # Ingestion Constraints
    MAX_UPLOAD_SIZE_BYTES: int = Field(
        default=50 * 1024 * 1024, description="Max upload size in bytes (50MB default)"
    )
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".pptx", ".csv"}
    MAX_INGESTION_RETRIES: int = 3

    # LLM & Orchestration (Secrets)
    GEMINI_API_KEY: str | None = Field(default=None, description="Google Gemini API Key")
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or not isinstance(v, str):
            raise ValueError("DATABASE_URL must be a non-empty connection string")
        # Ensure postgresql scheme uses psycopg or psycopg2 if standard postgresql://
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql+psycopg://", 1)
        elif v.startswith("postgresql://") and "+psycopg" not in v:
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v


@lru_cache()
def get_settings() -> Settings:
    """Returns cached singleton of Settings instance."""
    return Settings()
