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
    # Cleanup after tests
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture(scope="function")
def db_session(test_db_path: str) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    from syntexa.models.database import Base

    engine = create_engine(f"sqlite:///{test_db_path}")
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """Create a FastAPI test client."""
    from syntexa.api.main import app

    with TestClient(app) as test_client:
        yield test_client


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
