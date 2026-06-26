# Codex_ChatAPI

一个独立的 FastAPI 转发服务，用来把 `Responses API` 风格请求转发到上游 `chat/completions` 接口，并把响应再转换回 `Responses API` 风格，方便本地统一代理 Codex/OpenAI 兼容服务。

默认英文文档见根目录 [README.md](/home/lpc/repos/Codex_ChatAPI/README.md)。

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
cd /home/lpc/repos/Codex_ChatAPI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 初始化配置

首次使用时，先把 `examples` 里的示例配置复制到 `config`：

```bash
cd /home/lpc/repos/Codex_ChatAPI
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

## 启动

### 方式 2：使用启动脚本（推荐）

```bash
cd /home/lpc/repos/Codex_ChatAPI
bash scripts/start.sh deepseek 8000
```

参数说明：

- 第一个参数：默认服务商，例如 `deepseek`
- 第二个参数：监听端口，例如 `8000`

也支持环境变量：

```bash
CODEX_PROVIDER=openrouter PORT=8010 bash scripts/start.sh
```

### 方式 1：直接用 uvicorn

```bash
cd /home/lpc/repos/Codex_ChatAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

如果你想切换配置文件：

```bash
CODEX_CONFIG_PATH=/path/to/providers.yaml uvicorn app.main:app --host 0.0.0.0 --port 8000
```

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

请求体新增字段：

- `provider`：指定当前请求使用哪个服务商

优先级：

1. 请求体 `provider`
2. 启动脚本传入的 `CODEX_PROVIDER`
3. YAML 中的 `default_provider`

## 备注

- 上游接口需兼容 OpenAI 风格的 `/v1/chat/completions` 和 `/v1/models`
- 如果某个服务商配置了多个 `base_urls`，服务会按请求轮询使用
