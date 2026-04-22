"""Authentication utilities for session-based auth.

Provides bcrypt password hashing and secure session token generation.
Uses SQLite for session storage (survives server reloads).
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import bcrypt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy import Column, DateTime, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite session storage (persistent across reloads)
DB_PATH = "sessions.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SessionModel(Base):
    """Session table for persistent storage."""

    __tablename__ = "sessions"

    token = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)


# Create tables
Base.metadata.create_all(bind=engine)


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
    """Create a new session and return the session token."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expires_in_hours)

    db = SessionLocal()
    try:
        # Clean expired sessions for this user
        db.query(SessionModel).filter(
            SessionModel.user_id == user_id, SessionModel.expires_at < now
        ).delete(synchronize_session=False)

        # Create new session
        session = SessionModel(
            token=token,
            user_id=user_id,
            username=username,
            created_at=now,
            expires_at=expires_at,
        )
        db.add(session)
        db.commit()
        return token
    finally:
        db.close()


def get_session(token: str | None) -> SessionData | None:
    """Get session data if token is valid and not expired."""
    if token is None:
        return None

    db = SessionLocal()
    try:
        session = (
            db.query(SessionModel).filter(SessionModel.token == token).first()
        )
        if session is None:
            return None

        now = datetime.now(timezone.utc)
        if now > session.expires_at:
            # Clean up expired session
            db.delete(session)
            db.commit()
            return None

        return SessionData(
            user_id=session.user_id,
            username=session.username,
            created_at=session.created_at,
            expires_at=session.expires_at,
        )
    finally:
        db.close()


def delete_session(token: str) -> bool:
    """Delete a session (logout)."""
    db = SessionLocal()
    try:
        session = db.query(SessionModel).filter(SessionModel.token == token).first()
        if session:
            db.delete(session)
            db.commit()
            return True
        return False
    finally:
        db.close()


def cleanup_expired_sessions() -> int:
    """Remove all expired sessions from the store."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        result = (
            db.query(SessionModel)
            .filter(SessionModel.expires_at < now)
            .delete(synchronize_session=False)
        )
        db.commit()
        return result
    finally:
        db.close()


def get_session_count() -> int:
    """Get the number of active sessions."""
    cleanup_expired_sessions()
    db = SessionLocal()
    try:
        return db.query(SessionModel).count()
    finally:
        db.close()


def get_current_user(request: Request) -> SessionData:
    """Dependency to get the current authenticated user."""
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
