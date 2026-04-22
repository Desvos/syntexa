"""FastAPI application entry point.

Includes auth and user management (Phase 7/US5) with protected routes.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from syntexa.api.middleware import require_auth
from syntexa.api.routes import agents as agents_routes
from syntexa.api.routes import auth as auth_routes
from syntexa.api.routes import compositions as compositions_routes
from syntexa.api.routes import credentials as credentials_routes
from syntexa.api.routes import listeners as listeners_routes
from syntexa.api.routes import llm_providers as llm_providers_routes
from syntexa.api.routes import repositories as repositories_routes
from syntexa.api.routes import roles as roles_routes
from syntexa.api.routes import settings as settings_routes
from syntexa.api.routes import swarms as swarms_routes
from syntexa.api.routes import users as users_routes
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

    # Public routes (no auth required)
    app.include_router(auth_routes.router, prefix=API_PREFIX)

    # Protected routes (auth required)
    app.include_router(
        roles_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        compositions_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        settings_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        swarms_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        users_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        credentials_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        llm_providers_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        agents_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        repositories_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
    app.include_router(
        listeners_routes.router,
        prefix=API_PREFIX,
        dependencies=[Depends(require_auth)],
    )
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
