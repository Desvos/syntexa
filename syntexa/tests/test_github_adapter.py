"""T031 — GitHub adapter unit tests.

git subprocess calls are monkeypatched; REST calls use httpx MockTransport.
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from syntexa.adapters.clickup import AdapterError
from syntexa.adapters.github import GITHUB_API_BASE, GitHubAdapter


class FakeGit:
    """Records git calls and answers with canned responses keyed by args prefix."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []
        self.responses: dict[tuple[str, ...], str] = {}
        self.failures: set[tuple[str, ...]] = set()

    def answer(self, *args: str) -> str:
        key = args
        self.calls.append(key)
        if key in self.failures:
            import subprocess

            raise subprocess.CalledProcessError(1, ["git", *args], stderr="simulated")
        # Find the longest matching prefix.
        for prefix, response in sorted(
            self.responses.items(), key=lambda kv: -len(kv[0])
        ):
            if key[: len(prefix)] == prefix:
                return response
        return ""


@pytest.fixture
def fake_git(monkeypatch) -> FakeGit:
    fake = FakeGit()

    def fake_run(cmd, cwd, check, capture_output, text):  # noqa: ARG001
        assert cmd[0] == "git"
        stdout = fake.answer(*cmd[1:])

        class R:
            def __init__(self, out: str) -> None:
                self.stdout = out

        return R(stdout)

    monkeypatch.setattr("syntexa.adapters.github.subprocess.run", fake_run)
    return fake


def _adapter(repo_path: Path, handler=None) -> GitHubAdapter:
    handler = handler or (lambda req: httpx.Response(200, json={}))
    client = httpx.Client(
        base_url=GITHUB_API_BASE,
        transport=httpx.MockTransport(handler),
        headers={"Authorization": "Bearer token"},
    )
    return GitHubAdapter(
        token="token",
        owner="o",
        repo="r",
        repo_path=repo_path,
        client=client,
    )


def test_create_branch_creates_when_missing(tmp_path: Path, fake_git: FakeGit) -> None:
    # rev-parse fails → branch doesn't exist → checkout -B runs.
    fake_git.failures.add(("rev-parse", "--verify", "refs/heads/feature/x"))
    adapter = _adapter(tmp_path)
    adapter.create_branch("feature/x", "main")

    assert ("fetch", "origin", "main") in fake_git.calls
    assert ("checkout", "-B", "feature/x", "origin/main") in fake_git.calls


def test_create_branch_is_idempotent(tmp_path: Path, fake_git: FakeGit) -> None:
    # rev-parse succeeds → branch exists → plain checkout.
    adapter = _adapter(tmp_path)
    adapter.create_branch("feature/x", "main")

    assert ("checkout", "feature/x") in fake_git.calls
    assert not any(c[0] == "checkout" and "-B" in c for c in fake_git.calls)


def test_commit_returns_sha(tmp_path: Path, fake_git: FakeGit) -> None:
    fake_git.responses[("rev-parse", "HEAD")] = "abc1234"
    adapter = _adapter(tmp_path)
    sha = adapter.commit("feat/x", "feat: add x", ["a.py", "b.py"])

    assert sha == "abc1234"
    assert ("add", "a.py", "b.py") in fake_git.calls
    assert ("commit", "-m", "feat: add x") in fake_git.calls


def test_commit_empty_paths_adds_all(tmp_path: Path, fake_git: FakeGit) -> None:
    adapter = _adapter(tmp_path)
    adapter.commit("feat/x", "msg", [])
    assert ("add", "-A") in fake_git.calls


def test_create_pr_posts_to_api(tmp_path: Path, fake_git: FakeGit) -> None:
    captured: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["path"] = req.url.path
        captured["body"] = json.loads(req.content)
        return httpx.Response(
            201,
            json={
                "number": 7,
                "html_url": "https://github.com/o/r/pull/7",
                "title": "t",
            },
        )

    adapter = _adapter(tmp_path, handler)
    pr = adapter.create_pr("feat/x", "main", "t", "b")

    assert pr.number == 7
    assert pr.url == "https://github.com/o/r/pull/7"
    assert captured["path"] == "/repos/o/r/pulls"
    assert captured["body"]["head"] == "feat/x"
    assert captured["body"]["base"] == "main"


def test_create_pr_raises_on_api_error(tmp_path: Path, fake_git: FakeGit) -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"message": "validation failed"})

    adapter = _adapter(tmp_path, handler)
    with pytest.raises(AdapterError):
        adapter.create_pr("feat/x", "main", "t", "b")


def test_push_runs_git(tmp_path: Path, fake_git: FakeGit) -> None:
    adapter = _adapter(tmp_path)
    adapter.push("feat/x")
    assert ("push", "-u", "origin", "feat/x") in fake_git.calls
