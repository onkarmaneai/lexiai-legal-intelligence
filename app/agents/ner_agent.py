"""NER extraction agent implemented in AWS Strands."""
from __future__ import annotations

import logging

from transformers import pipeline

from app.agents.base import AgentResult, AwsStrandsAgent

logger = logging.getLogger(__name__)

class NerAgent(AwsStrandsAgent):
    _ner_pipeline = None

    @classmethod
    def _get_pipeline(cls):
        """Load and cache the Transformers NER pipeline."""
        if cls._ner_pipeline is None:
            cls._ner_pipeline = pipeline("ner", aggregation_strategy="simple")
        return cls._ner_pipeline

    def run(self, document_path: str, context: dict) -> AgentResult:
        """Extract entities using a Transformer-based NER pipeline."""
        logger.info("ner_start document_id=%s", context.get("document_id"))
        document_text = self._read_document(document_path)
        extractor = self._get_pipeline()
        extracted = extractor(document_text)
        entities = [
            {
                "entity_type": item.get("entity_group"),
                "entity_value": item.get("word"),
                "start_offset": item.get("start"),
                "end_offset": item.get("end"),
            }
            for item in extracted
        ]
        logger.info("ner_done document_id=%s count=%s", context.get("document_id"), len(entities))
        return AgentResult({"entities": entities})
