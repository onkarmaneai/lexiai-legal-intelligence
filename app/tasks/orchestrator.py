"""Celery orchestration for the legal intelligence pipeline."""
from __future__ import annotations

import logging

from celery import Celery

from app.agents.clause_extractor import ClauseExtractionAgent
from app.agents.contract_type import ContractTypeAgent
from app.agents.deduplicator import DeduplicationAgent
from app.agents.legal_classifier import LegalClassifierAgent
from app.agents.ner_agent import NerAgent
from app.core.config import settings
from app.services.elastic import ElasticClient
from app.services.storage import PostgresClient, RedisClient, TaskLog

celery_app = Celery("lexiai", broker=settings.broker_url, backend=settings.backend_url)
logger = logging.getLogger(__name__)

PIPELINE_STEPS = [
    "classification",
    "deduplication",
    "contract_type",
    "clauses",
    "ner",
]


def _step_index(step: str | None) -> int:
    """Return a stable index for pipeline steps, or -1 when unset."""
    if step is None:
        return -1
    return PIPELINE_STEPS.index(step)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.max_retries, "countdown": settings.retry_countdown},
)
def process_legal_document(self, document_id: str, document_path: str, extraction_mode: str = "all") -> None:
    """Run the contract intelligence pipeline for a single document."""
    postgres = PostgresClient()
    redis = RedisClient()
    elastic = ElasticClient()

    if extraction_mode not in {"all", "ner-only"}:
        raise ValueError("Invalid extraction_mode. Use 'all' or 'ner-only'.")
    context = {"document_id": document_id, "extraction_mode": extraction_mode}
    current_step = postgres.load_pipeline_state(document_id)

    def log(agent: str, status: str, error: str | None = None) -> None:
        """Persist task execution status to Postgres."""
        postgres.save_task_log(TaskLog(task_id=self.request.id, agent=agent, status=status, error=error))

    logger.info(
        "pipeline_start document_id=%s task_id=%s mode=%s",
        document_id,
        self.request.id,
        extraction_mode,
    )

    if _step_index(current_step) < _step_index("classification"):
        classifier = LegalClassifierAgent()
        result = classifier.run(document_path, context)
        log("legal_classifier", "completed")
        if not result.payload.get("is_legal"):
            logger.info("pipeline_stop_non_legal document_id=%s", document_id)
            return
        postgres.update_pipeline_state(document_id, "classification")
        current_step = "classification"

    if _step_index(current_step) < _step_index("deduplication"):
        deduplicator = DeduplicationAgent(redis_client=redis)
        dedup_result = deduplicator.run(document_path, context)
        document_hash = dedup_result.payload.get("document_hash")
        if dedup_result.payload.get("is_duplicate"):
            log("deduplication", "duplicate")
            logger.info("pipeline_stop_duplicate document_id=%s", document_id)
            return
        if document_hash:
            redis.cache_document_hash(document_hash)
        postgres.update_pipeline_state(document_id, "deduplication")
        current_step = "deduplication"
        log("deduplication", "completed")

    if _step_index(current_step) < _step_index("contract_type"):
        contract_type_agent = ContractTypeAgent()
        contract_type = contract_type_agent.run(document_path, context)
        context.update(contract_type.payload)
        postgres.update_pipeline_state(document_id, "contract_type")
        current_step = "contract_type"
        log("contract_type", "completed")

    if _step_index(current_step) < _step_index("clauses"):
        if extraction_mode == "all":
            clause_agent = ClauseExtractionAgent()
            clauses = clause_agent.run(document_path, context).payload.get("clauses", [])
            for clause in clauses:
                elastic.index(
                    "legal_clauses_index",
                    {"document_id": document_id, **context, "clause_text": clause.get("text"), **clause},
                )
            log("clauses", "completed")
            logger.info("clauses_indexed document_id=%s count=%s", document_id, len(clauses))
        else:
            log("clauses", "skipped")
            logger.info("clauses_skipped document_id=%s", document_id)
        postgres.update_pipeline_state(document_id, "clauses")
        current_step = "clauses"

    if _step_index(current_step) < _step_index("ner"):
        ner_agent = NerAgent()
        entities = ner_agent.run(document_path, context).payload.get("entities", [])
        for entity in entities:
            elastic.index("legal_ner_index", {"document_id": document_id, **entity})
        postgres.update_pipeline_state(document_id, "ner")
        current_step = "ner"
        log("ner", "completed")
        logger.info("ner_indexed document_id=%s count=%s", document_id, len(entities))

    log("orchestrator", "completed")
    logger.info("pipeline_complete document_id=%s", document_id)
