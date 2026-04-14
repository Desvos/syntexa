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


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Create a test user and return auth headers with a valid session token."""
    import sys
    sys.stderr.write("DEBUG: auth_headers fixture starting\n")
    from syntexa.models.database import session_scope, create_all
    from syntexa.models.entities import User
    from syntexa.api.auth import hash_password, create_session

    try:
        sys.stderr.write("DEBUG: creating tables\n")
        # Ensure tables exist
        create_all()
        sys.stderr.write("DEBUG: tables created\n")

        with session_scope() as db:
            sys.stderr.write("DEBUG: creating user\n")
            # Create test user
            user = User(
                username="testuser",
                password_hash=hash_password("testpassword123"),
            )
            db.add(user)
            db.flush()  # Get the user ID
            user_id = user.id
            sys.stderr.write(f"DEBUG: user created with ID {user_id}\n")

        # Create session token directly (bypass login API)
        token = create_session(user_id, "testuser")
        sys.stderr.write(f"DEBUG: token created {token[:20]}...\n")

        # Verify token is in store
        from syntexa.api.auth import get_session
        session = get_session(token)
        sys.stderr.write(f"DEBUG: session lookup: {session}\n")

        return {"authorization": f"Bearer {token}"}
    except Exception as e:
        import sys
        sys.stderr.write(f"auth_headers error: {e}\n")
        import traceback
        traceback.print_exc()

    sys.stderr.write("DEBUG: returning empty dict\n")
    return {}
