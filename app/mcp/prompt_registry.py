"""MCP prompt registry client."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptRecord:
    name: str
    template: str


class PromptRegistryClient:
    def fetch_prompt(self, name: str) -> PromptRecord:
        # Placeholder: fetch prompt template from MCP server.
        raise NotImplementedError
