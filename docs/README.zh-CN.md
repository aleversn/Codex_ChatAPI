# Codex_ChatAPI

一个独立的 FastAPI 转发服务，重点是把像 DeepSeek 这类主要提供 `Chat API` 的上游，适配成可供 OpenAI `Responses API` 使用的接口。

它会接收 `Responses API` 风格请求，转发到上游 `chat/completions` 接口，再把响应转换回 `Responses API` 风格，方便本地统一代理 Codex/OpenAI 兼容服务。

[English](../README.md)。

许可证：Apache-2.0。见 [LICENSE](../LICENSE)。

## 功能

- 提供独立接口：`/health`、`/v1/models`、`/v1/responses`
- 从本地 YAML 读取配置，不再依赖原项目数据库里的 `starter.yaml`
- 支持多个服务商 `provider`
- 每个服务商支持多个 `base_urls`，按轮询方式选择上游地址
- 支持在请求体中通过 `provider` 字段临时指定服务商
- 支持通过启动脚本指定默认服务商与端口
- 保留 SSE 流式转发能力

## 目录结构

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

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 快速开始

推荐流程是先用示例文件初始化本地配置，再通过启动脚本启动服务：

```bash
bash scripts/init_config.sh
bash scripts/start.sh deepseek 8000
```

之所以推荐这种方式，是因为它会把 `examples/` 下的模板复制为本地 `config/providers.yaml`，同时在启动时显式指定默认 provider，更适合作为日常使用方式。

## 初始化配置

首次使用时，先把 `examples` 里的示例配置复制到 `config`：

```bash
bash scripts/init_config.sh
```

如果要覆盖已存在的本地配置：

```bash
bash scripts/init_config.sh --force
```

然后再编辑 `config/providers.yaml`。

## 配置

示例：

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

字段说明：

- `default_provider`：默认服务商
- `providers.<name>.api_key`：该服务商默认密钥
- `providers.<name>.model`：该服务商默认模型
- `providers.<name>.timeout`：请求超时秒数
- `providers.<name>.base_urls`：上游地址列表，可配置多个

注意：

- `base_urls` 配置的是上游服务商 API 根地址，对应的是 `/v1`
- 不要把它写成 `/v1/responses`，因为 `/v1/responses` 是当前这个代理服务自己暴露的接口
- 例如可填写 `https://api.deepseek.com` 或 `https://openrouter.ai/api`，程序会自动规范到上游 `/v1` 路径

## 启动

### 方式 1：使用启动脚本（推荐）

```bash
bash scripts/start.sh deepseek 8000
```

参数说明：

- 第一个参数：默认服务商，例如 `deepseek`
- 第二个参数：监听端口，例如 `8000`

也支持环境变量：

```bash
CODEX_PROVIDER=openrouter PORT=8010 bash scripts/start.sh
```

### 方式 2：直接用 uvicorn

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果你想切换配置文件：

```bash
CODEX_CONFIG_PATH=/path/to/providers.yaml uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 在 Codex 中使用

当本项目启动后，如果你希望让 Codex 通过这个代理访问模型，可以在 Codex 的 `config.toml` 中这样配置。

以 `deepseek-v4-flash` 为例：

```toml
model = "deepseek-v4-flash"
model_provider = "dashscope_http"

[model_providers.dashscope_http]
name = "DashScope HTTP"
base_url = "http://<host>:<端口>/v1"
env_key = "DASHSCOPE_API_KEY"
wire_api = "responses"
supports_websockets = false
```

说明：

- `base_url` 需要指向本项目暴露出的服务地址，例如 `http://127.0.0.1:8000/v1`
- `wire_api = "responses"` 表示让 Codex 按 `Responses API` 方式请求当前代理

### 自定义 `CODEX_HOME`

默认情况下，Codex 的 `CODEX_HOME` 一般位于用户主目录 `~` 下。

如果你想自定义 `CODEX_HOME`，可以先设置环境变量，再启动 Codex：

```bash
export CODEX_HOME=<自定义目录>/.codex_home
```

然后再启动 Codex 即可。

## 接口

### 健康检查

```bash
curl http://127.0.0.1:8000/health
```

### 查看上游模型

默认服务商：

```bash
curl http://127.0.0.1:8000/v1/models
```

指定服务商：

```bash
curl "http://127.0.0.1:8000/v1/models?provider=deepseek"
```

### 转发 Responses API 请求

```bash
curl http://127.0.0.1:8000/v1/responses \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "input": "你好，介绍一下你自己",
    "stream": false
  }'
```

如果是流式返回，把 `"stream"` 设为 `true`。代理会请求上游的 Chat Completions 流式接口，再重新包装成 `Responses API` 风格的 SSE 事件输出，例如 `response.created`、`response.output_text.delta`、`response.output_text.done`、`response.completed`。

```bash
curl -N http://127.0.0.1:8000/v1/responses \
  -H 'Content-Type: application/json' \
  -d '{
    "provider": "deepseek",
    "model": "deepseek-chat",
    "input": "写一个简短的 Python hello world 示例",
    "stream": true
  }'
```

在流式模式下：

- 返回类型是 `text/event-stream`
- 文本内容会通过 `Responses API` 风格的 SSE 事件逐步输出
- 流结束时会先返回 `response.completed`，最后再输出 `data: [DONE]`

请求体新增字段：

- `provider`：指定当前请求使用哪个服务商

优先级：

1. 请求体 `provider`
2. 启动脚本传入的 `CODEX_PROVIDER`
3. YAML 中的 `default_provider`

## 备注

- 上游接口需兼容 OpenAI 风格的 `/v1/chat/completions` 和 `/v1/models`
- 如果某个服务商配置了多个 `base_urls`，服务会按请求轮询使用
- 客户端请求本项目时使用的是 `/v1/responses`，而配置里的上游 `base_urls` 应该指向服务商的 `/v1` API 根路径
