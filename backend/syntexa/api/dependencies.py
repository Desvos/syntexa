"""FastAPI dependency providers."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from syntexa.models.database import get_session_factory


def get_db() -> Iterator[Session]:
    """Per-request SQLAlchemy session. Commits on success, rolls back on
    exception, always closes. Routes that mutate should call session.commit()
    themselves only if they need the id of an inserted row mid-request."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
