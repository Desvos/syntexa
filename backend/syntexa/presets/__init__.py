"""Built-in presets for onboarding.

Exposes ready-to-use agents, LLM provider templates, and swarm blueprints
so vibe coders can go from zero to first swarm without hand-crafting a
dozen rows. The DB seed happens via ``apply_preset``.
"""
from __future__ import annotations

from syntexa.presets.agents import BUILTIN_AGENT_PRESETS
from syntexa.presets.apply import PresetError, UnknownPresetError, apply_preset
from syntexa.presets.providers import BUILTIN_PROVIDER_PRESETS
from syntexa.presets.swarm_templates import BUILTIN_SWARM_TEMPLATES

__all__ = [
    "BUILTIN_AGENT_PRESETS",
    "BUILTIN_PROVIDER_PRESETS",
    "BUILTIN_SWARM_TEMPLATES",
    "PresetError",
    "UnknownPresetError",
    "apply_preset",
]
