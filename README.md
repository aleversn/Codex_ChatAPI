# Codex_ChatAPI

Standalone FastAPI proxy service that makes Chat Completions style providers such as DeepSeek usable through the OpenAI `Responses API`.

It accepts `Responses API` style requests, forwards them to an upstream `chat/completions` API, and converts the result back into `Responses API` style responses. The main goal of this project is to let services that only expose Chat API semantics behave like a Responses API endpoint for local Codex/OpenAI-compatible workflows.

[中文教程](./docs/README.zh-CN.md)

License: Apache-2.0. See [LICENSE](./LICENSE).

## Features

- Provides `/health`, `/v1/models`, and `/v1/responses`
- Loads local YAML config instead of depending on an external project config store
- Supports multiple upstream providers
- Supports multiple `base_urls` per provider with round-robin selection
- Allows per-request provider override through the `provider` field
- Keeps SSE streaming support

## Project Structure

```text
Codex_ChatAPI/
├── app/
│   ├── config.py
│   ├── main.py
│   └── service.py
├── config/
├── docs/
│   └── README.zh-CN.md
├── examples/
│   └── providers.yaml
├── scripts/
│   ├── init_config.sh
│   └── start.sh
├── requirements.txt
└── README.md
```

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

The recommended way is to initialize the local config from the example file, then start the service with the helper script:

```bash
bash scripts/init_config.sh
bash scripts/start.sh deepseek 8000
```

This is the preferred flow because it keeps `config/providers.yaml` local, uses the example template under `examples/`, and makes provider selection explicit at startup.

## Initialize Config

On first setup, copy the example config into `config/`:

```bash
bash scripts/init_config.sh
```

If you want to overwrite an existing local config:

```bash
bash scripts/init_config.sh --force
```

Then edit `config/providers.yaml`.

## Configuration

Example:

```yaml
default_provider: deepseek

providers:
  deepseek:
    api_key: "sk-xxxx"
    model: "deepseek-chat"
    timeout: 300
    base_urls:
      - "https://api.deepseek.com"

  custom_vendor:
    api_key: "sk-xxxx"
    model: "gpt-4.1"
    timeout: 300
    base_urls:
      - "https://proxy-a.example.com"
      - "https://proxy-b.example.com"
```

Fields:

- `default_provider`: default provider name
- `providers.<name>.api_key`: default API key for that provider
- `providers.<name>.model`: default model for that provider
- `providers.<name>.timeout`: request timeout in seconds
- `providers.<name>.base_urls`: one or more upstream base URLs

Important:

- Configure each upstream `base_url` as the provider's API root ending at `/v1`
- Do not set it to `/v1/responses`, because `/v1/responses` is this proxy service's own endpoint
- Example: use `https://api.deepseek.com` or `https://openrouter.ai/api`, and the proxy will normalize them to the upstream `/v1` path

## Start

### Option 1: start script (recommended)

```bash
bash scripts/start.sh deepseek 8000
```

Arguments:

- First argument: default provider, for example `deepseek`
- Second argument: listening port, for example `8000`

Environment variables also work:

```bash
CODEX_PROVIDER=openrouter PORT=8010 bash scripts/start.sh
```

### Option 2: uvicorn directly

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

To use another config file:

```bash
CODEX_CONFIG_PATH=/path/to/providers.yaml uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API

### Health check

```bash
curl http://127.0.0.1:8000/health
```

### List upstream models

Default provider:

```bash
curl http://127.0.0.1:8000/v1/models
```

Specific provider:

```bash
curl "http://127.0.0.1:8000/v1/models?provider=deepseek"
```

### Forward a Responses API request

```bash
curl http://127.0.0.1:8000/v1/responses \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "input": "Hello, introduce yourself",
    "stream": false
  }'
```

For streaming responses, set `"stream": true`. The proxy will call the upstream Chat Completions stream and re-emit it as `Responses API` style SSE events such as `response.created`, `response.output_text.delta`, `response.output_text.done`, and `response.completed`.

```bash
curl -N http://127.0.0.1:8000/v1/responses \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "input": "Write a short hello world program in Python",
    "stream": true
  }'
```

In streaming mode:

- The response uses `text/event-stream`
- Text is emitted incrementally through `Responses API` style SSE events
- The stream ends with `response.completed`, followed by `data: [DONE]`

Request priority:

1. Request body `provider`
2. `CODEX_PROVIDER` from the start command
3. `default_provider` in YAML

## Notes

- The upstream service must support OpenAI-style `/v1/chat/completions` and `/v1/models`
- If a provider defines multiple `base_urls`, the service rotates them per request
- Client requests should call this project at `/v1/responses`, while configured upstream `base_urls` should point to the provider API root for `/v1`
