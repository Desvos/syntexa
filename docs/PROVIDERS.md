# LLM providers

Each `LLMProvider` row is a bundle: `(name, provider_type, base_url,
api_key, default_model)`. API keys are encrypted at rest with Fernet;
responses return a masked preview only (e.g. `sk-ant-…7890`).

Supported `provider_type` values:

- `anthropic`
- `openai`
- `openrouter`
- `ollama`
- `openai_compatible`

## Anthropic

Native Claude API.

```json
POST /api/v1/llm-providers
{
  "name": "claude-sonnet",
  "provider_type": "anthropic",
  "api_key": "sk-ant-xxx",
  "default_model": "claude-sonnet-4-6"
}
```

`base_url` is not needed — the adapter uses Anthropic's default. Known
models: `claude-opus-*`, `claude-sonnet-*`, `claude-haiku-*`.

## OpenAI

Native GPT API.

```json
POST /api/v1/llm-providers
{
  "name": "gpt-4",
  "provider_type": "openai",
  "api_key": "sk-xxx",
  "default_model": "gpt-4o"
}
```

Known models: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `o1-preview`, etc.

## OpenRouter

Multi-model gateway (OpenAI-format).

```json
POST /api/v1/llm-providers
{
  "name": "openrouter",
  "provider_type": "openrouter",
  "base_url": "https://openrouter.ai/api/v1",
  "api_key": "sk-or-xxx",
  "default_model": "anthropic/claude-sonnet-4"
}
```

Prefix `default_model` with the vendor slug OpenRouter expects (e.g.
`meta-llama/llama-3.3-70b-instruct`).

## Ollama

Local runtime. No API key required.

```json
POST /api/v1/llm-providers
{
  "name": "ollama",
  "provider_type": "ollama",
  "base_url": "http://localhost:11434/v1",
  "default_model": "llama3.2"
}
```

Make sure the target model is pulled first:

```bash
ollama pull llama3.2
```

## OpenAI-compatible (catch-all)

Any other endpoint that speaks the OpenAI chat/completions protocol —
LM Studio, vLLM, text-generation-webui, Together, etc.

```json
POST /api/v1/llm-providers
{
  "name": "lmstudio",
  "provider_type": "openai_compatible",
  "base_url": "http://localhost:1234/v1",
  "api_key": "lm-studio",
  "default_model": "local-model"
}
```

## Rotating an API key

```json
PUT /api/v1/llm-providers/{id}
{"api_key": "sk-new-xxx"}
```

Omit `api_key` to keep the stored one untouched while changing other
fields.

## Presets

`GET /api/v1/presets/providers` returns ready-to-use templates. Apply
one with:

```json
POST /api/v1/presets/apply
{
  "kind": "provider",
  "preset_name": "claude-sonnet",
  "overrides": {"api_key": "sk-ant-xxx"}
}
```
