"""Shared MCP client utilities."""
from __future__ import annotations

from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
from pydantic import BaseModel

from app.core.config import settings


class MCPConfig(BaseModel):
    command: str
    args: list[str]


def _parse_args(raw: str) -> list[str]:
    """Split comma-separated args for stdio MCP servers."""
    return [arg.strip() for arg in raw.split(",") if arg.strip()]


def _get_config(command: str, args: str) -> MCPConfig | None:
    """Return MCP config when a command is provided."""
    if not command:
        return None
    return MCPConfig(command=command, args=_parse_args(args))


def get_prompt_mcp_config() -> MCPConfig | None:
    """Resolve MCP config for prompt registry access."""
    return _get_config(
        settings.mcp_prompt_command or settings.mcp_command,
        settings.mcp_prompt_args or settings.mcp_args,
    )


def get_schema_mcp_config() -> MCPConfig | None:
    """Resolve MCP config for schema registry access."""
    return _get_config(
        settings.mcp_schema_command or settings.mcp_command,
        settings.mcp_schema_args or settings.mcp_args,
    )


def get_routing_mcp_config() -> MCPConfig | None:
    """Resolve MCP config for routing lookups."""
    return _get_config(
        settings.mcp_routing_command or settings.mcp_command,
        settings.mcp_routing_args or settings.mcp_args,
    )


def create_mcp_client(config: MCPConfig) -> MCPClient:
    """Create a Strands MCP client from stdio server configuration."""
    return MCPClient(
        lambda: stdio_client(
            StdioServerParameters(command=config.command, args=config.args)
        )
    )
