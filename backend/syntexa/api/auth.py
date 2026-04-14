"""Authentication utilities for session-based auth.

Provides bcrypt password hashing and secure session token generation.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import bcrypt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

# Simple in-memory session store. For production, this should be Redis or DB.
# Format: {session_token: SessionData}
_session_store: dict[str, "SessionData"] = {}


class SessionData(TypedDict):
    user_id: int
    username: str
    created_at: datetime
    expires_at: datetime


security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    password_bytes = password.encode("utf-8")
    hash_bytes = password_hash.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hash_bytes)


def create_session(user_id: int, username: str, expires_in_hours: int = 24) -> str:
    """Create a new session and return the session token.

    Args:
        user_id: The user's ID
        username: The user's username
        expires_in_hours: Session expiration time (default 24 hours)

    Returns:
        Session token string
    """
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expires_in_hours)

    _session_store[token] = SessionData(
        user_id=user_id,
        username=username,
        created_at=now,
        expires_at=expires_at,
    )
    return token


def get_session(token: str | None) -> SessionData | None:
    """Get session data if token is valid and not expired.

    Args:
        token: The session token

    Returns:
        SessionData if valid, None otherwise
    """
    if token is None:
        return None

    session = _session_store.get(token)
    if session is None:
        return None

    now = datetime.now(timezone.utc)
    if now > session["expires_at"]:
        # Clean up expired session
        del _session_store[token]
        return None

    return session


def delete_session(token: str) -> bool:
    """Delete a session (logout).

    Args:
        token: The session token to delete

    Returns:
        True if session was found and deleted, False otherwise
    """
    if token in _session_store:
        del _session_store[token]
        return True
    return False


def get_current_user(request: Request) -> SessionData:
    """Dependency to get the current authenticated user.

    Raises:
        HTTPException: 401 if not authenticated or session expired
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[7:]  # Remove "Bearer " prefix
    session = get_session(token)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session


def cleanup_expired_sessions() -> int:
    """Remove all expired sessions from the store.

    Returns:
        Number of sessions removed
    """
    now = datetime.now(timezone.utc)
    expired = [
        token for token, data in _session_store.items() if now > data["expires_at"]
    ]
    for token in expired:
        del _session_store[token]
    return len(expired)


def get_session_count() -> int:
    """Get the number of active sessions.

    Returns:
        Number of active (non-expired) sessions
    """
    cleanup_expired_sessions()
    return len(_session_store)
