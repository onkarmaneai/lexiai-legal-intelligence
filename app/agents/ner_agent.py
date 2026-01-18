"""NER extraction agent implemented in AWS Strands."""
from __future__ import annotations

from app.agents.base import AgentResult, AwsStrandsAgent


class NerAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        document_text = self._read_document(document_path)
        prompt = self._render_prompt("extract_entities.txt", context, document_text)
        response = self._llm.generate(prompt)
        parsed = self._parse_json(response.text, [])
        if isinstance(parsed, dict):
            entities = parsed.get("entities", [])
        else:
            entities = parsed
        return AgentResult({"entities": entities})
