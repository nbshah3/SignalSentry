from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "SignalSentry API"
    environment: str = "local"
    debug: bool = True
    database_url: str = "sqlite:////var/lib/signalsentry/signalsentry.db"
    log_level: str = "INFO"
    allowed_origins: List[str] = ["*"]
    postmortem_export_dir: str = "./exports"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
