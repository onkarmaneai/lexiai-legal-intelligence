"""Application configuration utilities."""
from __future__ import annotations

import os

from pydantic import BaseModel


class Settings(BaseModel):
    api_title: str = os.getenv("API_TITLE", "LexiAI Legal Intelligence")
    broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    backend_url: str = os.getenv("CELERY_BACKEND_URL", "redis://redis:6379/1")
    postgres_dsn: str = os.getenv("POSTGRES_DSN", "postgresql://lexiai:lexiai@postgres:5432/lexiai")
    elastic_url: str = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
    prompt_dir: str = os.getenv("PROMPT_DIR", "app/prompts")
    prompt_vars_dir: str = os.getenv("PROMPT_VARS_DIR", "app/prompt_vars")
    max_retries: int = int(os.getenv("PIPELINE_MAX_RETRIES", "5"))
    retry_countdown: int = int(os.getenv("PIPELINE_RETRY_COUNTDOWN", "60"))
    strands_provider: str = os.getenv("STRANDS_PROVIDER", "default")
    strands_model_id: str = os.getenv("STRANDS_MODEL_ID", "us.anthropic.claude-sonnet-4-20250514-v1:0")
    strands_region: str = os.getenv("STRANDS_REGION", "us-west-2")
    strands_temperature: float = float(os.getenv("STRANDS_TEMPERATURE", "0.2"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    mcp_command: str = os.getenv("MCP_COMMAND", "")
    mcp_args: str = os.getenv("MCP_ARGS", "")
    mcp_prompt_command: str = os.getenv("MCP_PROMPT_COMMAND", "")
    mcp_prompt_args: str = os.getenv("MCP_PROMPT_ARGS", "")
    mcp_schema_command: str = os.getenv("MCP_SCHEMA_COMMAND", "")
    mcp_schema_args: str = os.getenv("MCP_SCHEMA_ARGS", "")
    mcp_routing_command: str = os.getenv("MCP_ROUTING_COMMAND", "")
    mcp_routing_args: str = os.getenv("MCP_ROUTING_ARGS", "")
    mcp_schema_legal_classification: str = os.getenv("MCP_SCHEMA_LEGAL_CLASSIFICATION", "")
    mcp_schema_contract_type: str = os.getenv("MCP_SCHEMA_CONTRACT_TYPE", "")
    mcp_schema_clause_extraction: str = os.getenv("MCP_SCHEMA_CLAUSE_EXTRACTION", "")
    mcp_schema_ner: str = os.getenv("MCP_SCHEMA_NER", "")


settings = Settings()
