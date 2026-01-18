"""FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="LexiAI Legal Intelligence")
    app.include_router(router)
    return app


app = create_app()
