"""Tests for the built-in presets catalog + apply mechanism."""
from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from syntexa.core import crypto
from syntexa.models import Agent, LLMProvider, Repository, Swarm, SwarmAgent
from syntexa.presets import (
    BUILTIN_AGENT_PRESETS,
    BUILTIN_PROVIDER_PRESETS,
    BUILTIN_SWARM_TEMPLATES,
    UnknownPresetError,
    apply_preset,
)


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


# --- catalog shape -------------------------------------------------------


def test_builtin_agent_presets_are_non_empty_and_shaped() -> None:
    assert len(BUILTIN_AGENT_PRESETS) >= 6
    expected_keys = {"name", "system_prompt", "default_model", "description"}
    names = {p["name"] for p in BUILTIN_AGENT_PRESETS}
    # Known agents we rely on for swarm templates
    assert {"planner", "coder", "reviewer", "tester"} <= names
    for p in BUILTIN_AGENT_PRESETS:
        assert expected_keys <= set(p.keys())
        assert isinstance(p["system_prompt"], str) and p["system_prompt"]


def test_builtin_provider_presets_are_non_empty_and_shaped() -> None:
    assert len(BUILTIN_PROVIDER_PRESETS) >= 4
    expected_keys = {"name", "provider_type", "default_model", "base_url", "description"}
    for p in BUILTIN_PROVIDER_PRESETS:
        assert expected_keys <= set(p.keys())


def test_builtin_swarm_templates_are_non_empty_and_shaped() -> None:
    assert len(BUILTIN_SWARM_TEMPLATES) >= 4
    expected_keys = {"name", "description", "agent_names", "orchestrator_strategy"}
    names = {t["name"] for t in BUILTIN_SWARM_TEMPLATES}
    assert {"quick-fix", "feature-dev", "review-only", "auto"} <= names
    for t in BUILTIN_SWARM_TEMPLATES:
        assert expected_keys <= set(t.keys())
        assert t["orchestrator_strategy"] in ("auto", "parallel", "sequential")
        assert isinstance(t["agent_names"], list) and t["agent_names"]


# --- apply_preset direct -------------------------------------------------


def _seed_provider(db: Session, name: str = "prov-test") -> LLMProvider:
    provider = LLMProvider(
        name=name,
        provider_type="ollama",
        base_url="http://localhost:11434/v1",
        api_key_encrypted=None,
        default_model="llama3.1",
        is_active=True,
    )
    db.add(provider)
    db.flush()
    return provider


def _seed_repository(db: Session, tmp_path: Path) -> Repository:
    repo = Repository(
        name="repo-test",
        path=tmp_path.resolve().as_posix(),
        remote_url=None,
        default_branch="main",
        is_active=True,
    )
    db.add(repo)
    db.flush()
    return repo


def test_apply_preset_agent_creates_agent(db_session: Session) -> None:
    provider = _seed_provider(db_session)
    agent = apply_preset(
        "agent", "coder", db_session, provider_id=provider.id
    )
    assert isinstance(agent, Agent)
    assert agent.name == "coder"
    assert agent.provider_id == provider.id
    assert "production code" in agent.system_prompt


def test_apply_preset_agent_is_idempotent(db_session: Session) -> None:
    provider = _seed_provider(db_session)
    first = apply_preset(
        "agent", "reviewer", db_session, provider_id=provider.id
    )
    again = apply_preset(
        "agent", "reviewer", db_session, provider_id=provider.id
    )
    assert first.id == again.id


def test_apply_preset_unknown_raises(db_session: Session) -> None:
    provider = _seed_provider(db_session)
    with pytest.raises(UnknownPresetError):
        apply_preset(
            "agent", "nonexistent", db_session, provider_id=provider.id
        )


def test_apply_preset_swarm_template_seeds_missing_agents(
    db_session: Session, tmp_path: Path
) -> None:
    provider = _seed_provider(db_session)
    repo = _seed_repository(db_session, tmp_path)

    # No agents yet in DB
    assert db_session.query(Agent).count() == 0

    swarm = apply_preset(
        "swarm_template",
        "feature-dev",
        db_session,
        repository_id=repo.id,
        provider_id=provider.id,
    )
    assert isinstance(swarm, Swarm)
    assert swarm.name == "feature-dev"
    assert swarm.orchestrator_strategy == "sequential"
    assert swarm.repository_id == repo.id

    # All four agents were auto-seeded.
    agent_names = {a.name for a in db_session.query(Agent).all()}
    assert {"planner", "coder", "reviewer", "tester"} <= agent_names

    # Join rows ordered by position
    joins = (
        db_session.query(SwarmAgent)
        .filter(SwarmAgent.swarm_id == swarm.id)
        .order_by(SwarmAgent.position)
        .all()
    )
    assert len(joins) == 4
    assert [j.position for j in joins] == [0, 1, 2, 3]


def test_apply_preset_swarm_template_requires_overrides(
    db_session: Session,
) -> None:
    from syntexa.presets.apply import InvalidOverrideError

    with pytest.raises(InvalidOverrideError):
        apply_preset("swarm_template", "quick-fix", db_session)


# --- API endpoints -------------------------------------------------------


def test_get_agent_presets_returns_catalog(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.get("/api/v1/presets/agents", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 6
    assert {e["name"] for e in data} >= {"planner", "coder", "reviewer", "tester"}
    for entry in data:
        assert "system_prompt" in entry
        assert "description" in entry


def test_get_provider_presets_returns_catalog(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.get("/api/v1/presets/providers", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    types = {e["provider_type"] for e in data}
    assert {"anthropic", "openai", "openrouter", "ollama"} <= types


def test_get_swarm_templates_returns_catalog(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.get("/api/v1/presets/swarm-templates", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 4
    assert {t["name"] for t in data} >= {
        "quick-fix",
        "feature-dev",
        "review-only",
        "auto",
    }


def _make_provider_via_api(client: TestClient, auth_headers: dict) -> int:
    resp = client.post(
        "/api/v1/llm-providers",
        json={
            "name": "ollama-presets",
            "provider_type": "ollama",
            "default_model": "llama3.1",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_apply_agent_preset_happy_path(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider_via_api(client, auth_headers)
    resp = client.post(
        "/api/v1/presets/apply",
        json={
            "kind": "agent",
            "preset_name": "planner",
            "overrides": {"provider_id": provider_id},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["kind"] == "agent"
    assert data["agent"]["name"] == "planner"
    assert data["agent"]["provider_id"] == provider_id

    # Agent is visible in the normal listing
    listing = client.get("/api/v1/agents", headers=auth_headers).json()
    assert any(a["name"] == "planner" for a in listing["agents"])


def test_apply_unknown_preset_returns_404(
    client: TestClient, auth_headers: dict
) -> None:
    provider_id = _make_provider_via_api(client, auth_headers)
    resp = client.post(
        "/api/v1/presets/apply",
        json={
            "kind": "agent",
            "preset_name": "does-not-exist",
            "overrides": {"provider_id": provider_id},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404, resp.text


def test_apply_agent_preset_missing_override_returns_422(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/v1/presets/apply",
        json={
            "kind": "agent",
            "preset_name": "planner",
            "overrides": {},
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422, resp.text


def test_apply_invalid_kind_returns_422(
    client: TestClient, auth_headers: dict
) -> None:
    resp = client.post(
        "/api/v1/presets/apply",
        json={
            "kind": "banana",
            "preset_name": "planner",
            "overrides": {},
        },
        headers=auth_headers,
    )
    # kind validator on the schema trips before hitting the builder.
    assert resp.status_code == 422, resp.text
