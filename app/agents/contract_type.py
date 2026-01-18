"""Contract type detection agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class ContractTypeAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        document_text = self._read_document(document_path)
        prompt = self._render_prompt("detect_contract_type.txt", context, document_text)
        result = self._agent(prompt)
        raw_text = getattr(result, "message", str(result))
        payload = self._parse_json(raw_text, {"contract_type": "Unknown"})
        return AgentResult({"contract_type": payload.get("contract_type", "Unknown")})
