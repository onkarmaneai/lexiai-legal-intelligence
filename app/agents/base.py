"""AWS Strands agent base abstractions."""
from __future__ import annotations

import json
import os
from pathlib import Path

from strands import Agent as StrandsAgent
from strands.models import BedrockModel, OpenAIModel
from pydantic import BaseModel

from app.core.config import settings
from app.mcp.prompt_registry import PromptRegistryClient
from app.mcp.schema_registry import SchemaRegistryClient
from app.mcp.routing import RoutingClient
from app.services.llm_client import LangChainLLMClient, LLMClient
from app.utils.prompt_loader import load_prompt, load_prompt_vars


class AgentResult(BaseModel):
    payload: dict


class AwsStrandsAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize Strands and LangChain clients for agent execution."""
        self._agent = self._build_strands_agent()
        self._llm = llm_client or LangChainLLMClient()
        self._router = RoutingClient()
        self._prompt_registry = PromptRegistryClient()
        self._schema_registry = SchemaRegistryClient()

    def run(self, document_path: str, context: dict) -> AgentResult:
        raise NotImplementedError

    def _build_strands_agent(self) -> StrandsAgent:
        """Build the default Strands agent from environment settings."""
        return self._build_strands_agent_for(settings.strands_provider, settings.strands_model_id)

    def _build_strands_agent_for(self, provider: str, model_id: str) -> StrandsAgent:
        """Build a Strands agent for a specific provider/model."""
        provider = provider.lower()
        if provider == "default":
            return StrandsAgent()
        if provider == "openai":
            client_args = {}
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client_args["api_key"] = api_key
            model = OpenAIModel(
                client_args=client_args,
                model_id=model_id,
                params={"temperature": settings.strands_temperature},
            )
            return StrandsAgent(model=model)
        if provider == "bedrock":
            model = BedrockModel(
                model_id=model_id,
                region_name=settings.strands_region,
                temperature=settings.strands_temperature,
            )
            return StrandsAgent(model=model)
        raise ValueError(f"Unsupported Strands provider: {provider}")

    def _get_strands_agent(self, context: dict) -> StrandsAgent:
        """Resolve the Strands agent from MCP routing (tenant-aware)."""
        tenant_id = context.get("tenant_id")
        if tenant_id:
            decision = self._router.resolve_route(str(tenant_id))
            if decision.provider in {"openai", "bedrock"}:
                return self._build_strands_agent_for(decision.provider, decision.model)
        return self._agent

    def _get_llm(self, context: dict) -> LLMClient:
        """Resolve the LangChain client from MCP routing (tenant-aware)."""
        tenant_id = context.get("tenant_id")
        if tenant_id:
            decision = self._router.resolve_route(str(tenant_id))
            return LangChainLLMClient(provider=decision.provider, model=decision.model)
        return self._llm

    def _read_document(self, document_path: str) -> str:
        """Load a document from disk as text."""
        return Path(document_path).read_text(encoding="utf-8", errors="ignore")

    def _render_prompt(
        self,
        prompt_name: str,
        context: dict,
        document_text: str,
        schema_name: str | None = None,
    ) -> str:
        """Combine prompt templates, context, and schema into a single prompt."""
        prompt = self._load_prompt(prompt_name)
        try:
            vars_payload = load_prompt_vars(prompt_name.replace(".txt", ".json"))
        except FileNotFoundError:
            vars_payload = {}
        prompt_vars = json.dumps(vars_payload, ensure_ascii=True)
        context_json = json.dumps(context, ensure_ascii=True)
        schema_payload = self._load_schema(schema_name)
        schema_json = json.dumps(schema_payload, ensure_ascii=True) if schema_payload else None
        parts = [
            prompt,
            f"Prompt vars: {prompt_vars}",
            f"Context: {context_json}",
        ]
        if schema_json:
            parts.append(f"Schema: {schema_json}")
        parts.append(f"Document:\n{document_text}")
        return "\n\n".join(
            parts
        )

    def _load_prompt(self, prompt_name: str) -> str:
        """Fetch a prompt from MCP if configured, otherwise from disk."""
        try:
            record = self._prompt_registry.fetch_prompt(prompt_name)
            return record.template
        except Exception:
            return load_prompt(prompt_name)

    def _load_schema(self, schema_name: str | None) -> dict | None:
        """Fetch a JSON schema from MCP if configured."""
        if not schema_name:
            return None
        try:
            record = self._schema_registry.fetch_schema(schema_name)
            return record.payload
        except Exception:
            return None

    def _parse_json(self, text: str, fallback: dict | list) -> dict | list:
        """Parse JSON from model output with a safe fallback."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            for start, end in (("{", "}"), ("[", "]")):
                start_idx = text.find(start)
                end_idx = text.rfind(end)
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    try:
                        return json.loads(text[start_idx : end_idx + 1])
                    except json.JSONDecodeError:
                        continue
        return fallback
