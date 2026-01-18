"""Clause extraction agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class ClauseExtractionAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        return AgentResult(
            {
                "clauses": [
                    {
                        "clause_type": "termination",
                        "text": "...",
                        "confidence": 0.91,
                    }
                ]
            }
        )
