"""Seed preset rows into the DB.

The top-level entry point is ``apply_preset(kind, preset_name, session,
**overrides)``. It dispatches to one of three builders:

- ``agent``    — needs ``provider_id`` (override or kwarg).
- ``provider`` — optional ``api_key`` override (required for non-Ollama).
- ``swarm_template`` — needs ``repository_id`` and ``provider_id``; creates
  any missing agents from the agent-preset library first.

The function is idempotent-ish: if a row with the target name already
exists we return it untouched rather than raising. For the swarm-template
path we only reuse existing agents — never mutate their prompts.
"""
from __future__ import annotations

from typing import Any, Literal

from sqlalchemy.orm import Session

from syntexa.core.crypto import encrypt
from syntexa.models import Agent, LLMProvider, Repository, Swarm, SwarmAgent
from syntexa.presets.agents import BUILTIN_AGENT_PRESETS
from syntexa.presets.providers import BUILTIN_PROVIDER_PRESETS
from syntexa.presets.swarm_templates import BUILTIN_SWARM_TEMPLATES

PresetKind = Literal["agent", "provider", "swarm_template"]


class PresetError(Exception):
    """Base class for preset-application errors."""


class UnknownPresetError(PresetError):
    """Raised when ``preset_name`` isn't in the built-in catalog."""


class InvalidOverrideError(PresetError):
    """Raised when required overrides are missing or malformed."""


# --- lookup helpers ------------------------------------------------------


def _find_preset(catalog: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for entry in catalog:
        if entry["name"] == name:
            return entry
    raise UnknownPresetError(f"No preset named '{name}'")


# --- builders ------------------------------------------------------------


def _apply_agent(
    preset: dict[str, Any],
    session: Session,
    overrides: dict[str, Any],
) -> Agent:
    provider_id = overrides.get("provider_id")
    if provider_id is None:
        raise InvalidOverrideError(
            "agent presets require 'provider_id' in overrides"
        )
    if session.get(LLMProvider, provider_id) is None:
        raise InvalidOverrideError(
            f"No LLMProvider with id={provider_id}"
        )

    name = overrides.get("name") or preset["name"]
    existing = session.query(Agent).filter(Agent.name == name).first()
    if existing is not None:
        return existing

    agent = Agent(
        name=name,
        system_prompt=overrides.get("system_prompt") or preset["system_prompt"],
        provider_id=provider_id,
        model=overrides.get("model", preset.get("default_model")),
        is_active=overrides.get("is_active", True),
    )
    session.add(agent)
    session.flush()
    return agent


def _apply_provider(
    preset: dict[str, Any],
    session: Session,
    overrides: dict[str, Any],
) -> LLMProvider:
    name = overrides.get("name") or preset["name"]
    existing = (
        session.query(LLMProvider).filter(LLMProvider.name == name).first()
    )
    if existing is not None:
        return existing

    api_key = overrides.get("api_key")
    provider_type = preset["provider_type"]
    if provider_type != "ollama" and not api_key:
        raise InvalidOverrideError(
            f"provider preset '{preset['name']}' requires 'api_key' in "
            "overrides (non-ollama providers must carry a key)"
        )

    provider = LLMProvider(
        name=name,
        provider_type=provider_type,
        base_url=overrides.get("base_url", preset.get("base_url")),
        api_key_encrypted=encrypt(api_key) if api_key else None,
        default_model=overrides.get("default_model") or preset["default_model"],
        is_active=overrides.get("is_active", True),
    )
    session.add(provider)
    session.flush()
    return provider


def _ensure_agent_from_library(
    agent_name: str,
    provider_id: int,
    session: Session,
) -> Agent:
    """Look up (or seed) an agent by name using the built-in preset library."""
    existing = session.query(Agent).filter(Agent.name == agent_name).first()
    if existing is not None:
        return existing
    try:
        agent_preset = _find_preset(BUILTIN_AGENT_PRESETS, agent_name)
    except UnknownPresetError as exc:
        raise InvalidOverrideError(
            f"Agent '{agent_name}' does not exist and is not in the "
            "built-in agent preset library; cannot auto-seed."
        ) from exc
    return _apply_agent(agent_preset, session, {"provider_id": provider_id})


def _apply_swarm_template(
    preset: dict[str, Any],
    session: Session,
    overrides: dict[str, Any],
) -> Swarm:
    repository_id = overrides.get("repository_id")
    provider_id = overrides.get("provider_id")
    if repository_id is None or provider_id is None:
        raise InvalidOverrideError(
            "swarm_template presets require 'repository_id' and "
            "'provider_id' in overrides"
        )
    if session.get(Repository, repository_id) is None:
        raise InvalidOverrideError(
            f"No Repository with id={repository_id}"
        )
    if session.get(LLMProvider, provider_id) is None:
        raise InvalidOverrideError(
            f"No LLMProvider with id={provider_id}"
        )

    name = overrides.get("name") or preset["name"]
    existing = session.query(Swarm).filter(Swarm.name == name).first()
    if existing is not None:
        return existing

    # Seed missing agents first, in declared order.
    agents: list[Agent] = []
    for agent_name in preset["agent_names"]:
        agents.append(
            _ensure_agent_from_library(agent_name, provider_id, session)
        )

    strategy = (
        overrides.get("orchestrator_strategy")
        or preset["orchestrator_strategy"]
    )

    swarm = Swarm(
        name=name,
        repository_id=repository_id,
        task_description=overrides.get(
            "task_description", preset.get("description")
        ),
        orchestrator_strategy=strategy,
        max_rounds=overrides.get("max_rounds", 60),
        status="idle",
        is_active=True,
    )
    session.add(swarm)
    session.flush()

    for position, agent in enumerate(agents):
        session.add(
            SwarmAgent(
                swarm_id=swarm.id,
                agent_id=agent.id,
                position=position,
            )
        )
    session.flush()
    return swarm


# --- public entry point --------------------------------------------------


_BUILDERS = {
    "agent": (_apply_agent, BUILTIN_AGENT_PRESETS),
    "provider": (_apply_provider, BUILTIN_PROVIDER_PRESETS),
    "swarm_template": (_apply_swarm_template, BUILTIN_SWARM_TEMPLATES),
}


def apply_preset(
    kind: PresetKind,
    preset_name: str,
    session: Session,
    **overrides: Any,
) -> Agent | LLMProvider | Swarm:
    """Seed one preset row into the DB and return the created/existing entity.

    ``kind`` picks the catalog; ``preset_name`` picks the entry within it.
    ``overrides`` supplies runtime-required values (provider_id, api_key,
    repository_id) plus optional field overrides.

    Raises:
        UnknownPresetError: ``kind`` or ``preset_name`` not recognized.
        InvalidOverrideError: required override missing or malformed.
    """
    if kind not in _BUILDERS:
        raise UnknownPresetError(
            f"Unknown preset kind '{kind}'; expected one of "
            f"{sorted(_BUILDERS.keys())}"
        )
    builder, catalog = _BUILDERS[kind]
    preset = _find_preset(catalog, preset_name)
    return builder(preset, session, overrides)
