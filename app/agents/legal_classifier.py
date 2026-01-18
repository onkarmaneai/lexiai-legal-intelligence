"""Legal document classifier agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class LegalClassifierAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        return AgentResult({"is_legal": True})
