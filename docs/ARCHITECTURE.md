# Architecture

This document maps Syntexa's code top-to-bottom: what each layer is
responsible for, how a request flows through the system, and where to
look when you need to change something. It complements
[CONCEPTS.md](./CONCEPTS.md) (the data model in plain English) and
[CODE_MAP.md](./CODE_MAP.md) (a file-by-file index).

## 1. What the project does

Syntexa turns a plain-English task + a git repository into a run of one
or more AI agents that collaborate to produce a result. A user picks a
repo, describes a task, selects an agent roster, and starts a **swarm**.
An **orchestrator** decides whether those agents run sequentially or in
parallel and dispatches them. Each agent calls out to a configurable
LLM provider (Claude, GPT, OpenRouter, Ollama, or any OpenAI-compatible
endpoint). Results come back as a per-agent output map.

Two trigger paths exist:

- **Interactive** — React wizard → `POST /swarms` → `POST /swarms/{id}/run`.
- **Event-driven** — A background daemon polls ClickUp (tasks tagged
  with a trigger) and listens to Telegram (messages that mention a repo
  slug). Each new event spawns a swarm automatically, with dedupe via
  the `processed_events` table.

## 2. Top-level topology

```
┌──────────────────────────────────────────────────────────────────┐
│                         React frontend                            │
│  Wizard • Swarms • Agents • Providers • Repos • Settings         │
└────────────────────────┬─────────────────────────────────────────┘
                         │   HTTP /api/v1 (bearer token)
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI app (syntexa.api)                      │
│  auth · settings · llm_providers · agents · repositories ·       │
│  swarms · credentials · listeners · presets · users              │
└──────┬─────────────────────┬──────────────────────────┬─────────┘
       │                     │                          │
       ▼                     ▼                          ▼
  Orchestrator        LLM adapters              Listener registry
  (strategy picker,   (build_llm_config          (ClickUp, Telegram
   parallel/serial    per provider_type)          poll loops)
   agent dispatch)           │                          │
       │                     │                          │
       └──────────┬──────────┘                          │
                  ▼                                     ▼
          SQLAlchemy models        ←→         processed_events
          (SQLite by default)                 (dedupe table)
```

The daemon (`syntexa-daemon`) is a separate process that runs the
listener registry outside the HTTP request lifecycle. The API can also
start/stop listeners in-process via `/listeners/*` for single-node
deployments.

## 3. Backend layout

All backend code lives in `backend/syntexa/`. Each package has a
focused responsibility:

| Package | Purpose |
|---|---|
| `api/` | FastAPI app, routers, Pydantic schemas, auth middleware |
| `models/` | SQLAlchemy ORM + engine/session helpers |
| `config/` | Pydantic settings loaded from `SYNTEXA_*` env vars |
| `core/` | Cross-cutting utilities — Fernet encryption for API keys |
| `orchestrator/` | Strategy selection + agent dispatch (parallel/sequential) |
| `llm/` | Provider-type → LLM adapter config (AG2/Autogen-compatible) |
| `listeners/` | Background polling (ClickUp, Telegram) + dedupe |
| `adapters/` | PM (ClickUp) and repo (GitHub) integration ports |
| `daemon/` | Standalone entry for the listener/executor process |
| `presets/` | Built-in agent, provider, and swarm-template catalogs |
| `migrations/` | Alembic schema versions |
| `tests/` | pytest suite (unit + integration) |

## 4. Data model

Nine SQLAlchemy models, all in `backend/syntexa/models/entities.py`.

| Model | Table | Notable columns | Relationships |
|---|---|---|---|
| `User` | `users` | `username` (unique), `password_hash` (bcrypt) | — |
| `SystemSetting` | `system_settings` | `key` (PK), JSON `value` | — |
| `LLMProvider` | `llm_providers` | `provider_type`, `base_url`, `api_key_encrypted` (Fernet), `default_model` | 1:N → Agent |
| `Agent` | `agents` | `system_prompt`, `model` (optional override), `is_active` | FK → LLMProvider; N:M → Swarm via SwarmAgent |
| `Repository` | `repositories` | `path` (unique, absolute), `default_branch`, `clickup_list_id`, `clickup_trigger_tag` | 1:N → Swarm |
| `Swarm` | `swarms` | `orchestrator_strategy` (auto/sequential/parallel), `manual_agent_order` (JSON), `status` (idle/running/completed/failed), `max_rounds` | FK → Repository; N:M → Agent |
| `SwarmAgent` | `swarm_agents` | composite PK `(swarm_id, agent_id)`, `position` | FK → Swarm (CASCADE), Agent (RESTRICT) |
| `ExternalCredential` | `external_credentials` | `service_type` (clickup/github/…), JSON `_credentials`, `is_active` | — |
| `ProcessedEvent` | `processed_events` | composite PK `(source, external_id)`, nullable `swarm_id` | FK → Swarm (SET NULL) |

