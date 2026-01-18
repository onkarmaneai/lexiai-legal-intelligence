"""Legal document classifier agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class LegalClassifierAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        document_text = self._read_document(document_path)
        prompt = self._render_prompt("classify_legal.txt", context, document_text)
        result = self._agent(prompt)
        raw_text = getattr(result, "message", str(result))
        payload = self._parse_json(raw_text, {"is_legal": False})
        return AgentResult({"is_legal": bool(payload.get("is_legal", False))})
