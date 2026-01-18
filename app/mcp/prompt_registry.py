"""MCP prompt registry client."""
from __future__ import annotations

from pydantic import BaseModel

from app.mcp.client import create_mcp_client, get_prompt_mcp_config


class PromptRecord(BaseModel):
    name: str
    template: str


class PromptRegistryClient:
    def fetch_prompt(self, name: str) -> PromptRecord:
        """Fetch a prompt template from an MCP server."""
        config = get_prompt_mcp_config()
        if not config:
            raise RuntimeError("MCP prompt client not configured.")
        with create_mcp_client(config) as client:
            prompt = client.get_prompt_sync(name, {})
            if hasattr(prompt, "messages") and prompt.messages:
                content = prompt.messages[0].content
            else:
                content = str(prompt)
            return PromptRecord(name=name, template=content)
