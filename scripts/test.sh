#!/usr/bin/env bash
set -euo pipefail

# Run test suite using uv with reasonable defaults.
# -q by default; pass VERBOSE=1 for -v.

if [[ "${VERBOSE:-0}" == "1" ]]; then
  echo "> Running: uv run --with pytest --with pytest-asyncio python -m pytest -v"
  uv run --with pytest --with pytest-asyncio python -m pytest -v
else
  echo "> Running: uv run --with pytest --with pytest-asyncio python -m pytest -q"
  uv run --with pytest --with pytest-asyncio python -m pytest -q
fi
