"""Redis broker access stub."""
from __future__ import annotations


class RedisClient:
    def cache_document_hash(self, document_hash: str) -> None:
        return None

    def has_document_hash(self, document_hash: str) -> bool:
        return False