Key design choices:

- **API keys never leave the DB in plaintext.** `api_key_encrypted` is
  Fernet ciphertext; `build_llm_config()` decrypts only at dispatch
  time; API responses return a masked preview (`sk-ant-…7890`).
- **RESTRICT on `Agent.id` inside `SwarmAgent`.** You can't delete an
  agent that is still wired into a swarm — makes orphan-swarm states
  impossible.
- **`processed_events.swarm_id` is nullable.** If swarm creation fails
  mid-flight, the event is still marked processed so the listener
  doesn't replay a poison event in a loop.

## 5. Request flow: interactive swarm run

```
User clicks "Run" in Swarms page
        │
        ▼
  POST /api/v1/swarms/{id}/run   (Bearer token)
        │
        ▼
  require_auth  ──►  get_db_session  ──►  routes/swarms.py::run_swarm
        │                                         │
        │                                         ▼
        │                              orchestrator.run_swarm(swarm_id)
        │                                         │
        │                     ┌───────────────────┼───────────────────┐
        │                     ▼                   ▼                   ▼
        │          _load_swarm_bundle     decide_strategy()   _pick_meta_provider()
        │          (Swarm + Agents +     (auto → LLM call    (for auto only)
        │           Providers bulk-     → {strategy,order})
        │           fetched)
        │                     │
        │                     ├──► _run_parallel  ── asyncio.gather(agents)
        │                     │
        │                     └──► _run_sequential ─ agent[i] sees prior outputs
        │                                         │
        │                            swarm.status = running → completed|failed
        ▼                                         │
  OrchestratorResult  ◄────────────────────────────
  { strategy_used, order, agent_outputs, success, error }
```

Each agent call in the real path (`_default_agent_runner`):

1. Build AG2 `llm_config` from the agent's provider (with optional
   `agent.model` override).
2. Instantiate `ConversableAgent(name, system_message, llm_config)`.
3. Call `generate_reply(...)` wrapped in `asyncio.to_thread()` — AG2's
   sync API is bridged into asyncio so parallel dispatch really is
   concurrent.

The orchestrator accepts injectable `agent_runner` and
`decision_llm_caller` callables — tests stub these out to avoid real
LLM calls.

## 6. Request flow: listener-driven swarm

```
Daemon starts (syntexa-daemon)
        │
        ▼
  listeners.registry.start_all()
        │
        ├──► ClickUpListener._run_loop() ──┐
        │                                   │
        └──► TelegramListener._run_loop() ──┤
                                            │
                         every N seconds    ▼
                         poll_once() → list[InboundEvent]
                                            │
                                     for each event:
                                            │
                                            ▼
                                   process_event(evt)
                                            │
                 ┌──────────────────────────┼──────────────────────────┐
                 ▼                          ▼                          ▼
           ProcessedEvent?            Create Swarm row         asyncio.create_task(
           already exists?            + SwarmAgent joins         run_swarm(swarm_id))
           → skip                     (all is_active agents)   (fire-and-forget)
                                            │
                                            ▼
                                    Insert ProcessedEvent
```

Robustness details worth remembering:

- **Poison events don't kill the loop.** `process_event()` swallows and
  logs its own exceptions; only `poll_once()` failures trigger
  exponential backoff.
- **The dedupe row is written even on failure.** Spawning a swarm that
  crashes still produces a `ProcessedEvent(source, external_id,
  swarm_id=NULL)` so the next poll doesn't replay the same task.
- **Listeners are not auto-started by the API.** The FastAPI lifespan
  only initializes the DB engine. Listeners start when the daemon
  process runs, or when a user clicks Start on the listeners page
  (`POST /listeners/{source}/start`).

## 7. LLM adapter layer

One file does the work: `backend/syntexa/llm/provider_config.py`.

`build_llm_config(provider, *, model=None)` returns an AG2 `config_list`
dict. The branching is small:

