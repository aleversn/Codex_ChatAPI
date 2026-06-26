#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROVIDER="${1:-${CODEX_PROVIDER:-}}"
PORT="${2:-${PORT:-8000}}"
HOST="${HOST:-0.0.0.0}"
CONFIG_PATH="${CODEX_CONFIG_PATH:-${ROOT_DIR}/config/providers.yaml}"

if [[ -z "${PROVIDER}" ]]; then
  PROVIDER="$(python3 - <<PY
import yaml
from pathlib import Path
path = Path(r"${CONFIG_PATH}")
with path.open("r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
print((data.get("default_provider") or "").strip())
PY
)"
fi

if [[ -z "${PROVIDER}" ]]; then
  echo "No provider specified and no default_provider found in ${CONFIG_PATH}" >&2
  exit 1
fi

export CODEX_PROVIDER="${PROVIDER}"
export CODEX_CONFIG_PATH="${CONFIG_PATH}"

echo "Starting Codex Chat API Proxy"
echo "  provider: ${CODEX_PROVIDER}"
echo "  port: ${PORT}"
echo "  config: ${CODEX_CONFIG_PATH}"

exec uvicorn app.main:app --host "${HOST}" --port "${PORT}"
