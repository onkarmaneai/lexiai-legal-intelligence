"""MCP schema registry client."""
from __future__ import annotations

import json

from pydantic import BaseModel

from app.mcp.client import create_mcp_client, get_schema_mcp_config


class SchemaRecord(BaseModel):
    name: str
    payload: dict


class SchemaRegistryClient:
    def fetch_schema(self, name: str) -> SchemaRecord:
        """Fetch a JSON schema from an MCP resource."""
        config = get_schema_mcp_config()
        if not config:
            raise RuntimeError("MCP schema client not configured.")
        with create_mcp_client(config) as client:
            raw = client.read_resource_sync(name)
            payload = json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode("utf-8"))
            return SchemaRecord(name=name, payload=payload)
