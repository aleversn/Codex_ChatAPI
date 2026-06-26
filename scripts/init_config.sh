#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_PATH="${ROOT_DIR}/examples/providers.yaml"
TARGET_DIR="${ROOT_DIR}/config"
TARGET_PATH="${TARGET_DIR}/providers.yaml"
FORCE="${1:-}"

mkdir -p "${TARGET_DIR}"

if [[ ! -f "${SOURCE_PATH}" ]]; then
  echo "Example config not found: ${SOURCE_PATH}" >&2
  exit 1
fi

if [[ -f "${TARGET_PATH}" && "${FORCE}" != "--force" ]]; then
  echo "Config already exists: ${TARGET_PATH}" >&2
  echo "Use 'bash scripts/init_config.sh --force' to overwrite it." >&2
  exit 1
fi

cp "${SOURCE_PATH}" "${TARGET_PATH}"
echo "Initialized config: ${TARGET_PATH}"
