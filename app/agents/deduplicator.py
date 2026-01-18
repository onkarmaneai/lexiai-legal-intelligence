"""Deduplication agent implemented in AWS Strands."""
from __future__ import annotations

import logging

from app.agents.base import AgentResult, AwsStrandsAgent
from app.services.storage import RedisClient
from app.utils.hashing import sha256_file

logger = logging.getLogger(__name__)

class DeduplicationAgent(AwsStrandsAgent):
    def __init__(self, redis_client: RedisClient | None = None) -> None:
        """Create a deduplication agent with an optional Redis backend."""
        super().__init__()
        self._redis = redis_client

    def run(self, document_path: str, context: dict) -> AgentResult:
        """Compute a SHA-256 hash and check for duplicates in Redis."""
        logger.info("dedup_start document_id=%s", context.get("document_id"))
        document_hash = sha256_file(document_path)
        is_duplicate = bool(self._redis and self._redis.has_document_hash(document_hash))
        logger.info(
            "dedup_done document_id=%s duplicate=%s",
            context.get("document_id"),
            is_duplicate,
        )
        return AgentResult({"is_duplicate": is_duplicate, "document_hash": document_hash})
