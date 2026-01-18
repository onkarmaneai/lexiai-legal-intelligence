"""ElasticSearch indexing stub."""
from __future__ import annotations

from typing import Any


class ElasticClient:
    def index(self, index: str, document: dict[str, Any]) -> None:
        # Placeholder for ElasticSearch indexing.
        return None
