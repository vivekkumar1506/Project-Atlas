import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine base directory (workspace root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Project Atlas - AI Market Research Report Copilot"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Security
    api_key: str = "atlas_dev_secret_key_2026"

    # MySQL Configuration
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "project_atlas"
    mysql_pool_size: int = 5
    mysql_pool_recycle: int = 3600

    # LLM Settings
    llm_provider: str = "openai"
    openai_api_key: Optional[str] = None
    llm_model: str = "gpt-4o-mini"

    # Vector DB Settings
    vector_store_type: str = "chroma"
    chroma_persist_directory: str = "./vector_store"

    # Agent Guardrail Settings
    confidence_threshold: float = 0.75

    @property
    def database_url(self) -> str:
        """Construct a safe SQLAlchemy connection URL with quoted credentials."""
        encoded_user = quote_plus(self.mysql_user)
        encoded_password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}@"
            f"{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def server_database_url(self) -> str:
        """Database URL without specific database (used for checking or creating the database)."""
        encoded_user = quote_plus(self.mysql_user)
        encoded_password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{encoded_user}:{encoded_password}@"
            f"{self.mysql_host}:{self.mysql_port}?charset=utf8mb4"
        )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
