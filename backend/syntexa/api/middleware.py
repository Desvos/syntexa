"""Authentication middleware for protected endpoints.

Provides dependencies to enforce authentication on specific routes.
"""
from __future__ import annotations

from collections.abc import Callable

from fastapi import Header, HTTPException, Request, status
from fastapi.security import HTTPBearer

from syntexa.api.auth import get_session

security = HTTPBearer(auto_error=True)


def require_auth(
    # Use Header to inject the authorization header
    authorization: str | None = Header(None, alias="Authorization"),
) -> dict:
    """Dependency for requiring authentication on routes.

    Usage:
        @router.get("/protected", dependencies=[Depends(require_auth)])
        def protected_route(): ...

    Args:
        authorization: The Authorization header value

    Returns:
        Session data dict if authentication succeeds

    Raises:
        HTTPException: 401 if authentication fails
    """
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]
    session = get_session(token)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return session


def get_current_user(request: Request) -> dict:
    """Get the current authenticated user from request state.

    Use this in route handlers that already have RequireAuth dependency.

    Args:
        request: The FastAPI request object

    Returns:
        Session data dict with user_id, username, etc.

    Raises:
        HTTPException: 401 if no user in request state
    """
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def optional_auth(request: Request) -> dict | None:
    """Optional authentication - returns user if authenticated, None otherwise.

    Use this for routes that can work with or without authentication.

    Args:
        request: The FastAPI request object

    Returns:
        Session data dict or None
    """
    auth_header = request.headers.get("authorization", "")

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:]
    session = get_session(token)
    return session
