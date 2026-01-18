"""Postgres persistence stub."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TaskLog:
    task_id: str
    agent: str
    status: str
    error: str | None = None
    metadata: dict[str, Any] | None = None


class PostgresClient:
    def save_task_log(self, log: TaskLog) -> None:
        # Placeholder for inserting log rows.
        return None

    def update_pipeline_state(self, document_id: str, step: str) -> None:
        # Placeholder for pipeline state persistence.
        return None

    def load_pipeline_state(self, document_id: str) -> str | None:
        # Placeholder for pipeline state retrieval.
        return None
