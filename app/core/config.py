"""Application configuration utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    api_title: str = os.getenv("API_TITLE", "LexiAI Legal Intelligence")
    broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    backend_url: str = os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/1")
    postgres_dsn: str = os.getenv("POSTGRES_DSN", "postgresql://lexiai:lexiai@postgres:5432/lexiai")
    elastic_url: str = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
    prompt_dir: str = os.getenv("PROMPT_DIR", "app/prompts")
    prompt_vars_dir: str = os.getenv("PROMPT_VARS_DIR", "app/prompt_vars")
    max_retries: int = int(os.getenv("PIPELINE_MAX_RETRIES", "5"))
    retry_countdown: int = int(os.getenv("PIPELINE_RETRY_COUNTDOWN", "60"))


settings = Settings()
