"""AWS Strands agent base abstractions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentResult:
    payload: dict


class AwsStrandsAgent:
    def run(self, document_path: str, context: dict) -> AgentResult:
        raise NotImplementedError