| `provider_type` | `api_type` sent to AG2 | `base_url` default |
|---|---|---|
| `anthropic` | `anthropic` | Anthropic default |
| `openai` | `openai` | OpenAI default |
| `openrouter` | `openai` | `https://openrouter.ai/api/v1` |
| `ollama` | `openai` | `http://localhost:11434/v1` |
| `openai_compatible` | `openai` | must be supplied by the caller |

Adding a provider type is a three-step change:

1. Add the literal to the Pydantic schema for `LLMProvider.provider_type`.
2. Add a branch in `build_llm_config()`.
3. Add a UI option in `frontend/src/pages/LLMProviders.jsx`.

API keys are decrypted at this boundary and never logged. Ollama gets a
placeholder key if none is set, since local Ollama doesn't
authenticate.

## 8. Orchestration strategy picker

`backend/syntexa/orchestrator/decision.py::decide_strategy()` handles
the three modes:

- **`parallel`** — short-circuits, returns no order.
- **`sequential`** — resolves `swarm.manual_agent_order` if set,
  otherwise orders agents by `SwarmAgent.position`.
- **`auto`** — calls a **meta-agent LLM** with the task + agent roster
  and parses a JSON reply `{"strategy":"...","order":[...],"reasoning":"..."}`.
  Malformed replies fall back to sequential-by-position. The meta-agent
  uses whichever provider the caller passed (`meta_provider_id`) or,
  failing that, the first active agent's provider.

## 9. Security

- **Authentication.** `POST /auth/login` issues a URL-safe 32-byte
  token stored in `sessions.db` (separate SQLite file). All routes
  except `/health` and `/auth/*` depend on `require_auth`, which pulls
  the bearer token and looks up the session. Sessions expire after 24h.
- **Passwords.** bcrypt via `passlib`, 12 rounds.
- **API keys at rest.** Fernet with a key sourced in this order:
  1. `SYNTEXA_ENCRYPTION_KEY` env var.
  2. `~/.syntexa/encryption.key` file (0600 permissions).
  3. Autogenerated + written to that file on first run.
- **External credentials.** `external_credentials._credentials` is a
  JSON blob stored through the same encryption helper; `GET
  /credentials` returns masked previews only.

Things that are *not* protected yet: role-based access control (every
authenticated user can do everything), CSRF tokens (bearer tokens
instead), and rate limiting.

## 10. Frontend layout

All frontend code lives in `frontend/src/`.

| Folder | Purpose |
|---|---|
| `api/` | `client.js` (fetch wrapper, ApiError, `api.*` namespaces) and `auth.js` (token + session-expiry helpers) |
| `components/` | Shell (AppLayout), auth guard (ProtectedRoute), theming, reusable UI |
| `pages/` | One component per route |
| `styles/base.css` | Global resets + prefers-reduced-motion |
| `theme.js` | MUI theme (light + dark, brand colors, component overrides) |
| `main.jsx` | Entry — BrowserRouter + top-level App with 8 routes |

### Routes

| Path | Page | Purpose |
|---|---|---|
| `/login` | `Login.jsx` | Full-screen login; public. |
| `/` | `Wizard.jsx` | 3-step swarm-creation flow. The main UX. |
| `/swarms` | `Swarms.jsx` | List, run, delete swarms; inline run results. |
| `/agents` | `Agents.jsx` | Agent CRUD. |
| `/llm-providers` | `LLMProviders.jsx` | Provider CRUD; keys are masked. |
| `/repositories` | `Repositories.jsx` | Repo CRUD + per-row health check. |
| `/users` | `Users.jsx` | User admin. |
| `/settings` | `Settings.jsx` | Runtime-tunable daemon settings + connection status. |

### State & data flow

- **No Redux/Zustand.** Pages own their state with `useState`. Auth
  lives in localStorage (`syntexa_auth_token`), read by `api/auth.js`
  and checked by `ProtectedRoute`.
- **`api` client.** Every page imports `{ api }` from `api/client.js`
  and calls namespaced methods (`api.swarms.run(id)`). A 401 response
  clears the token and redirects to `/login` via a shared error
  handler.
- **Theming.** `ThemeContextProvider` wraps the app, provides
  `{ mode, toggleMode }`, and persists the choice. All components read
  colors from the MUI theme — no hex literals in components.
- **Dev proxy.** `vite.config.js` forwards `/api/*` and `/health/*` to
  `http://127.0.0.1:8000`, so the frontend runs on `:5173` without
  CORS configuration.

## 11. Configuration surface

Two layers of configuration:

