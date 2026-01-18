"""NER extraction agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class NerAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        return AgentResult(
            {
                "entities": [
                    {
                        "entity_type": "PARTY",
                        "entity_value": "ABC Corp",
                        "start_offset": 120,
                        "end_offset": 128,
                    }
                ]
            }
        )
