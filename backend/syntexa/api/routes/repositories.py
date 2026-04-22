"""CRUD endpoints for repositories.

A repository is a (name, path, remote_url, default_branch, clickup_list_id)
bundle the daemon will bind worktrees to. Rows can exist before the path is
materialized — disk reality is surfaced by the /health endpoint, not by
validation on create.
"""
from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from syntexa.api.dependencies import get_db
from syntexa.api.schemas import (
    RepositoryCreate,
    RepositoryHealth,
    RepositoryList,
    RepositoryRead,
    RepositoryUpdate,
)
from syntexa.models import Repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["repositories"])


def _to_read(repo: Repository) -> RepositoryRead:
    return RepositoryRead(
        id=repo.id,
        name=repo.name,
        path=repo.path,
        remote_url=repo.remote_url,
        default_branch=repo.default_branch,
        clickup_list_id=repo.clickup_list_id,
        clickup_trigger_tag=repo.clickup_trigger_tag,
        is_active=repo.is_active,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )


def _git_rev_parse(path: str, branch: str) -> bool:
    """Return True iff `git -C <path> rev-parse --verify <branch>` succeeds.

    Swallows any error (including timeout, missing binary, non-zero exit)
    and returns False. This is a read-only disk probe with a 5s timeout.
    """
    try:
        result = subprocess.run(
            ["git", "-C", path, "rev-parse", "--verify", branch],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


@router.get("", response_model=RepositoryList)
def list_repositories(db: Session = Depends(get_db)) -> RepositoryList:
    rows = db.query(Repository).order_by(Repository.name).all()
    return RepositoryList(repositories=[_to_read(r) for r in rows])


@router.post(
    "",
    response_model=RepositoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_repository(
    payload: RepositoryCreate,
    db: Session = Depends(get_db),
) -> RepositoryRead:
    # Only schema-layer validation we enforce in the route: the path must
    # be absolute. We do NOT validate on-disk presence — users may pre-
    # configure a repo before cloning; /health surfaces reality.
    if not os.path.isabs(payload.path):
        raise HTTPException(
            status_code=422,
            detail=f"path must be absolute: '{payload.path}'",
        )

    repo = Repository(
        name=payload.name,
        path=payload.path,
        remote_url=payload.remote_url,
        default_branch=payload.default_branch,
        clickup_list_id=payload.clickup_list_id,
        clickup_trigger_tag=payload.clickup_trigger_tag,
        is_active=payload.is_active,
    )
    db.add(repo)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        # SQLite raises a single IntegrityError for either unique violation;
        # disambiguate by checking which existing row collides.
        msg = str(exc.orig).lower() if exc.orig else str(exc).lower()
        if "path" in msg:
            detail = f"Repository with path '{payload.path}' already exists."
        elif "name" in msg:
            detail = f"Repository '{payload.name}' already exists."
        else:
            # Fall back to an explicit lookup if the DB error text is vague.
            if db.query(Repository).filter(Repository.name == payload.name).first():
                detail = f"Repository '{payload.name}' already exists."
            else:
                detail = f"Repository with path '{payload.path}' already exists."
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=detail
        ) from None
    return _to_read(repo)


@router.put("/{repo_id}", response_model=RepositoryRead)
def update_repository(
    repo_id: int,
    payload: RepositoryUpdate,
    db: Session = Depends(get_db),
) -> RepositoryRead:
    repo = db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )

    if payload.path is not None:
        if not os.path.isabs(payload.path):
            raise HTTPException(
                status_code=422,
                detail=f"path must be absolute: '{payload.path}'",
            )
        repo.path = payload.path
    if payload.remote_url is not None:
        repo.remote_url = payload.remote_url
    if payload.default_branch is not None:
        repo.default_branch = payload.default_branch
    if payload.clickup_list_id is not None:
        repo.clickup_list_id = payload.clickup_list_id
    if payload.clickup_trigger_tag is not None:
        repo.clickup_trigger_tag = payload.clickup_trigger_tag
    if payload.is_active is not None:
        repo.is_active = payload.is_active
    repo.updated_at = datetime.now(timezone.utc)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository with path '{payload.path}' already exists.",
        ) from None
    return _to_read(repo)


@router.delete(
    "/{repo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_repository(repo_id: int, db: Session = Depends(get_db)) -> Response:
    repo = db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )
    db.delete(repo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{repo_id}/health", response_model=RepositoryHealth)
def repository_health(
    repo_id: int, db: Session = Depends(get_db)
) -> RepositoryHealth:
    repo = db.get(Repository, repo_id)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found"
        )

    p = Path(repo.path)
    path_exists = p.exists()
    is_git_repo = path_exists and (p / ".git").is_dir()
    default_branch_exists = (
        is_git_repo and _git_rev_parse(repo.path, repo.default_branch)
    )
    return RepositoryHealth(
        is_git_repo=is_git_repo,
        path_exists=path_exists,
        default_branch_exists=default_branch_exists,
    )
