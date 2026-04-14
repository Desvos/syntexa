"""Pytest configuration and fixtures for syntexa tests."""

import os
import tempfile
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test environment before importing app. Env vars must match the
# SYNTEXA_ prefix used by syntexa.config.Settings so tests that rely on
# get_settings() see the overridden values.
os.environ["SYNTEXA_ENVIRONMENT"] = "test"
os.environ["SYNTEXA_DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SYNTEXA_SESSION_SECRET"] = "test-secret-key-not-for-production"


@pytest.fixture(scope="session")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    # Cleanup after tests - on Windows, the file might still be open
    # so we just try to delete it but don't fail if we can't
    try:
        if os.path.exists(path):
            os.unlink(path)
    except (OSError, PermissionError):
        pass  # File may still be open by another process


@pytest.fixture(scope="function")
def db_session(test_db_path: str) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    # Import models first to register them with Base.metadata
    from syntexa.models import (  # noqa: F401 - registers all models
        AgentRole,
        SwarmComposition,
        SwarmInstance,
        SystemSetting,
        User,
    )
    from syntexa.models.database import Base

    engine = create_engine(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db_path: str) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with initialized database."""
    # Import models first to register them with Base.metadata
    from syntexa.models import (  # noqa: F401 - registers all models
        AgentRole,
        SwarmComposition,
        SwarmInstance,
        SystemSetting,
        User,
    )
    from syntexa.config import get_settings
    from syntexa.models.database import Base, init_engine

    # Set the database URL before importing app so lifespan uses it
    db_url = f"sqlite:///{test_db_path}"
    os.environ["SYNTEXA_DATABASE_URL"] = db_url

    # Clear settings cache so it picks up the new env var
    get_settings.cache_clear()

    # Initialize engine and create tables BEFORE importing app
    init_engine(db_url)
    from syntexa.models.database import get_engine

    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    # Import app AFTER engine is initialized and tables created
    from syntexa.api.main import app

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_clickup_response():
    """Sample ClickUp API response for testing."""
    return {
        "tasks": [
            {
                "id": "12345",
                "name": "Test Feature Task",
                "text_content": "Implement a new feature",
                "status": {"status": "in progress"},
                "tags": [{"name": "ag2-agent"}],
            }
        ]
    }


@pytest.fixture
def mock_github_response():
    """Sample GitHub API response for testing."""
    return {
        "number": 42,
        "html_url": "https://github.com/owner/repo/pull/42",
        "title": "Test PR",
        "state": "open",
    }
