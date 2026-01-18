"""Legal document classifier agent implemented in AWS Strands."""
from __future__ import annotations

import logging

from app.core.config import settings
from app.agents.base import AgentResult, AwsStrandsAgent

logger = logging.getLogger(__name__)

class LegalClassifierAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        """Classify whether the document is a legal contract."""
        logger.info("legal_classifier_start document_id=%s", context.get("document_id"))
        document_text = self._read_document(document_path)
        prompt = self._render_prompt(
            "classify_legal.txt",
            context,
            document_text,
            schema_name=settings.mcp_schema_legal_classification or None,
        )
        agent = self._get_strands_agent(context)
        result = agent(prompt)
        raw_text = getattr(result, "message", str(result))
        payload = self._parse_json(raw_text, {"is_legal": False})
        is_legal = bool(payload.get("is_legal", False))
        logger.info("legal_classifier_done document_id=%s is_legal=%s", context.get("document_id"), is_legal)
        return AgentResult({"is_legal": is_legal})
