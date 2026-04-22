# Core concepts

Syntexa's data model is deliberately small: three nouns and one verb.

## Repository

A `Repository` is a git checkout on disk. Each row has a name (slug), an
absolute path, a default branch, and optional ClickUp wiring
(`clickup_list_id`, `clickup_trigger_tag`). Multiple repositories can be
registered — swarms that run concurrently against different repos don't
interfere because each swarm uses its own worktree under the repo path.

## Agent

An `Agent` is a reusable persona: a `name`, a `system_prompt`, and a
pointer to an `LLMProvider`. You can optionally override the provider's
default model per-agent. The built-in preset library (see `/presets`)
ships six ready-made agents: planner, coder, reviewer, tester,
doc-writer, debugger.

## LLMProvider

An `LLMProvider` is an `(endpoint, credential)` pair. Supported types:

- `anthropic` — native Claude API
- `openai` — native GPT API
- `openrouter` — multi-model gateway
- `ollama` — local runtime (no key required)
- `openai_compatible` — any other OpenAI-format endpoint

API keys are encrypted at rest (Fernet) and never echoed back — the API
returns a masked preview only.

## Swarm

A `Swarm` is the unit of work: a repository + a task description + a set
of agents + an orchestrator strategy. Strategies:

- `auto` — the meta-orchestrator agent picks the best strategy.
- `sequential` — agents run in fixed order (see `manual_agent_order`).
- `parallel` — agents run simultaneously.

When you run a swarm, status transitions `idle → running →
completed|failed`. Swarms are N:M with agents through a join table —
one agent can sit in many swarms; one swarm holds many agents.

## Orchestrator

The orchestrator is a meta-agent that decides how a swarm's agents
should collaborate. For `strategy=auto` it reads the task and agent
roster and picks sequential vs parallel at run time. For explicit
`sequential` / `parallel` it just executes accordingly.

## Listeners

H24 listeners run in a background daemon and react to external events:

- **ClickUp listener** polls a list for tasks tagged with the configured
  trigger and auto-spawns a swarm per task.
- **Telegram listener** accepts messages that mention a tagged repo and
  spawns a swarm for the message body.

Listeners dedupe via the `processed_events` table — the same event is
never double-processed.

## Presets (Phase 9)

Built-in catalogs accelerate onboarding:

- Agent presets (6 roles) — usable with any provider.
- Provider presets (4 templates) — user still supplies the API key.
- Swarm templates (4 blueprints) — name an agent roster + a strategy.

The `/presets/apply` endpoint seeds a preset into the DB and returns
the created entity.
