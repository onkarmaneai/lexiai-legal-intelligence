"""AWS Strands agent base abstractions."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from strands import Agent as StrandsAgent
from strands.models import BedrockModel, OpenAIModel

from app.core.config import settings
from app.services.llm_client import LangChainLLMClient, LLMClient
from app.services.prompt_loader import load_prompt, load_prompt_vars


@dataclass
class AgentResult:
    payload: dict


class AwsStrandsAgent:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._agent = self._build_strands_agent()
        self._llm = llm_client or LangChainLLMClient()

    def run(self, document_path: str, context: dict) -> AgentResult:
        raise NotImplementedError

    def _build_strands_agent(self) -> StrandsAgent:
        provider = settings.strands_provider.lower()
        if provider == "default":
            return StrandsAgent()
        if provider == "openai":
            client_args = {}
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client_args["api_key"] = api_key
            model = OpenAIModel(
                client_args=client_args,
                model_id=settings.strands_model_id,
                params={"temperature": settings.strands_temperature},
            )
            return StrandsAgent(model=model)
        if provider == "bedrock":
            model = BedrockModel(
                model_id=settings.strands_model_id,
                region_name=settings.strands_region,
                temperature=settings.strands_temperature,
            )
            return StrandsAgent(model=model)
        raise ValueError(f"Unsupported Strands provider: {settings.strands_provider}")

    def _read_document(self, document_path: str) -> str:
        return Path(document_path).read_text(encoding="utf-8", errors="ignore")

    def _render_prompt(self, prompt_name: str, context: dict, document_text: str) -> str:
        prompt = load_prompt(prompt_name)
        try:
            vars_payload = load_prompt_vars(prompt_name.replace(".txt", ".json"))
        except FileNotFoundError:
            vars_payload = {}
        prompt_vars = json.dumps(vars_payload, ensure_ascii=True)
        context_json = json.dumps(context, ensure_ascii=True)
        return "\n\n".join(
            [
                prompt,
                f"Prompt vars: {prompt_vars}",
                f"Context: {context_json}",
                f"Document:\n{document_text}",
            ]
        )

    def _parse_json(self, text: str, fallback: dict | list) -> dict | list:
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
