"""Application settings loaded from the process environment and optional `.env` file."""

import enum
from functools import lru_cache
from typing import Annotated

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import constants


class Environment(str, enum.Enum):
    """Deployment tier; values match `app.core.constants` and `ENVIRONMENT` in `.env`."""
    DEV = constants.DEV
    STAGING = constants.STAGING
    PROD = constants.PROD


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection and pool sizing; env vars use the `DATABASE_` prefix."""
    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    url: PostgresDsn
    pool_size: int = Field(default=20, ge=1, le=128)
    max_overflow: int = Field(default=10, ge=0, le=256)


class Settings(BaseSettings):
    """Root service configuration: API metadata, database group, and HTTP server options."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    project_name: str = Field(default=constants.PROJECT_NAME)
    environment: Environment = Field(default=Environment.DEV)
    api_v1_str: str = Field(default=constants.API_V1_STR)
    debug: bool = Field(default=False)

    database: Annotated[DatabaseSettings, Field(default_factory=DatabaseSettings)]

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001, ge=1, le=65535)
    uvicorn_reload: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    log_json_file: str | None = Field(
        default="logs/user-service.jsonl",
        description="Append JSON log lines for ELK/Filebeat; empty env disables file sink.",
    )

    @field_validator("log_json_file", mode="before")
    @classmethod
    def _coerce_log_json_file(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        return str(value).strip() if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    """Return a process-wide cached `Settings` instance (refresh via `get_settings.cache_clear()`)."""
    return Settings()
