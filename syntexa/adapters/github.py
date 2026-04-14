"""GitHub implementation of RepositoryAdapter.

Local git operations use `subprocess` against a checked-out working copy
at `repo_path`. Pull-request creation uses the REST API v3.

This split matches the deployment model: the daemon runs on a VPS where
the swarm edits files in a local clone, then pushes and opens a PR.
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import httpx

from syntexa.adapters.base import PullRequestRef, RepositoryAdapter
from syntexa.adapters.clickup import AdapterError

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubAdapter(RepositoryAdapter):
    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        repo_path: Path,
        *,
        client: httpx.Client | None = None,
        git_bin: str = "git",
        timeout: float = 30.0,
    ) -> None:
        if not token:
            raise ValueError("GitHubAdapter requires a token.")
        if not owner or not repo:
            raise ValueError("GitHubAdapter requires owner and repo.")
        self._owner = owner
        self._repo = repo
        self._repo_path = Path(repo_path)
        self._git = git_bin
        self._client = client or httpx.Client(
            base_url=GITHUB_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=timeout,
        )

    # -- git wrappers -----------------------------------------------------

    def _run_git(self, *args: str) -> str:
        """Run a git command in the local repo_path, return stdout."""
        try:
            result = subprocess.run(
                [self._git, *args],
                cwd=str(self._repo_path),
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as exc:
            # stderr carries the actionable failure reason from git.
            raise AdapterError(
                f"git {' '.join(args)} failed: {exc.stderr.strip() or exc}"
            ) from exc

    def _branch_exists(self, name: str) -> bool:
        try:
            self._run_git("rev-parse", "--verify", f"refs/heads/{name}")
            return True
        except AdapterError:
            return False

    def create_branch(self, name: str, base: str) -> None:
        # Fetch latest base, then create branch if it doesn't exist locally.
        self._run_git("fetch", "origin", base)
        if self._branch_exists(name):
            logger.debug("Branch %s already exists; checking out", name)
            self._run_git("checkout", name)
            return
        self._run_git("checkout", "-B", name, f"origin/{base}")

    def commit(self, branch: str, message: str, paths: list[str]) -> str:
        self._run_git("checkout", branch)
        if paths:
            self._run_git("add", *paths)
        else:
            self._run_git("add", "-A")
        # `git commit` exits non-zero if there's nothing staged.
        self._run_git("commit", "-m", message)
        return self._run_git("rev-parse", "HEAD")

    def push(self, branch: str) -> None:
        self._run_git("push", "-u", "origin", branch)

    # -- REST API ---------------------------------------------------------

    def create_pr(
        self,
        head: str,
        base: str,
        title: str,
        body: str,
    ) -> PullRequestRef:
        try:
            resp = self._client.post(
                f"/repos/{self._owner}/{self._repo}/pulls",
                json={"title": title, "head": head, "base": base, "body": body},
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise AdapterError(f"GitHub create_pr failed: {exc}") from exc

        data = resp.json()
        return PullRequestRef(
            number=data["number"],
            url=data["html_url"],
            branch=head,
            title=data.get("title", title),
        )

    def health_check(self) -> bool:
        try:
            resp = self._client.get(f"/repos/{self._owner}/{self._repo}")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False
