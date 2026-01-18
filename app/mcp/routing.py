"""MCP model routing client."""
from __future__ import annotations

import json

from pydantic import BaseModel

from app.core.config import settings
from app.mcp.client import create_mcp_client, get_routing_mcp_config


class RouteDecision(BaseModel):
    provider: str
    model: str


class RoutingClient:
    def resolve_route(self, tenant_id: str) -> RouteDecision:
        """Resolve model routing for a tenant via MCP, with settings fallback."""
        config = get_routing_mcp_config()
        if not config:
            return RouteDecision(provider=settings.llm_provider, model=settings.llm_model)
        with create_mcp_client(config) as client:
            raw = client.read_resource_sync(tenant_id)
            payload = json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode("utf-8"))
            return RouteDecision(provider=payload.get("provider"), model=payload.get("model"))
