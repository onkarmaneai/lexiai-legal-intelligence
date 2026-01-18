"""Deduplication agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class DeduplicationAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        return AgentResult({"is_duplicate": False})
