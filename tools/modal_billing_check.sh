#!/usr/bin/env bash
set -euo pipefail

# Compatibility shim for local env files that name the Modal token id MODAL_KEY.
if [[ -n "${MODAL_KEY:-}" && -z "${MODAL_TOKEN_ID:-}" ]]; then
  export MODAL_TOKEN_ID="${MODAL_KEY}"
fi

if ! command -v modal >/dev/null 2>&1; then
  echo "missing modal CLI; install with: python -m pip install modal" >&2
  exit 2
fi

modal token info
modal billing report --for "this month" --json

