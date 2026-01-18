"""Celery orchestration for the legal intelligence pipeline."""
from __future__ import annotations

from pathlib import Path

from celery import Celery

from app.agents.clause_extractor import ClauseExtractionAgent
from app.agents.contract_type import ContractTypeAgent
from app.agents.deduplicator import DeduplicationAgent
from app.agents.legal_classifier import LegalClassifierAgent
from app.agents.ner_agent import NerAgent
from app.core.config import settings
from app.services.elastic import ElasticClient
from app.services.postgres import PostgresClient, TaskLog
from app.services.redis import RedisClient
from app.utils.hashing import sha256_file

celery_app = Celery("lexiai", broker=settings.broker_url, backend=settings.backend_url)

PIPELINE_STEPS = [
    "classification",
    "deduplication",
    "contract_type",
    "clauses",
    "ner",
]


def _step_index(step: str | None) -> int:
    if step is None:
        return -1
    return PIPELINE_STEPS.index(step)


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": settings.max_retries, "countdown": settings.retry_countdown},
)
def process_legal_document(self, document_id: str, document_path: str) -> None:
    postgres = PostgresClient()
    redis = RedisClient()
    elastic = ElasticClient()

    context = {"document_id": document_id}
    current_step = postgres.load_pipeline_state(document_id)
    document_path_obj = Path(document_path)

    def log(agent: str, status: str, error: str | None = None) -> None:
        postgres.save_task_log(TaskLog(task_id=self.request.id, agent=agent, status=status, error=error))

    if _step_index(current_step) < _step_index("classification"):
        classifier = LegalClassifierAgent()
        result = classifier.run(document_path, context)
        log("legal_classifier", "completed")
        if not result.payload.get("is_legal"):
            return
        postgres.update_pipeline_state(document_id, "classification")
        current_step = "classification"

    if _step_index(current_step) < _step_index("deduplication"):
        document_hash = sha256_file(document_path_obj)
        if redis.has_document_hash(document_hash):
            log("deduplication", "duplicate")
            return
        deduplicator = DeduplicationAgent()
        deduplicator.run(document_path, context)
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
        clause_agent = ClauseExtractionAgent()
        clauses = clause_agent.run(document_path, context).payload.get("clauses", [])
        for clause in clauses:
            elastic.index(
                "legal_clauses_index",
                {"document_id": document_id, **context, "clause_text": clause.get("text"), **clause},
            )
        postgres.update_pipeline_state(document_id, "clauses")
        current_step = "clauses"
        log("clauses", "completed")

    if _step_index(current_step) < _step_index("ner"):
        ner_agent = NerAgent()
        entities = ner_agent.run(document_path, context).payload.get("entities", [])
        for entity in entities:
            elastic.index("legal_ner_index", {"document_id": document_id, **entity})
        postgres.update_pipeline_state(document_id, "ner")
        current_step = "ner"
        log("ner", "completed")

    log("orchestrator", "completed")
