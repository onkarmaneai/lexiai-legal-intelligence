"""Postgres + Redis persistence helpers."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import asyncpg
import redis
from pydantic import BaseModel

from app.core.config import settings


class TaskLog(BaseModel):
    task_id: str
    agent: str
    status: str
    error: str | None = None
    metadata: dict[str, Any] | None = None


class PostgresClient:
    def __init__(self, dsn: str | None = None) -> None:
        """Create a Postgres client for task logs and pipeline state."""
        self._dsn = dsn or settings.postgres_dsn
        self._schema_ready = False

    def save_task_log(self, log: TaskLog) -> None:
        """Persist a task log entry."""
        self._run(self._save_task_log(log))

    def update_pipeline_state(self, document_id: str, step: str) -> None:
        """Persist the latest pipeline step for a document."""
        self._run(self._update_pipeline_state(document_id, step))

    def load_pipeline_state(self, document_id: str) -> str | None:
        """Load the last completed step for a document, if any."""
        return self._run(self._load_pipeline_state(document_id))

    def _run(self, coro):
        """Run an async Postgres operation from a sync context."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        raise RuntimeError("PostgresClient used from an active event loop; use async methods instead.")

    async def _connect(self) -> asyncpg.Connection:
        """Connect to Postgres and ensure required tables exist."""
        conn = await asyncpg.connect(self._dsn)
        if not self._schema_ready:
            await self._ensure_schema(conn)
            self._schema_ready = True
        return conn

    async def _ensure_schema(self, conn: asyncpg.Connection) -> None:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_logs (
                id BIGSERIAL PRIMARY KEY,
                task_id TEXT NOT NULL,
                agent TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                metadata JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline_state (
                document_id TEXT PRIMARY KEY,
                last_completed_step TEXT,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
            """
        )

    async def _save_task_log(self, log: TaskLog) -> None:
        """Insert a task log record into Postgres."""
        conn = await self._connect()
        try:
            await conn.execute(
                """
                INSERT INTO task_logs (task_id, agent, status, error, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                log.task_id,
                log.agent,
                log.status,
                log.error,
                json.dumps(log.metadata) if log.metadata is not None else None,
            )
        finally:
            await conn.close()

    async def _update_pipeline_state(self, document_id: str, step: str) -> None:
        """Upsert the latest pipeline step into Postgres."""
        conn = await self._connect()
        try:
            await conn.execute(
                """
                INSERT INTO pipeline_state (document_id, last_completed_step)
                VALUES ($1, $2)
                ON CONFLICT (document_id)
                DO UPDATE SET last_completed_step = EXCLUDED.last_completed_step, updated_at = NOW()
                """,
                document_id,
                step,
            )
        finally:
            await conn.close()

    async def _load_pipeline_state(self, document_id: str) -> str | None:
        """Fetch the latest pipeline step from Postgres."""
        conn = await self._connect()
        try:
            row = await conn.fetchrow(
                "SELECT last_completed_step FROM pipeline_state WHERE document_id = $1",
                document_id,
            )
            return row["last_completed_step"] if row else None
        finally:
            await conn.close()


class RedisClient:
    def __init__(self, url: str | None = None) -> None:
        """Create a Redis client for deduplication."""
        self._client = redis.Redis.from_url(url or settings.broker_url)

    def cache_document_hash(self, document_hash: str) -> None:
        """Store a document hash to mark it as processed."""
        self._client.set(document_hash, 1)

    def has_document_hash(self, document_hash: str) -> bool:
        """Check whether a document hash already exists."""
        return bool(self._client.exists(document_hash))
