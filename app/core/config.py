from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    app_name: str = Field(default="Campus Chemistry Vibe Engine V1")
    environment: str = Field(default="local")
    database_url: str = Field(
        default="postgresql+psycopg://campus_chemistry:campus_chemistry@localhost:5432/campus_chemistry"
    )
    create_tables_on_startup: bool = False
    log_level: str = "INFO"
    vibe_service_token: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            app_name=os.getenv("APP_NAME", "Campus Chemistry Vibe Engine V1"),
            environment=os.getenv("ENVIRONMENT", "local"),
            database_url=os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://campus_chemistry:campus_chemistry@localhost:5432/campus_chemistry",
            ),
            create_tables_on_startup=_bool_from_env("CREATE_TABLES_ON_STARTUP", False),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            vibe_service_token=os.getenv("VIBE_SERVICE_TOKEN") or None,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
