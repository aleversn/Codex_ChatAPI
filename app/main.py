from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from .config import ConfigError, load_app_config
from .service import build_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_app_config()
    app.state.app_config = config
    app.state.response_proxy_service = build_service(config)
    yield


app = FastAPI(
    title="Codex Chat API Proxy",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, object]:
    config = app.state.app_config
    return {
        "ok": True,
        "service": "codex-chat-api-proxy",
        "default_provider": config.default_provider,
        "providers": sorted(config.providers.keys()),
    }


@app.get("/v1/models")
async def list_models(provider: str | None = Query(default=None)):
    service = app.state.response_proxy_service
    status_code, content = await service.list_models(provider_name=provider)
    return Response(content=content, status_code=status_code, media_type="application/json")


@app.post("/v1/responses")
async def responses_proxy(request: Request):
    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {exc}") from exc

    if not isinstance(body, dict):
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "request body must be a JSON object", "type": "invalid_request_error"}},
        )

    service = app.state.response_proxy_service
    mode, payload, status_code = await service.forward_responses_request(body)
    if mode == "error":
        try:
            content = json.loads(payload.decode("utf-8"))
        except Exception:
            content = {"error": {"message": payload.decode("utf-8", errors="ignore") or "upstream error"}}
        return JSONResponse(status_code=status_code, content=content)
    if mode == "json":
        return JSONResponse(status_code=status_code, content=payload)
    return StreamingResponse(
        payload,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Codex Chat API Proxy is running"}


@app.exception_handler(ConfigError)
async def config_error_handler(_: Request, exc: ConfigError):
    return JSONResponse(status_code=500, content={"error": {"message": str(exc), "type": "config_error"}})
