"""User management routes for CRUD operations."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from syntexa.api.auth import hash_password
from syntexa.api.schemas import (
    UserCreate,
    UserDeleteResponse,
    UserList,
    UserRead,
)
from syntexa.models.database import get_db_session
from syntexa.models.entities import User

router = APIRouter(prefix="/users", tags=["users"])


def _get_current_user_id(request: Request) -> int:
    """Get current user ID from session (for self-delete protection)."""
    from syntexa.api.auth import get_session

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    token = auth_header[7:]
    session = get_session(token)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return session["user_id"]


@router.get("", response_model=UserList)
def list_users(
    db: Session = Depends(get_db_session),
) -> UserList:
    """List all users (excludes password hashes)."""
    users = db.query(User).order_by(User.username).all()
    return UserList(users=users)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db_session),
) -> UserRead:
    """Create a new user.

    Username must be unique. Password is hashed with bcrypt.
    """
    # Check for existing username
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user_in.username}' already exists",
        )

    # Create user with hashed password
    user = User(
        username=user_in.username,
        password_hash=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserRead.model_validate(user)


@router.delete("/{user_id}", response_model=UserDeleteResponse)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db_session),
) -> UserDeleteResponse:
    """Delete a user by ID.

    Users cannot delete themselves (self-delete protection).
    Requires authentication.
    """
    current_user_id = _get_current_user_id(request)

    # Self-delete protection
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own account",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    deleted_id = user.id
    db.delete(user)
    db.commit()

    return UserDeleteResponse(
        message="User deleted successfully",
        deleted_user_id=deleted_id,
    )