# Implementation Notes

This directory contains the modular Python implementation for the GenAI legal document intelligence platform.

## Highlights
- FastAPI for async ingestion (see `app/main.py` and `app/api/routes.py`).
- Celery orchestration (see `app/tasks/orchestrator.py`).
- AWS Strands agent stubs in `app/agents/`.
- Prompt + variable loading in `app/utils/prompt_loader.py`.
- MCP clients (prompt/schema/routing) implemented in `app/mcp/`.