1. **Environment variables** (loaded by `backend/syntexa/config/settings.py`,
   prefix `SYNTEXA_`). These are fixed at process start.
2. **System settings** (`system_settings` table, mutated via `PATCH
   /settings`). Runtime-tunable: `poll_interval`, `max_concurrent`,
   `log_retention_days`, `agent_trigger_tag`, `base_branch`.

The most load-bearing env vars:

| Var | Default | What it controls |
|---|---|---|
| `SYNTEXA_DATABASE_URL` | `sqlite:///./syntexa.db` | SQLAlchemy DSN. |
| `SYNTEXA_API_HOST` / `SYNTEXA_API_PORT` | `127.0.0.1:8000` | uvicorn bind. |
| `SYNTEXA_ENCRYPTION_KEY` | autogen | Fernet key for API-key encryption. |
| `SYNTEXA_SESSION_SECRET` | `change-me` | Must be overridden in prod. |
| `SYNTEXA_CLICKUP_API_KEY` | — | Listener fallback if no DB credential. |
| `SYNTEXA_TELEGRAM_BOT_TOKEN` | — | Listener fallback if no DB credential. |
| `SYNTEXA_POLL_INTERVAL` | `300` | Seconds between ClickUp polls. |
| `SYNTEXA_MAX_CONCURRENT` | `3` | Swarm concurrency cap in the daemon. |

## 12. Running the system

### Local development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/Scripts/activate   # Windows
pip install -e .
alembic upgrade head
syntexa-api                     # HTTP on :8000

# Frontend (always bun, never npm)
cd frontend
bun install
bun run dev                     # :5173 with /api proxied to backend

# Background daemon (optional; listeners can also run inside the API)
syntexa-daemon
```

Tests:

```bash
# Backend
cd backend && PYTHONPATH=$(pwd) python -m pytest syntexa/tests/ -q

# Frontend
cd frontend && bunx vitest run
```

### Production

Only one deployment target ships today: a systemd unit at
`deploy/syntexa.service`. It runs `syntexa-daemon` as the `syntexa`
user from `/opt/syntexa`, with hardening flags (`NoNewPrivileges`,
`PrivateTmp`, `ProtectSystem=strict`) and an env file at
`/etc/syntexa/syntexa.env`. The API is expected to run alongside it —
either as a second systemd unit or behind a reverse proxy — that setup
is not templated yet.

## 13. Extension points

| To add… | Touch |
|---|---|
| A new LLM provider type | `llm/provider_config.py` + `api/schemas.py` literals + `frontend/src/pages/LLMProviders.jsx` |
| A new listener source | New module under `listeners/`, register in `listeners/registry.py`, extend `routes/listeners.py` |
| A new orchestration strategy | Branch in `orchestrator/decision.py::decide_strategy` + dispatcher in `orchestrator/executor.py` |
| A new adapter (e.g. Jira) | Subclass `adapters/base.py::ProjectManagementAdapter`, wire it in `daemon/main.py` credential resolution |
| A new preset | Append to `presets/agents.py` / `providers.py` / `swarm_templates.py`; `POST /presets/apply` picks it up |
| A new schema column | New Alembic revision in `backend/syntexa/migrations/versions/`, plus the model + Pydantic schema |

## 14. Known limitations

- **No RBAC.** Any authenticated user can mutate any resource.
- **Sync `/swarms/{id}/run`.** The HTTP request blocks until all agents
  finish. For long swarms this will time out at the reverse-proxy layer.
  A job-queue path is planned but not built.
- **Single-node.** Listeners assume one daemon instance. Running two
  daemons against the same DB is safe for dedupe but wasteful.
- **Worktree cleanup.** Worktrees under `worktrees/` are gitignored and
  created per swarm; cleanup relies on successful swarm completion.
- **Legacy tables.** The `drop_legacy_agent_roles_compositions_instances`
  migration removed the pre-simple-swarms schema; if you see references
  to `agent_roles` / `swarm_compositions` / `swarm_instances` in old
  code or specs, they're historical.

## 15. Related documents

- [CONCEPTS.md](./CONCEPTS.md) — the data model, in plain English.
- [CODE_MAP.md](./CODE_MAP.md) — file-by-file map with line pointers.
- [API.md](./API.md) — endpoint list.
- [PROVIDERS.md](./PROVIDERS.md) — per-provider setup.
- [LISTENERS.md](./LISTENERS.md) — ClickUp/Telegram setup.
- [QUICKSTART.md](./QUICKSTART.md) — five-minute onboarding.
