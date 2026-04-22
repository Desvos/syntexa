# Syntexa

Syntexa is an agent-swarm platform for vibe coders. Describe what you
want in plain English, point it at a git repo, and a team of AI agents
(planner, coder, reviewer, tester, and more) collaborates on the work.
Multiple swarms can run concurrently against different repositories,
each in its own worktree, each picking its own orchestration strategy.

## Key capabilities

- **Bring your own LLM.** Anthropic, OpenAI, OpenRouter, Ollama (local),
  or any OpenAI-compatible endpoint. API keys are encrypted at rest.
- **Built-in agent presets.** Six ready-to-use agents (planner, coder,
  reviewer, tester, doc-writer, debugger) plus four swarm templates
  (quick-fix, feature-dev, review-only, auto). Seed them with a click.
- **Progressive 3-step wizard.** Pick a repo → describe the task →
  pick agents. Advanced controls are collapsed by default.
- **H24 listeners.** Auto-spawn swarms from ClickUp tasks or Telegram
  messages. Each event is deduped so nothing gets double-processed.
- **Multi-repo, multi-swarm.** Run many swarms in parallel on the same
  or different codebases; each gets its own worktree.

## Quickstart

See [docs/QUICKSTART.md](./docs/QUICKSTART.md) — zero to first swarm in
five minutes.

## Documentation

- [Quickstart](./docs/QUICKSTART.md)
- [Core concepts](./docs/CONCEPTS.md)
- [API reference](./docs/API.md)
- [LLM providers](./docs/PROVIDERS.md)
- [Listeners](./docs/LISTENERS.md)

## Local development

### Backend (FastAPI + SQLAlchemy)

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -e .

# Initialize DB schema
alembic upgrade head

# Run the API (http://localhost:8000)
syntexa-api
# or
python -m uvicorn syntexa.api.main:app --reload
```

Run the test suite:

```bash
PYTHONPATH=$(pwd) python -m pytest syntexa/tests/ -q
```

### Frontend (React + Vite + Material-UI)

Always use `bun` — never npm/npx.

```bash
cd frontend
bun install
bun run dev        # dev server on http://localhost:5173
bun run build      # production build in dist/
```

The dev server proxies `/api/v1` to the backend, so start both in
parallel terminals.

## License

See repository root.
