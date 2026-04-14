"""FastAPI application entry point.

Minimal shell for Phase 4. Auth middleware (Phase 7/US5) and other user
story routers (US3–US5) plug in here as they land.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from syntexa.api.routes import compositions as compositions_routes
from syntexa.api.routes import roles as roles_routes
from syntexa.api.routes import settings as settings_routes
from syntexa.api.routes import swarms as swarms_routes
from syntexa.config import get_settings
from syntexa.models import init_engine

logger = logging.getLogger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """Initialize DB engine on startup. Migrations are the operator's job
    (`alembic upgrade head`); we don't auto-create tables in production."""
    settings = get_settings()
    init_engine(settings.database_url)
    logger.info("syntexa-api started against %s", settings.database_url)
    yield


def create_app() -> FastAPI:
    """App factory. Used by both the console script and tests — tests call
    init_engine() themselves, which is safe to re-init."""
    app = FastAPI(
        title="Syntexa API",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": app.version}

    app.include_router(roles_routes.router, prefix=API_PREFIX)
    app.include_router(compositions_routes.router, prefix=API_PREFIX)
    app.include_router(settings_routes.router, prefix=API_PREFIX)
    app.include_router(swarms_routes.router, prefix=API_PREFIX)
    return app


app = create_app()


def run() -> None:
    """Console-script entry point (`syntexa-api`)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "syntexa.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )
