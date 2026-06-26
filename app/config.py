from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "providers.yaml"


class ConfigError(RuntimeError):
    """Raised when the local YAML configuration is missing or invalid."""


@dataclass(slots=True)
class ProviderConfig:
    name: str
    base_urls: list[str]
    api_key: str = ""
    model: str | None = None
    timeout: float = 300.0


@dataclass(slots=True)
class AppConfig:
    default_provider: str
    providers: dict[str, ProviderConfig]

    def get_provider(self, provider_name: str | None = None) -> ProviderConfig:
        resolved_name = (provider_name or self.default_provider or "").strip()
        if not resolved_name:
            raise ConfigError("No provider specified and default_provider is empty")
        provider = self.providers.get(resolved_name)
        if provider is None:
            raise ConfigError(f"Provider '{resolved_name}' is not defined in YAML config")
        return provider


def _normalize_base_urls(raw_value: Any) -> list[str]:
    if isinstance(raw_value, str):
        values = [raw_value]
    elif isinstance(raw_value, list):
        values = [item for item in raw_value if isinstance(item, str)]
    else:
        values = []
    normalized = [value.strip().rstrip('/') for value in values if value and value.strip()]
    if not normalized:
        raise ConfigError("Each provider must define at least one non-empty base_urls entry")
    return normalized


def get_config_path() -> Path:
    configured = os.getenv("CODEX_CONFIG_PATH", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_CONFIG_PATH


def load_app_config(config_path: Path | None = None) -> AppConfig:
    path = config_path or get_config_path()
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file) or {}

    if not isinstance(raw_config, dict):
        raise ConfigError("YAML root must be a mapping")

    raw_default_provider = str(raw_config.get("default_provider") or "").strip()
    raw_providers = raw_config.get("providers")
    if not isinstance(raw_providers, dict) or not raw_providers:
        raise ConfigError("providers must be a non-empty mapping")

    providers: dict[str, ProviderConfig] = {}
    for provider_name, provider_value in raw_providers.items():
        if not isinstance(provider_value, dict):
            raise ConfigError(f"Provider '{provider_name}' must be a mapping")
        providers[str(provider_name)] = ProviderConfig(
            name=str(provider_name),
            base_urls=_normalize_base_urls(provider_value.get("base_urls") or provider_value.get("urls")),
            api_key=str(provider_value.get("api_key") or ""),
            model=str(provider_value.get("model") or "").strip() or None,
            timeout=float(provider_value.get("timeout") or 300.0),
        )

    default_provider = os.getenv("CODEX_PROVIDER", "").strip() or raw_default_provider or next(iter(providers))
    if default_provider not in providers:
        raise ConfigError(f"default_provider '{default_provider}' is not present in providers")

    return AppConfig(default_provider=default_provider, providers=providers)
