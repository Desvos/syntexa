"""Authentication routes for login/logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from syntexa.api.auth import create_session, verify_password
from syntexa.api.schemas import LoginRequest, LoginResponse, UserRead
from syntexa.models.database import get_db_session
from syntexa.models.entities import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db_session),
) -> LoginResponse:
    """Authenticate user and create a session.

    Returns a bearer token to use in the Authorization header
    for subsequent requests.
    """
    user = db.query(User).filter(User.username == request.username.lower()).first()

    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login timestamp
    from datetime import datetime, timezone

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    # Create session
    token = create_session(user.id, user.username)

    return LoginResponse(
        access_token=token,
        user=UserRead.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def logout(request: Request) -> None:
    """Logout the current user by invalidating their session token."""
    from syntexa.api.auth import delete_session

    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        delete_session(token)