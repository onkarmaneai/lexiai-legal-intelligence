"""Contract type detection agent implemented in AWS Strands."""
from __future__ import annotations

import logging

from app.core.config import settings
from app.agents.base import AgentResult, AwsStrandsAgent

logger = logging.getLogger(__name__)

class ContractTypeAgent(AwsStrandsAgent):
    def run(self, document_path: str, context: dict) -> AgentResult:
        """Detect the contract type using the CUAD taxonomy."""
        logger.info("contract_type_start document_id=%s", context.get("document_id"))
        document_text = self._read_document(document_path)
        prompt = self._render_prompt(
            "detect_contract_type.txt",
            context,
            document_text,
            schema_name=settings.mcp_schema_contract_type or None,
        )
        agent = self._get_strands_agent(context)
        result = agent(prompt)
        raw_text = getattr(result, "message", str(result))
        payload = self._parse_json(raw_text, {"contract_type": "Unknown"})
        contract_type = payload.get("contract_type", "Unknown")
        logger.info("contract_type_done document_id=%s type=%s", context.get("document_id"), contract_type)
        return AgentResult({"contract_type": contract_type})
