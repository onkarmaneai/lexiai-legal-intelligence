"""Pluggable LLM client interfaces."""
from __future__ import annotations

import os
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class LLMResult:
    text: str
    metadata: dict[str, str] | None = None


class LLMClient:
    def generate(self, prompt: str) -> LLMResult:
        raise NotImplementedError


class StubLLMClient(LLMClient):
    def generate(self, prompt: str) -> LLMResult:
        return LLMResult(text="stub-response", metadata={"provider": "stub"})


class LangChainLLMClient(LLMClient):
    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        self.provider = (provider or settings.llm_provider).lower()
        self.model = model or settings.llm_model
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self._client = self._build_client()

    def _build_client(self):
        if self.provider == "openai":
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                model=self.model,
                temperature=self.temperature,
            )
        if self.provider == "bedrock":
            from langchain_aws import ChatBedrock

            return ChatBedrock(
                model_id=self.model,
                region_name=os.getenv("AWS_REGION", settings.strands_region),
                model_kwargs={"temperature": self.temperature},
            )
        raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate(self, prompt: str) -> LLMResult:
        response = self._client.invoke(prompt)
        text = getattr(response, "content", str(response))
        return LLMResult(
            text=text,
            metadata={
                "provider": self.provider,
                "model": self.model,
            },
        )
