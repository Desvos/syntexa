"""CRUD tests for /api/v1/repositories."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# --- helpers -------------------------------------------------------------


def _abs_path(p: Path) -> str:
    """Return absolute path string using POSIX-style slashes to keep
    assertions identical on Windows and Unix."""
    return p.resolve().as_posix()


# --- create --------------------------------------------------------------


def test_create_succeeds_with_name_lowercased(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    resp = client.post(
        "/api/v1/repositories",
        json={
            "name": "MyRepo",
            "path": _abs_path(tmp_path),
            "remote_url": "https://github.com/owner/repo.git",
            "default_branch": "develop",
            "clickup_list_id": "901234",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "myrepo"
    assert data["path"] == _abs_path(tmp_path)
    assert data["remote_url"] == "https://github.com/owner/repo.git"
    assert data["default_branch"] == "develop"
    assert data["clickup_list_id"] == "901234"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_rejects_non_slug_name(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    resp = client.post(
        "/api/v1/repositories",
        json={
            "name": "bad name!",
            "path": _abs_path(tmp_path),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_rejects_relative_path(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/v1/repositories",
        json={
            "name": "rel",
            "path": "relative/path",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "absolute" in resp.text.lower()


def test_create_rejects_duplicate_name(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    p1 = tmp_path / "a"
    p2 = tmp_path / "b"
    p1.mkdir()
    p2.mkdir()

    assert client.post(
        "/api/v1/repositories",
        json={"name": "dup", "path": _abs_path(p1)},
        headers=auth_headers,
    ).status_code == 201

    resp = client.post(
        "/api/v1/repositories",
        json={"name": "dup", "path": _abs_path(p2)},
        headers=auth_headers,
    )
    assert resp.status_code == 409


def test_create_rejects_duplicate_path(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    assert client.post(
        "/api/v1/repositories",
        json={"name": "first", "path": _abs_path(tmp_path)},
        headers=auth_headers,
    ).status_code == 201

    resp = client.post(
        "/api/v1/repositories",
        json={"name": "second", "path": _abs_path(tmp_path)},
        headers=auth_headers,
    )
    assert resp.status_code == 409


def test_create_accepts_nonexistent_path(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    # User pre-configures a repo before it's cloned to disk — the row
    # must be accepted; /health surfaces reality.
    ghost = tmp_path / "does-not-exist-yet"
    resp = client.post(
        "/api/v1/repositories",
        json={"name": "ghost", "path": _abs_path(ghost)},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["is_active"] is True  # not auto-deactivated


def test_create_defaults_branch_to_main(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    resp = client.post(
        "/api/v1/repositories",
        json={"name": "defaults", "path": _abs_path(tmp_path)},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["default_branch"] == "main"


# --- update --------------------------------------------------------------


def test_update_patches_fields(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    created = client.post(
        "/api/v1/repositories",
        json={"name": "patchme", "path": _abs_path(tmp_path)},
        headers=auth_headers,
    ).json()

    resp = client.put(
        f"/api/v1/repositories/{created['id']}",
        json={
            "remote_url": "https://github.com/new/origin.git",
            "default_branch": "trunk",
            "is_active": False,
            "clickup_list_id": "555",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["remote_url"] == "https://github.com/new/origin.git"
    assert data["default_branch"] == "trunk"
    assert data["is_active"] is False
    assert data["clickup_list_id"] == "555"
    # name unchanged
    assert data["name"] == "patchme"


def test_update_404_on_missing_id(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.put(
        "/api/v1/repositories/99999",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# --- delete --------------------------------------------------------------


def test_delete_returns_204_and_removes_row(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    created = client.post(
        "/api/v1/repositories",
        json={"name": "bye", "path": _abs_path(tmp_path)},
        headers=auth_headers,
    ).json()

    resp = client.delete(
        f"/api/v1/repositories/{created['id']}", headers=auth_headers
    )
    assert resp.status_code == 204

    listing = client.get(
        "/api/v1/repositories", headers=auth_headers
    ).json()
    assert all(r["id"] != created["id"] for r in listing["repositories"])


# --- list ----------------------------------------------------------------


def test_list_is_ordered_by_name(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    for name in ("z-repo", "a-repo", "m-repo"):
        sub = tmp_path / name
        sub.mkdir()
        client.post(
            "/api/v1/repositories",
            json={"name": name, "path": _abs_path(sub)},
            headers=auth_headers,
        )
    resp = client.get("/api/v1/repositories", headers=auth_headers)
    assert resp.status_code == 200
    names = [r["name"] for r in resp.json()["repositories"]]
    assert names == sorted(names)


# --- health --------------------------------------------------------------


def test_health_for_nonexistent_path(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    ghost = tmp_path / "nope"
    created = client.post(
        "/api/v1/repositories",
        json={"name": "ghost-health", "path": _abs_path(ghost)},
        headers=auth_headers,
    ).json()

    resp = client.get(
        f"/api/v1/repositories/{created['id']}/health", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data == {
        "path_exists": False,
        "is_git_repo": False,
        "default_branch_exists": False,
    }


def test_health_for_existing_nongit_path(
    client: TestClient, auth_headers: dict, tmp_path: Path
) -> None:
    # tmp_path exists but is not a git repo.
    created = client.post(
        "/api/v1/repositories",
        json={"name": "nongit", "path": _abs_path(tmp_path)},
        headers=auth_headers,
    ).json()

    resp = client.get(
        f"/api/v1/repositories/{created['id']}/health", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path_exists"] is True
    assert data["is_git_repo"] is False
    assert data["default_branch_exists"] is False


def test_health_for_git_repo_with_branch(
    client: TestClient,
    auth_headers: dict,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full-pass case. We monkeypatch the git-subprocess helper to avoid
    depending on a system `git` being on PATH in CI. We still exercise
    the real path/.git existence check by materializing a fake .git
    directory — that's a plain filesystem check."""
    repo_path = tmp_path / "myrepo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    from syntexa.api.routes import repositories as repo_routes

    monkeypatch.setattr(
        repo_routes, "_git_rev_parse", lambda _p, _b: True
    )

    created = client.post(
        "/api/v1/repositories",
        json={
            "name": "realgit",
            "path": _abs_path(repo_path),
            "default_branch": "main",
        },
        headers=auth_headers,
    ).json()

    resp = client.get(
        f"/api/v1/repositories/{created['id']}/health", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data == {
        "path_exists": True,
        "is_git_repo": True,
        "default_branch_exists": True,
    }


def test_health_404_on_missing_id(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.get(
        "/api/v1/repositories/99999/health", headers=auth_headers
    )
    assert resp.status_code == 404


# --- unit test on the git helper ----------------------------------------


def test_git_rev_parse_swallows_errors(tmp_path: Path) -> None:
    """The helper returns False on any failure path (non-git dir,
    missing dir, bad branch) and never raises."""
    from syntexa.api.routes.repositories import _git_rev_parse

    # Non-git directory - git will return non-zero.
    assert _git_rev_parse(str(tmp_path), "main") is False
    # Missing directory - git will error out, helper should swallow.
    missing = tmp_path / "does-not-exist"
    assert _git_rev_parse(str(missing), "main") is False


def test_git_rev_parse_handles_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Subprocess timeout returns False, not a propagated exception."""
    from syntexa.api.routes import repositories as repo_routes

    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=5)

    monkeypatch.setattr(repo_routes.subprocess, "run", _raise_timeout)
    assert repo_routes._git_rev_parse(str(tmp_path), "main") is False
