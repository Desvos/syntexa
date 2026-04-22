"""Built-in Agent presets.

Each entry is a dict with:
    - name: slug used as the Agent.name (must satisfy the slug validator).
    - system_prompt: the agent's role/persona prompt.
    - default_model: optional explicit model override; ``None`` means
      "inherit from the provider".
    - description: short human-readable blurb shown in UI pickers.

These are pure Python data — the DB seeding happens in ``apply.py``.
"""
from __future__ import annotations

from typing import Any

BUILTIN_AGENT_PRESETS: list[dict[str, Any]] = [
    {
        "name": "planner",
        "system_prompt": (
            "You break down high-level tasks into concrete sub-tasks with "
            "acceptance criteria."
        ),
        "default_model": None,
        "description": "Decomposes tasks into actionable sub-tasks.",
    },
    {
        "name": "coder",
        "system_prompt": (
            "You write production code matching the project's style. You "
            "edit files via patches."
        ),
        "default_model": None,
        "description": "Writes production code and patches.",
    },
    {
        "name": "reviewer",
        "system_prompt": (
            "You critique code for bugs, edge cases, and style. You approve "
            "or request changes."
        ),
        "default_model": None,
        "description": "Reviews code for bugs, style, and edge cases.",
    },
    {
        "name": "tester",
        "system_prompt": (
            "You write tests that cover happy path and edge cases using the "
            "project's test framework."
        ),
        "default_model": None,
        "description": "Writes tests covering happy path and edges.",
    },
    {
        "name": "doc-writer",
        "system_prompt": (
            "You write clear user-facing and developer documentation."
        ),
        "default_model": None,
        "description": "Writes user-facing and developer docs.",
    },
    {
        "name": "debugger",
        "system_prompt": (
            "You diagnose bugs from error messages and failing tests, then "
            "propose minimal fixes."
        ),
        "default_model": None,
        "description": "Diagnoses bugs and proposes minimal fixes.",
    },
]
