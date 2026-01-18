"""Pipeline state tracking."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PipelineState:
    document_id: str
    last_completed_step: str | None = None
