"""Clause extraction agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class ClauseExtractionAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        document_text = self._read_document(document_path)
        prompt = self._render_prompt("extract_clauses.txt", context, document_text)
        response = self._llm.generate(prompt)
        parsed = self._parse_json(response.text, [])
        if isinstance(parsed, dict):
            clauses = parsed.get("clauses", [])
        else:
            clauses = parsed
        return AgentResult({"clauses": clauses})
