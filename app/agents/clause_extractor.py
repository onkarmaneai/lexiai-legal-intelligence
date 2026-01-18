"""Clause extraction agent implemented in AWS Strands."""
from __future__ import annotations

import logging

from app.core.config import settings
from app.agents.base import AgentResult, AwsStrandsAgent

logger = logging.getLogger(__name__)

class ClauseExtractionAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        """Extract key clauses from the contract using the configured LLM."""
        logger.info("clause_extraction_start document_id=%s", context.get("document_id"))
        document_text = self._read_document(document_path)
        prompt = self._render_prompt(
            "extract_clauses.txt",
            context,
            document_text,
            schema_name=settings.mcp_schema_clause_extraction or None,
        )
        response = self._get_llm(context).generate(prompt)
        parsed = self._parse_json(response.text, [])
        if isinstance(parsed, dict):
            clauses = parsed.get("clauses", [])
        else:
            clauses = parsed
        logger.info("clause_extraction_done document_id=%s count=%s", context.get("document_id"), len(clauses))
        return AgentResult({"clauses": clauses})
