# Quickstart — zero to first swarm in 5 minutes

This guide assumes the backend (`syntexa-api`) and frontend (`bun run
dev`) are already running locally. See the root `README.md` for local
dev setup.

1. **Sign up.** Open `http://localhost:5173`, click **Sign up**, pick a
   username and password (min 8 chars). You'll be redirected to the
   wizard.

2. **Add an LLM provider.** Go to **Advanced → LLM Providers →
   Add provider**. Pick a type (Anthropic, OpenAI, OpenRouter, or
   Ollama) and paste your API key. See [PROVIDERS](./PROVIDERS.md) for
   specifics. Local Ollama needs no key.

3. **Add a repository.** In the wizard Step 1, click **Add new
   repository**. Give it a slug and the absolute path to a local git
   checkout. The platform creates worktrees under this path when running
   swarms.

4. **Describe the task.** In Step 2, click one of the template chips
   ("Quick Fix", "Feature Dev", "Review Only", or "Auto") to pre-select
   the agent roster and orchestrator strategy. Then type your task in
   plain English ("Fix the NPE in login handler").

5. **Seed preset agents.** In Step 3, if you don't have any agents yet,
   click **Seed preset agents** — this creates the six built-in agents
   (planner, coder, reviewer, tester, doc-writer, debugger) bound to
   your first LLM provider.

6. **Run the swarm.** Click **Create & Run Swarm**. The orchestrator
   picks a strategy (or uses the template's override), runs the agents,
   and shows each agent's output in a card below.

That's it. For triggering swarms automatically from ClickUp or
Telegram, see [LISTENERS](./LISTENERS.md).
