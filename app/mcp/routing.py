"""MCP model routing client."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RouteDecision:
    provider: str
    model: str


class RoutingClient:
    def resolve_route(self, tenant_id: str) -> RouteDecision:
        raise NotImplementedError
