# Listeners

H24 listeners run inside the background daemon and react to external
events. Each inbound event is deduped via the `processed_events` table
before a swarm is created — the same ClickUp task or Telegram message
is never double-processed.

## ClickUp

The ClickUp listener polls a specific list for tasks carrying a trigger
tag and spawns a swarm per task.

### Setup

1. **Create an API token.** In ClickUp → Settings → Apps → API
   Token.

2. **Store the credential.** Either via the `/credentials` API or the
   frontend settings page:

    ```json
    POST /api/v1/credentials
    {
      "service_type": "clickup",
      "credentials": {"api_key": "pk_xxx"},
      "is_active": true
    }
    ```

3. **Wire a repository to a list.** When you create the repo, supply:

    - `clickup_list_id` — the numeric list ID in ClickUp.
    - `clickup_trigger_tag` — the tag the listener reacts to
      (default: `ag2-agent`).

4. **Start the listener.** The daemon auto-starts it, or call
   `POST /api/v1/listeners/clickup/start`.

### How triggering works

Every `poll_interval` seconds (runtime-tunable in `/settings`) the
listener pulls tasks with the configured tag that haven't been
processed. For each new task it:

1. Builds a task description from title + text content.
2. Looks up the repo via `clickup_list_id`.
3. Spawns a swarm (default template: `auto`).
4. Writes a `processed_events` row to prevent replay.

## Telegram

The Telegram listener accepts messages from a configured bot and spawns
a swarm per message that mentions a repo slug.

### Setup

1. **Create a bot** via `@BotFather` and capture the token.

2. **Store the credential:**

    ```json
    POST /api/v1/credentials
    {
      "service_type": "telegram",
      "credentials": {"bot_token": "1234:ABC..."},
      "is_active": true
    }
    ```

    Alternatively set `SYNTEXA_TELEGRAM_BOT_TOKEN` in the environment.

3. **Invite the bot to a chat** and send messages in the form:

    ```
    @syntexa-bot repo:my-repo Fix login timeout
    ```

The listener parses `repo:<slug>` to find the repository, uses the rest
of the message as the task description, and spawns a swarm.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `SYNTEXA_CLICKUP_API_KEY` | Fallback when no DB credential is set. |
| `SYNTEXA_TELEGRAM_BOT_TOKEN` | Fallback when no DB credential is set. |
| `SYNTEXA_POLL_INTERVAL` | Seconds between ClickUp polls (default 60). |

## Stopping a listener

Call `POST /api/v1/listeners/{source}/stop` or set its credential's
`is_active=false`. The daemon picks up the change on its next poll.
