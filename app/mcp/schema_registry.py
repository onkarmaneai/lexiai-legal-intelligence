"""MCP schema registry client."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SchemaRecord:
    name: str
    payload: dict


class SchemaRegistryClient:
    def fetch_schema(self, name: str) -> SchemaRecord:
        raise NotImplementedError
