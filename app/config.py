"""Application configuration module using Pydantic Settings."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Application
    app_env: str = "development"
    app_name: str = "Agentic Ticket Triage"
    log_level: str = "INFO"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    backend_api_url: str = "http://localhost:8000"

    # Database
    database_url: str = "sqlite:///./triage.db"

    # Knowledge Base
    kb_dir: str = "kb"

    # LLM Configuration
    llm_provider: str = "mock"  # "mock" or "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_temperature: float = 0.0

    # Human-in-the-loop thresholds
    confidence_threshold: float = 0.70

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
