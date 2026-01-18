"""Pluggable LLM client interfaces."""
from __future__ import annotations

from dataclasses import dataclass


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
