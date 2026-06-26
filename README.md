# Codex_ChatAPI

Standalone FastAPI proxy service that accepts `Responses API` style requests, forwards them to an upstream `chat/completions` API, and converts the result back into `Responses API` style responses.

Chinese documentation: [docs/README.zh-CN.md](/home/lpc/repos/Codex_ChatAPI/docs/README.zh-CN.md)

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
cd /home/lpc/repos/Codex_ChatAPI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Initialize Config

On first setup, copy the example config into `config/`:

```bash
cd /home/lpc/repos/Codex_ChatAPI
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

## Start

### Preferred: start script

```bash
cd /home/lpc/repos/Codex_ChatAPI
bash scripts/start.sh deepseek 8000
```

Arguments:

- First argument: default provider, for example `deepseek`
- Second argument: listening port, for example `8000`

Environment variables also work:

```bash
CODEX_PROVIDER=openrouter PORT=8010 bash scripts/start.sh
```

### Alternative: uvicorn directly

```bash
cd /home/lpc/repos/Codex_ChatAPI
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

Request priority:

1. Request body `provider`
2. `CODEX_PROVIDER` from the start command
3. `default_provider` in YAML

## Notes

- The upstream service must support OpenAI-style `/v1/chat/completions` and `/v1/models`
- If a provider defines multiple `base_urls`, the service rotates them per request
